# ScentLib
**The Open Standard for Digital Olfaction**

ScentLib is an open-source library and data ecosystem designed to bring to olfaction what MP3 brought to sound: a universal, lightweight, and intelligent format for storing and exchanging olfactory data.

## The Vision

Digital olfaction is the next technological frontier. However, chemical and sensory data are currently fragmented and proprietary. ScentLib introduces the **`.scent`** file format — a hardware-agnostic data structure that unifies sensor capture (e-noses), human perceptual data, and AI-driven semantic interpretation under a single open standard.

> *"Just as Newton needed Calculus to explain gravity, I needed a technical framework — the `.scent` standard — to explain and transport digital odors."*

## The `.scent` Format

The `.scent` format is a self-contained JSON object (extensible to binary via the `SCNT` protocol) structured around four pillars:

1. **Header** — Capture type, data origin, dimension map, and timestamp.
2. **Chemical Info** — Standard molecular identifiers (SMILES, PubChem CID, InChIKey, IUPAC name).
3. **Labels** — Hierarchical olfactory taxonomy (Layer 1 → 2 → 3) based on the Dravnieks standard.
4. **Data** — Normalized perceptual or sensor vector, all values in `[0.0, 1.0]`.

All values are normalized to `[0.0, 1.0]` to ensure interoperability across sensor hardware, human panels, and AI models. Every file is validated against `schemas/scent_schema.json` (JSON Schema Draft-07) before being written to disk.

## The 6-Pillar Architecture

| Pillar | Name | Role | Status |
|---|---|---|---|
| **P1** | ScentLib Core | SDK, API, `.scent` standard, validation, analytics | ✅ Production Ready |
| **P2** | Scent Explorer | Cloud web visualizer & global database | 🔲 Planned |
| **P3** | Scent Player | Native desktop reader, offline, Radar Chart | 🔲 In Progress |
| **P4** | ScentBox | E-nose hardware acquisition (ESP32) | 🔲 Planned |
| **P5** | ScentPredictor | GNN-based molecule-to-odor AI model | 🔲 Planned |
| **P6** | ScentOutput | Physical scent synthesis cartridge (Arduino) | 🔲 Planned |

## Roadmap

### Phase 1 — Foundations (Complete)
- [x] `.scent` schema specification v1.1.0 (`scent_schema.json`)
- [x] Global olfactory taxonomy — 12 categories (`categories_v1.json`)
- [x] Dravnieks 146-descriptor map (`descriptor_map_v1.json`)
- [x] Pydantic v2 data models with strict runtime validation
- [x] Three-pass validator (JSON Schema → taxonomy → Pydantic)
- [x] Technical decisions documentation (`docs/TECHNICAL_DECISIONS.md`)

### Phase 2 — Data Pipeline (Complete)
- [x] Pyrfume → `.scent` conversion pipeline (`pyrfume_to_scent.py`)
- [x] 144 real `.scent` files from Dravnieks 1985 Atlas
- [x] Full CLI: `play`, `list`, `compare`, `match`, `blend`, `fingerprint`, `export`
- [x] FastAPI driver (`scentlib serve`) with `/scents`, `/color`, `/categories` endpoints
- [x] Stream support (`capture_type: stream`) with `StreamHandler`

### Phase 3 — Visualization & Intelligence (Next)
- [ ] Scent Player native desktop app (CustomTkinter + Matplotlib Radar Chart)
- [ ] Scent Explorer web app (React TSX + 3Dmol.js)
- [ ] ScentPredictor — GNN model (PyTorch + RDKit)

### Phase 4 — Hardware & Binary (Planned)
- [ ] `SCNT` binary format (`binary.py`) — 65–80% size reduction vs JSON
- [ ] ScentBox firmware (ESP32, C++)
- [ ] ScentOutput firmware (Arduino, PWM)

## Quick Start

```bash
git clone https://github.com/Ezdev2/ScentLib.git
cd ScentLib
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

**Populate the library from Pyrfume (Dravnieks 1985):**
```bash
python scripts/pyrfume_to_scent.py
```

**CLI commands:**
```bash
# Browse the library
scentlib list data/processed

# Search by category
scentlib list data/processed -q "floral"

# Visualize a scent profile
scentlib play data/processed/cid_6501.scent

# Compare two molecules (cosine similarity)
scentlib compare data/processed/cid_6501.scent data/processed/cid_1183.scent

# Find the 5 closest molecules in the library (Euclidean distance)
scentlib match data/processed/cid_6501.scent --top 5

# Blend two scents at 70/30 ratio
scentlib blend data/processed/cid_6501.scent data/processed/cid_1183.scent --ratio 0.7 --save blend.scent

# Export the full library to CSV or Parquet
scentlib export library.csv --dir data/processed

# Start the REST API driver
scentlib serve --port 8000
```

**API endpoints (once server is running):**
```
GET /scents              → list all scent IDs
GET /scents/{id}         → full .scent object + fingerprint
GET /scents/{id}/color   → category color mapping
GET /categories          → full category palette
```

## The `.scent` File — Example

```json
{
  "schema_version": "1.1.0",
  "header": {
    "capture_type": "static",
    "data_origin": "human_perceptual",
    "dimension_map": ["ROSE", "FLORAL", "FRUITY"],
    "timestamp": "2026-05-07T11:30:13.059760+00:00",
    "source_dataset": "pyrfume:dravnieks_1985"
  },
  "chemical_info": {
    "pubchem_cid": 1183,
    "smiles": "O=Cc1ccccc1",
    "iupac_name": "benzaldehyde",
    "common_name": "benzaldehyde",
    "molecular_weight": 106.12
  },
  "labels": {
    "layer1_category": "floral",
    "layer3_descriptor": "FRAGRANT"
  },
  "data": [0.676, 0.9, 0.12]
}
```

## Technical Design Decisions

All architectural and algorithmic choices are documented with scientific justifications in [`docs/TECHNICAL_DECISIONS.md`](docs/TECHNICAL_DECISIONS.md). Key decisions include:

- **Why `÷5` normalization** — Dravnieks panel scale, linear min-max, preserves proportionality
- **Why two similarity metrics** — cosine for character comparison, Euclidean for proximity retrieval
- **Why self-contained `dimension_map`** — interoperability over file size, same principle as CSV headers
- **Why three-pass validation** — each pass catches a different class of error
- **Why MD5 fingerprint** — speed over cryptographic strength for duplicate detection

## Distribution

- **Current:** Install directly via GitHub — `pip install -e .`
- **Planned:** PyPI release once the Core API is stabilized — `pip install scentlib`

## Contributing

ScentLib is in **Alpha**. The Core (P1) is production-ready. Contributions are welcome on schema extensions, new dataset converters, and the Scent Player UI. Open a GitHub Issue to discuss before submitting a PR.

---

*Distributed under the Apache License 2.0.*  
*Author: Ezra Fanomezantsoa*