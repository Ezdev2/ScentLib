"""
pyrfume_to_scent.py — Convertisseur Pyrfume → ScentLib (.scent)
================================================================
Dataset cible : Dravnieks 1985 (via pyrfume-data sur GitHub)

Structure réelle Pyrfume / Dravnieks :
  molecules.csv   → index=CID    | MolecularWeight, IsomericSMILES, IUPACName, name
  stimuli.csv     → index=Stimulus | CID (clé de jointure)
  behavior_1.csv  → index=Stimulus | 146 descripteurs Dravnieks (scores 0–5)
                    FORMAT WIDE : une colonne par descripteur

Chaîne de jointure correcte :
  behavior_1 (Stimulus → scores)
      ↓  join on Stimulus index
  stimuli    (Stimulus → CID)
      ↓  join on CID
  molecules  (CID → SMILES, MW, etc.)

Règles appliquées :
  1. Join Rule    : toujours passer par stimuli.csv pour résoudre Stimulus → CID
  2. Normalisation: scores Dravnieks [0–5] → [0.0–1.0] (÷5)
  3. Null handling: NaN ignorés — le descripteur est exclu du vecteur, pas mis à 0
  4. Mapping      : descripteur dominant → layer1_category via descriptor_map_v1.json
  5. Marquage     : data_origin = "human_perceptual"
"""

import io
import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

import requests
import polars as pl

# ---------------------------------------------------------------------------
# Gestion optionnelle de pyrfume
# ---------------------------------------------------------------------------
try:
    import pyrfume
    USE_PYRFUME = True
except ImportError:
    USE_PYRFUME = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCHEMAS_DIR = Path("schemas")
DESCRIPTOR_MAP_PATH = SCHEMAS_DIR / "descriptor_map_v1.json"

DATASET = "dravnieks_1985"
DRAVNIEKS_MAX_SCORE = 5.0

PYRFUME_RAW = "https://raw.githubusercontent.com/pyrfume/pyrfume-data/main/dravnieks_1985"


# ---------------------------------------------------------------------------
# Chargement du descriptor map
# ---------------------------------------------------------------------------

def load_descriptor_map(path: Path) -> dict:
    """
    Charge descriptor_map_v1.json et retourne {descriptor_id: layer1_category}.
    Input  : chemin vers descriptor_map_v1.json
    Output : dict de mapping descripteur → catégorie
    """
    if not path.exists():
        print(f"  WARNING: {path} not found. Category inference will use 'unclassified'.")
        return {}
    with open(path) as f:
        data = json.load(f)
    return {d["id"]: d["layer1"] for d in data.get("descriptors", [])}


# ---------------------------------------------------------------------------
# Chargement des CSV Pyrfume
# ---------------------------------------------------------------------------

def load_pyrfume_csv(filename: str) -> pl.DataFrame:
    """
    Charge un CSV depuis le dataset Dravnieks via pyrfume ou HTTP fallback.
    Input  : nom du fichier (ex: 'molecules.csv')
    Output : DataFrame Polars
    """
    if USE_PYRFUME:
        try:
            import pandas as pd
            df_pd = pyrfume.load_data(f"{DATASET}/{filename}").reset_index()
            return pl.from_pandas(df_pd)
        except Exception as e:
            print(f"  pyrfume.load_data failed ({e}), falling back to HTTP...")

    url = f"{PYRFUME_RAW}/{filename}"
    print(f"  Fetching: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pl.read_csv(io.StringIO(response.text))


# ---------------------------------------------------------------------------
# Inférence de catégorie
# ---------------------------------------------------------------------------

def infer_category(scores: dict, descriptor_map: dict) -> tuple:
    """
    Déduit layer1_category et layer3_descriptor depuis les scores normalisés.
    Prend le descripteur dominant (score le plus élevé) et le mappe.
    Input  : {descripteur: score_normalisé}, mapping descripteur→catégorie
    Output : (layer1_category, layer3_descriptor)
    """
    if not scores:
        return "unclassified", "Unknown"

    top_descriptor = max(scores, key=scores.get)

    # Correspondance exacte
    category = descriptor_map.get(top_descriptor.upper())

    # Correspondance partielle si rien trouvé
    if not category:
        for key, cat in descriptor_map.items():
            if key in top_descriptor.upper() or top_descriptor.upper() in key:
                category = cat
                break

    return (category or "unclassified"), top_descriptor.title()


# ---------------------------------------------------------------------------
# Construction du dict .scent
# ---------------------------------------------------------------------------

def build_scent_dict(
    cid: int,
    smiles,
    inchi_key,
    iupac_name,
    common_name,
    mol_weight,
    dim_map: list,
    data_vector: list,
    category: str,
    descriptor: str,
) -> dict:
    """
    Construit un dict conforme à scent_schema.json v1.1.0.
    Input  : identifiants chimiques + vecteur perceptuel normalisé + labels
    Output : dict prêt pour json.dump
    """
    return {
        "schema_version": "1.1.0",
        "header": {
            "capture_type": "static",
            "data_origin": "human_perceptual",
            "dimension_map": dim_map,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_dataset": f"pyrfume:{DATASET}",
        },
        "chemical_info": {
            "pubchem_cid": cid,
            "smiles": smiles,
            "inchi_key": inchi_key,
            "iupac_name": iupac_name,
            "common_name": common_name,
            "molecular_weight": mol_weight,
        },
        "labels": {
            "layer1_category": category,
            "layer3_descriptor": descriptor,
        },
        "data": data_vector,
        "metadata": {
            "source": "Pyrfume / Dravnieks 1985 Atlas of Odor Character Profiles",
            "scale_original": "0–5 (Dravnieks panelist rating)",
            "normalization": "÷5 → [0.0, 1.0]",
            "n_descriptors_used": len(dim_map),
            "n_descriptors_total": 146,
        },
    }


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def run_import(limit=None, output_dir=OUTPUT_DIR):
    """
    Pipeline complet : Pyrfume Dravnieks → fichiers .scent.
    Jointure : behavior_1 → stimuli (CID) → molecules (chimie)
    Input  : limit (int, optionnel), output_dir (Path)
    Output : fichiers cid_XXXX.scent dans output_dir
    """
    print("\n ScentLib — Pyrfume Real Import (Dravnieks 1985)")
    print("=" * 55)

    # 0. Descriptor map
    print("\n[0/5] Loading descriptor map...")
    descriptor_map = load_descriptor_map(DESCRIPTOR_MAP_PATH)
    print(f"  {len(descriptor_map)} descriptors loaded.")

    # 1. Téléchargement
    print("\n[1/5] Downloading Pyrfume datasets...")
    molecules_df = load_pyrfume_csv("molecules.csv")
    stimuli_df   = load_pyrfume_csv("stimuli.csv")
    behavior_df  = load_pyrfume_csv("behavior_1.csv")

    print(f"  molecules : {len(molecules_df)} rows")
    print(f"  stimuli   : {len(stimuli_df)} rows | cols: {stimuli_df.columns}")
    print(f"  behavior  : {len(behavior_df)} rows | {len(behavior_df.columns)} cols")

    # 2. Résolution des colonnes
    print("\n[2/5] Resolving column names...")

    stim_col_b = next((c for c in behavior_df.columns  if "Stimulus" in c or c == "index"), None)
    stim_col_s = next((c for c in stimuli_df.columns   if "Stimulus" in c or c == "index"), None)
    cid_col_s  = next((c for c in stimuli_df.columns   if "CID" in c.upper()), None)
    cid_col_m  = next((c for c in molecules_df.columns if "CID" in c.upper() or c == "index"), None)

    if not all([stim_col_b, stim_col_s, cid_col_s, cid_col_m]):
        print("  ERROR: Cannot resolve join columns.")
        print(f"    behavior  columns : {behavior_df.columns[:5]}")
        print(f"    stimuli   columns : {stimuli_df.columns}")
        print(f"    molecules columns : {molecules_df.columns[:5]}")
        sys.exit(1)

    print(f"  Join path: behavior['{stim_col_b}'] → stimuli['{stim_col_s}'] → stimuli['{cid_col_s}'] → molecules['{cid_col_m}']")

    smiles_col = next((c for c in molecules_df.columns if "SMILES" in c.upper()), None)
    inchi_col  = next((c for c in molecules_df.columns if "InChIKey" in c), None)
    iupac_col  = next((c for c in molecules_df.columns if "IUPAC" in c.upper()), None)
    name_col   = next((c for c in molecules_df.columns if c.lower() == "name"), None)
    mw_col     = next((c for c in molecules_df.columns if "Weight" in c or c == "MW"), None)

    # Colonnes descripteurs = tout sauf la colonne Stimulus
    descriptor_cols = [c for c in behavior_df.columns if c not in {stim_col_b, "CID", "index"}]
    print(f"  Found {len(descriptor_cols)} perceptual descriptor columns.")

    # 3. Jointure 3 tables
    print("\n[3/5] Joining behavior → stimuli → molecules...")

    merged = behavior_df.join(
        stimuli_df.select([stim_col_s, cid_col_s]),
        left_on=stim_col_b,
        right_on=stim_col_s,
        how="inner"
    ).join(
        molecules_df,
        left_on=cid_col_s,
        right_on=cid_col_m,
        how="inner"
    )

    print(f"  Merged: {len(merged)} molecules with complete chemical + perceptual data")

    if limit:
        merged = merged.head(limit)
        print(f"  (Limited to {limit} for this run)")

    # 4. Normalisation + export
    print(f"\n[4/5] Normalizing scores [0–5] → [0.0–1.0]...")
    print(f"\n[5/5] Generating .scent files in {output_dir}/...")

    success, skipped = 0, 0

    for row in merged.to_dicts():
        try:
            cid = int(row[cid_col_s])
            scores_norm = {}
            data_vector = []
            valid_dims  = []

            for col in descriptor_cols:
                val = row.get(col)
                if val is None:
                    continue
                if isinstance(val, float) and val != val:  # NaN
                    continue
                norm = round(float(val) / DRAVNIEKS_MAX_SCORE, 4)
                norm = max(0.0, min(1.0, norm))  # clamp
                scores_norm[col] = norm
                data_vector.append(norm)
                valid_dims.append(col)

            if not data_vector:
                skipped += 1
                continue

            category, descriptor = infer_category(scores_norm, descriptor_map)

            scent_dict = build_scent_dict(
                cid=cid,
                smiles=row.get(smiles_col) if smiles_col else None,
                inchi_key=row.get(inchi_col) if inchi_col else None,
                iupac_name=row.get(iupac_col) if iupac_col else None,
                common_name=row.get(name_col) if name_col else None,
                mol_weight=float(row[mw_col]) if mw_col and row.get(mw_col) is not None else None,
                dim_map=valid_dims,
                data_vector=data_vector,
                category=category,
                descriptor=descriptor,
            )

            file_path = output_dir / f"cid_{cid}.scent"
            with open(file_path, "w") as f:
                json.dump(scent_dict, f, indent=2, ensure_ascii=False)

            success += 1

        except Exception as e:
            print(f"  ERROR on CID {row.get(cid_col_s, '?')}: {e}")
            skipped += 1

    print(f"\n{'=' * 55}")
    print(f" Done! {success} files generated | {skipped} skipped")
    print(f" Output: {output_dir.resolve()}")
    print(f"{'=' * 55}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    default_output = script_dir.parent / "data" / "processed"

    parser = argparse.ArgumentParser(
        description="Import Pyrfume Dravnieks 1985 dataset into ScentLib .scent format"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit number of molecules (e.g. --limit 10 for a test run)"
    )
    parser.add_argument(
        "--output", type=str, default=str(default_output),
        help=f"Output directory for .scent files (default: {default_output})"
    )
    args = parser.parse_args()
    
    # On s'assure que le dossier existe avant de lancer l'import
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    run_import(limit=args.limit, output_dir=output_path)