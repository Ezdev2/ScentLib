import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Constantes du format SCNT
# ---------------------------------------------------------------------------

MAGIC           = b"SCNT"
SCNT_VERSION    = 1

# Flags (bitfield uint16)
FLAG_COMPRESSED = 0b0000_0000_0000_0001   # bit 0 : payload zlib compressé
FLAG_AI_DATA    = 0b0000_0000_0000_0010   # bit 1 : données ai_generated
FLAG_DEBUG      = 0b0000_0000_0000_0100   # bit 2 : mode debug (lisibilité)
FLAG_HAS_CHEM   = 0b0000_0000_0000_1000   # bit 3 : chemical_info présent
FLAG_HAS_META   = 0b0000_0000_0001_0000   # bit 4 : metadata présent

# Enums internes
CAPTURE_TYPES = {
    "static": 0,
    "stream": 1,
}
CAPTURE_TYPES_INV = {v: k for k, v in CAPTURE_TYPES.items()}

DATA_ORIGINS = {
    "human_perceptual":  0,
    "sensor_raw":        1,
    "simulated":         2,
    "ai_generated":      3,
    "computed_features": 4,
}
DATA_ORIGINS_INV = {v: k for k, v in DATA_ORIGINS.items()}

# Sentinelle pour valeurs None dans les champs optionnels
NULL_UINT32 = 0xFFFFFFFF    # CID absent
NULL_FLOAT32 = float("nan") # MW absente


# ---------------------------------------------------------------------------
# Helpers bas niveau
# ---------------------------------------------------------------------------

def _pack_str(s: Optional[str]) -> bytes:
    """
    Sérialise une chaîne : uint8 longueur + bytes UTF-8.
    Chaîne vide ou None → longueur 0.
    Tronque silencieusement à 255 caractères (limite uint8).

    Input  : str ou None
    Output : bytes (1 + len(s))
    """
    if s is None:
        return b"\x00"
    enc = s.encode("utf-8")
    if len(enc) > 255:
        enc = enc[:255]
    return struct.pack("B", len(enc)) + enc


def _unpack_str(data: bytes, offset: int) -> tuple[str, int]:
    """
    Désérialise une chaîne depuis les bytes.
    Input  : buffer bytes, offset de lecture
    Output : (str, nouvel_offset)
    """
    length = data[offset]
    offset += 1
    if length == 0:
        return "", offset
    s = data[offset : offset + length].decode("utf-8")
    return s, offset + length


def _pack_optional_float(value: Optional[float], fmt: str = ">f") -> bytes:
    """
    Sérialise un float optionnel. None → NaN.
    Input  : float ou None, format struct
    Output : bytes (4 bytes pour '>f')
    """
    v = value if value is not None else float("nan")
    return struct.pack(fmt, v)


def _unpack_optional_float(data: bytes, offset: int, fmt: str = ">f") -> tuple[Optional[float], int]:
    """
    Désérialise un float optionnel. NaN → None.
    Input  : buffer, offset, format struct
    Output : (float ou None, nouvel_offset)
    """
    size = struct.calcsize(fmt)
    v = struct.unpack(fmt, data[offset : offset + size])[0]
    result = None if (v != v) else float(round(v, 6))  # NaN check
    return result, offset + size


# ---------------------------------------------------------------------------
# Encodeur principal
# ---------------------------------------------------------------------------

def encode(scent_dict: dict) -> bytes:
    """
    Convertit un dict .scent validé en bytes SCNT.

    Input  : dict Python conforme à scent_schema.json
    Output : bytes du fichier .scnt
    Raises : ValueError si champ obligatoire manquant ou inconnu

    Structure produite :
      HEADER (16) | CAPTURE (4+) | DIM_MAP (var) | DATA (N×2)
      | CHEM_INFO (var) | LABELS (var) | METADATA (var) | CRC32 (4)
    """
    header  = scent_dict.get("header", {})
    chem    = scent_dict.get("chemical_info")
    labels  = scent_dict.get("labels", {})
    data    = scent_dict.get("data", [])
    meta    = scent_dict.get("metadata")
    dim_map = header.get("dimension_map", [])

    # --- Calcul des flags ---
    flags = 0
    if chem is not None:
        flags |= FLAG_HAS_CHEM
    if meta is not None:
        flags |= FLAG_HAS_META
    if header.get("data_origin") == "ai_generated":
        flags |= FLAG_AI_DATA

    # --- Timestamp → uint64 ms ---
    ts_str = header.get("timestamp", "")
    try:
        if ts_str:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            ts_ms = int(dt.timestamp() * 1000)
        else:
            ts_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    except (ValueError, AttributeError):
        ts_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    # --- Lookup enums ---
    cap_type_raw = header.get("capture_type", "static")
    cap_type_int = CAPTURE_TYPES.get(cap_type_raw)
    if cap_type_int is None:
        raise ValueError(f"capture_type inconnu : '{cap_type_raw}'. Valeurs: {list(CAPTURE_TYPES)}")

    d_origin_raw = header.get("data_origin", "human_perceptual")
    d_origin_int = DATA_ORIGINS.get(d_origin_raw)
    if d_origin_int is None:
        raise ValueError(f"data_origin inconnu : '{d_origin_raw}'. Valeurs: {list(DATA_ORIGINS)}")

    n_dims = len(dim_map)

    # ================================================================
    # Assemblage du buffer (ordre fixe du format SCNT v1)
    # ================================================================
    buf = bytearray()

    # --- SECTION 1 : HEADER FIXE (16 bytes) ---
    buf += MAGIC                                    # [0:4]   Magic "SCNT"
    buf += struct.pack(">H", SCNT_VERSION)          # [4:6]   Version uint16
    buf += struct.pack(">H", flags)                 # [6:8]   Flags uint16
    buf += struct.pack(">Q", ts_ms)                 # [8:16]  Timestamp uint64

    # --- SECTION 2 : CAPTURE INFO ---
    buf += struct.pack("B", cap_type_int)           # capture_type uint8
    buf += struct.pack("B", d_origin_int)           # data_origin uint8
    buf += struct.pack(">H", n_dims)                # n_dimensions uint16

    # --- SECTION 3 : DIMENSION MAP ---
    # Format : pour chaque dim → uint8(len) + bytes
    for dim_name in dim_map:
        buf += _pack_str(dim_name)

    # --- SECTION 4 : DATA VECTOR (float16, big-endian) ---
    # float16 : précision ~0.001, suffisant pour Dravnieks [0.0-1.0]
    f16_array = np.array(data, dtype=np.float16)
    buf += f16_array.tobytes()

    # --- SECTION 5 : CHEMICAL INFO (si FLAG_HAS_CHEM) ---
    if flags & FLAG_HAS_CHEM:
        cid = chem.get("pubchem_cid") if chem else None
        cid_int = int(cid) if cid is not None else NULL_UINT32
        buf += struct.pack(">I", cid_int)                           # CID uint32
        buf += _pack_str(chem.get("smiles") if chem else None)      # SMILES
        buf += _pack_str(chem.get("inchi_key") if chem else None)   # InChIKey
        buf += _pack_str(chem.get("iupac_name") if chem else None)  # IUPAC
        buf += _pack_str(chem.get("common_name") if chem else None) # common_name
        mw = chem.get("molecular_weight") if chem else None
        buf += _pack_optional_float(mw, ">f")                       # MW float32

    # --- SECTION 6 : LABELS ---
    buf += _pack_str(labels.get("layer1_category", "unclassified"))
    buf += _pack_str(labels.get("layer2_sub_category"))
    buf += _pack_str(labels.get("layer3_descriptor"))
    buf += _pack_optional_float(labels.get("intensity"), ">f")
    buf += _pack_optional_float(labels.get("confidence"), ">f")

    # --- SECTION 7 : METADATA (si FLAG_HAS_META) ---
    if flags & FLAG_HAS_META and meta:
        # Sérialise uniquement les valeurs stringifiables
        meta_pairs = []
        for k, v in meta.items():
            if isinstance(v, (str, int, float, bool)):
                meta_pairs.append((str(k), str(v)))
        buf += struct.pack("B", min(len(meta_pairs), 255))
        for k, v in meta_pairs[:255]:
            buf += _pack_str(k)
            buf += _pack_str(v)

    # --- SECTION 8 : CRC32 FOOTER (4 bytes) ---
    crc = zlib.crc32(bytes(buf)) & 0xFFFFFFFF
    buf += struct.pack(">I", crc)

    return bytes(buf)


# ---------------------------------------------------------------------------
# Décodeur principal
# ---------------------------------------------------------------------------

def decode(data: bytes) -> dict:
    """
    Convertit des bytes SCNT en dict .scent (compatible scent_schema.json).

    Input  : bytes d'un fichier .scnt
    Output : dict Python reconstruit
    Raises : ValueError si magic invalide ou CRC échoue
             struct.error si fichier tronqué/corrompu
    """
    if len(data) < 20:
        raise ValueError("Fichier SCNT trop court (< 20 bytes). Corrompu ?")

    # --- Vérification CRC32 ---
    crc_stored   = struct.unpack(">I", data[-4:])[0]
    crc_computed = zlib.crc32(data[:-4]) & 0xFFFFFFFF
    if crc_stored != crc_computed:
        raise ValueError(
            f"CRC32 mismatch : stocké={crc_stored:08X}, calculé={crc_computed:08X}. "
            f"Fichier corrompu ou modifié."
        )

    offset = 0

    # --- SECTION 1 : HEADER FIXE ---
    magic = data[0:4]
    if magic != MAGIC:
        raise ValueError(
            f"Magic number invalide : attendu b'SCNT', reçu {magic!r}. "
            f"Ce fichier n'est pas un fichier .scnt ScentLib."
        )
    offset = 4

    version = struct.unpack(">H", data[offset:offset+2])[0]; offset += 2
    flags   = struct.unpack(">H", data[offset:offset+2])[0]; offset += 2
    ts_ms   = struct.unpack(">Q", data[offset:offset+8])[0]; offset += 8

    # Reconstruction du timestamp ISO 8601
    try:
        ts_dt  = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
        ts_str = ts_dt.isoformat()
    except (OSError, OverflowError, ValueError):
        ts_str = datetime.now(timezone.utc).isoformat()

    # --- SECTION 2 : CAPTURE INFO ---
    cap_type_int = data[offset]; offset += 1
    d_origin_int = data[offset]; offset += 1
    n_dims       = struct.unpack(">H", data[offset:offset+2])[0]; offset += 2

    capture_type = CAPTURE_TYPES_INV.get(cap_type_int, "static")
    data_origin  = DATA_ORIGINS_INV.get(d_origin_int, "human_perceptual")

    # --- SECTION 3 : DIMENSION MAP ---
    dim_map = []
    for _ in range(n_dims):
        s, offset = _unpack_str(data, offset)
        dim_map.append(s)

    # --- SECTION 4 : DATA VECTOR ---
    n_bytes  = n_dims * 2
    f16_raw  = data[offset : offset + n_bytes]; offset += n_bytes
    f16_arr  = np.frombuffer(f16_raw, dtype=np.float16)
    # Arrondi à 4 décimales pour masquer les artefacts float16 minimes
    data_vec = [round(float(v), 4) for v in f16_arr]

    # --- SECTION 5 : CHEMICAL INFO ---
    chem_info = None
    if flags & FLAG_HAS_CHEM:
        cid_raw      = struct.unpack(">I", data[offset:offset+4])[0]; offset += 4
        cid          = None if cid_raw == NULL_UINT32 else int(cid_raw)
        smiles,    offset = _unpack_str(data, offset)
        inchi_key, offset = _unpack_str(data, offset)
        iupac_name,offset = _unpack_str(data, offset)
        common_name,offset= _unpack_str(data, offset)
        mw, offset        = _unpack_optional_float(data, offset, ">f")

        chem_info = {
            "pubchem_cid":      cid,
            "smiles":           smiles or None,
            "inchi_key":        inchi_key or None,
            "iupac_name":       iupac_name or None,
            "common_name":      common_name or None,
            "molecular_weight": round(mw, 4) if mw is not None else None,
        }

    # --- SECTION 6 : LABELS ---
    layer1,    offset = _unpack_str(data, offset)
    layer2,    offset = _unpack_str(data, offset)
    layer3,    offset = _unpack_str(data, offset)
    intensity, offset = _unpack_optional_float(data, offset, ">f")
    confidence,offset = _unpack_optional_float(data, offset, ">f")

    labels = {
        "layer1_category":    layer1 or "unclassified",
        "layer2_sub_category": layer2 or None,
        "layer3_descriptor":  layer3 or None,
        "intensity":          round(intensity, 4) if intensity is not None else None,
        "confidence":         round(confidence, 4) if confidence is not None else None,
    }
    # Nettoyage des None pour ne pas polluer le dict
    labels = {k: v for k, v in labels.items() if v is not None}

    # --- SECTION 7 : METADATA ---
    metadata = None
    if flags & FLAG_HAS_META and offset < len(data) - 4:
        n_meta = data[offset]; offset += 1
        metadata = {}
        for _ in range(n_meta):
            k, offset = _unpack_str(data, offset)
            v, offset = _unpack_str(data, offset)
            metadata[k] = v

    # --- Reconstruction du dict .scent ---
    result = {
        "schema_version": f"1.{version}.0",
        "header": {
            "capture_type":  capture_type,
            "data_origin":   data_origin,
            "dimension_map": dim_map if dim_map else None,
            "timestamp":     ts_str,
        },
        "labels": labels,
        "data":   data_vec,
    }

    # Ajout des champs optionnels seulement s'ils ont du contenu
    if chem_info is not None:
        result["chemical_info"] = chem_info
    if metadata is not None:
        result["metadata"] = metadata

    return result


# ---------------------------------------------------------------------------
# Utilitaires fichiers
# ---------------------------------------------------------------------------

def encode_file(json_path: str, out_path: str = None) -> str:
    """
    Encode un fichier .scent JSON vers .scnt binaire sur le disque.

    Input  : chemin vers le .scent source
             out_path optionnel (défaut : même nom, extension .scnt)
    Output : chemin du fichier .scnt créé
    Raises : FileNotFoundError, ValueError
    """
    import json

    src = Path(json_path)
    if not src.exists():
        raise FileNotFoundError(f"Fichier source introuvable : {json_path}")

    with open(src, "r", encoding="utf-8") as f:
        scent_dict = json.load(f)

    raw_bytes = encode(scent_dict)

    if out_path is None:
        dst = src.with_suffix(".scnt")
    else:
        dst = Path(out_path)
        dst.parent.mkdir(parents=True, exist_ok=True)

    with open(dst, "wb") as f:
        f.write(raw_bytes)

    return str(dst)


def decode_file(scnt_path: str) -> dict:
    """
    Décode un fichier .scnt binaire vers un dict Python.

    Input  : chemin vers le .scnt
    Output : dict conforme à scent_schema.json
    Raises : FileNotFoundError, ValueError (CRC/magic)
    """
    src = Path(scnt_path)
    if not src.exists():
        raise FileNotFoundError(f"Fichier binaire introuvable : {scnt_path}")

    with open(src, "rb") as f:
        raw = f.read()

    return decode(raw)


def compile_directory(input_dir: str, output_dir: str, verbose: bool = True) -> dict:
    """
    Compile tous les fichiers .scent d'un dossier vers .scnt dans un autre.
    C'est la commande 'scentlib compile --dir ... --out ...'

    Input  : dossier source (.scent JSON), dossier destination (.scnt)
    Output : dict {"success": N, "failed": N, "errors": [...]}
    """
    import json

    src_dir = Path(input_dir)
    dst_dir = Path(output_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    scent_files = list(src_dir.glob("*.scent"))

    if not scent_files:
        if verbose:
            print(f"Aucun fichier .scent trouvé dans {input_dir}")
        return {"success": 0, "failed": 0, "errors": []}

    success, failed, errors = 0, 0, []

    for f in scent_files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                scent_dict = json.load(fp)

            raw_bytes = encode(scent_dict)
            out_path  = dst_dir / f.with_suffix(".scnt").name

            with open(out_path, "wb") as fp:
                fp.write(raw_bytes)

            size_json = f.stat().st_size
            size_scnt = out_path.stat().st_size
            ratio     = size_json / size_scnt if size_scnt > 0 else 0

            if verbose:
                print(f"  ✓ {f.name} → {out_path.name}  "
                      f"({size_json}B → {size_scnt}B, {ratio:.1f}x)")
            success += 1

        except Exception as e:
            errors.append({"file": str(f.name), "error": str(e)})
            if verbose:
                print(f"  ✗ {f.name} : {e}")
            failed += 1

    if verbose:
        print(f"\nCompilation terminée : {success} réussis, {failed} échoués")

    return {"success": success, "failed": failed, "errors": errors}


# ---------------------------------------------------------------------------
# Inspection / Debug
# ---------------------------------------------------------------------------

def inspect(scnt_path: str) -> dict:
    """
    Lit l'en-tête d'un fichier .scnt sans décoder le contenu complet.
    Utile pour vérifier rapidement la validité et les métadonnées.

    Input  : chemin vers le .scnt
    Output : dict avec les infos de l'en-tête + stats
    """
    src = Path(scnt_path)
    with open(src, "rb") as f:
        raw = f.read()

    if len(raw) < 20:
        raise ValueError("Fichier trop court")

    magic   = raw[0:4]
    version = struct.unpack(">H", raw[4:6])[0]
    flags   = struct.unpack(">H", raw[6:8])[0]
    ts_ms   = struct.unpack(">Q", raw[8:16])[0]

    crc_stored   = struct.unpack(">I", raw[-4:])[0]
    crc_computed = zlib.crc32(raw[:-4]) & 0xFFFFFFFF
    crc_valid    = crc_stored == crc_computed

    cap_int = raw[16]
    org_int = raw[17]
    n_dims  = struct.unpack(">H", raw[18:20])[0]

    try:
        ts_dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
        ts_str = ts_dt.isoformat()
    except Exception:
        ts_str = "unknown"

    return {
        "file":         src.name,
        "size_bytes":   len(raw),
        "magic_ok":     magic == MAGIC,
        "scnt_version": version,
        "crc_valid":    crc_valid,
        "timestamp":    ts_str,
        "capture_type": CAPTURE_TYPES_INV.get(cap_int, f"unknown({cap_int})"),
        "data_origin":  DATA_ORIGINS_INV.get(org_int, f"unknown({org_int})"),
        "n_dimensions": n_dims,
        "flags": {
            "compressed": bool(flags & FLAG_COMPRESSED),
            "ai_data":    bool(flags & FLAG_AI_DATA),
            "debug":      bool(flags & FLAG_DEBUG),
            "has_chem":   bool(flags & FLAG_HAS_CHEM),
            "has_meta":   bool(flags & FLAG_HAS_META),
        },
    }


# ---------------------------------------------------------------------------
# Test autonome : python -m scentlib.core.binary
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json, sys
    from pathlib import Path

    print("ScentLib — Test du Codex Binaire SCNT")
    print("=" * 55)

    # Cherche un vrai fichier .scent pour le test
    test_candidates = list(Path("data/processed").glob("*.scent"))

    if test_candidates:
        test_file = test_candidates[0]
        print(f"Fichier test : {test_file.name}")

        with open(test_file, "r") as f:
            original = json.load(f)
    else:
        # Fallback : données synthétiques
        print("Aucun fichier .scent trouvé — utilisation de données synthétiques")
        original = {
            "schema_version": "1.1.0",
            "header": {
                "capture_type": "static",
                "data_origin": "human_perceptual",
                "dimension_map": ["ROSE", "FLORAL", "FRUITY", "SPICY", "WOODY"],
                "timestamp": "2026-05-07T12:00:00+00:00",
                "source_dataset": "pyrfume:dravnieks_1985",
            },
            "chemical_info": {
                "pubchem_cid": 460,
                "smiles": "COC1=CC=CC=C1O",
                "iupac_name": "2-methoxyphenol",
                "common_name": "guaiacol",
                "molecular_weight": 124.14,
            },
            "labels": {
                "layer1_category": "floral",
                "layer3_descriptor": "FRAGRANT",
            },
            "data": [0.276, 1.0, 0.086, 1.0, 1.0],
            "metadata": {
                "source": "Pyrfume / Dravnieks 1985",
                "normalization": "÷5 → [0.0, 1.0]",
            },
        }

    # --- Encode ---
    raw = encode(original)
    print(f"\n[1] Encodage")
    print(f"    JSON original : {len(json.dumps(original).encode())} bytes")
    print(f"    SCNT binaire  : {len(raw)} bytes")
    print(f"    Ratio         : {len(json.dumps(original).encode()) / len(raw):.2f}x plus léger")
    print(f"    Hex (16 B)    : {raw[:16].hex().upper()}")

    # --- Decode ---
    restored = decode(raw)
    print(f"\n[2] Décodage")
    print(f"    capture_type : {restored['header']['capture_type']}")
    print(f"    data_origin  : {restored['header']['data_origin']}")
    print(f"    n_dimensions : {len(restored['data'])}")
    if restored.get("chemical_info"):
        print(f"    CID          : {restored['chemical_info'].get('pubchem_cid')}")
        print(f"    common_name  : {restored['chemical_info'].get('common_name')}")
    print(f"    layer1       : {restored['labels']['layer1_category']}")

    # --- Zero-loss test ---
    print(f"\n[3] Test Zero-Loss (tolérance ε < 0.001)")
    original_data  = original["data"]
    restored_data  = restored["data"]
    max_err        = 0.0
    all_pass       = True

    for i, (orig, rest) in enumerate(zip(original_data, restored_data)):
        err = abs(orig - rest)
        max_err = max(max_err, err)
        if err >= 0.001:
            print(f"    ✗ dim[{i}] : {orig} → {rest} (err={err:.6f})")
            all_pass = False

    print(f"    Erreur maximale : {max_err:.8f}")
    print(f"    Résultat        : {'✓ PASSED' if all_pass else '✗ FAILED'}")

    # --- Inspect ---
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".scnt", delete=False) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name

    info = inspect(tmp_path)
    print(f"\n[4] Inspection")
    for k, v in info.items():
        print(f"    {k:<16} : {v}")

    os.unlink(tmp_path)

    print(f"\n{'=' * 55}")
    print("Codex SCNT opérationnel.")