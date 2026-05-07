```
    ScentLib - Codex Binaire SCNT
    ================================================================
    Conversion bidirectionnelle : dict JSON (.scent) <-> bytes (.scnt)

    Format SCNT v1 - Structure :
    [HEADER   16 bytes] Magic + Version + Flags + Timestamp
    [CAPTURE   4 bytes] capture_type + data_origin + n_dimensions
    [DIM_MAP  variable] N × (uint8_len + UTF-8 bytes)
    [DATA      N×2 bytes] float16 little-endian
    [CHEM_INFO variable] CID + SMILES + IUPAC + common_name + MW
    [LABELS   variable] layer1 + layer2 + layer3 + intensity + confidence
    [METADATA variable] uint8 n_keys × (key_string + value_string)
    [CRC32     4 bytes] checksum sur tout le contenu précédent

    Précision float16 :
    Erreur maximale observée sur Dravnieks : < 0.0003
    Seuil perceptuel humain : ~0.05 (50x au-dessus)
    → Aucune perte d'information perceptuelle

    Usage :
        from scentlib.core.binary import encode, decode

        # JSON dict → bytes
        raw_bytes = encode(scent_dict)
        with open("cid_460.scnt", "wb") as f:
            f.write(raw_bytes)

        # bytes → JSON dict
        with open("cid_460.scnt", "rb") as f:
            raw_bytes = f.read()
        scent_dict = decode(raw_bytes)
```