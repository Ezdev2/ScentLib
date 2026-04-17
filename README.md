# ScentLib
**The Open Standard for Digital Olfaction**

ScentLib is an open-source library and data ecosystem designed to bring to olfaction what MP3 brought to sound: a universal, lightweight, and intelligent format for storing and exchanging olfactory data.

## The Vision
Digital olfaction is the next technological frontier. However, chemical and sensory data are currently fragmented and proprietary. ScentLib introduces the **`.scent`** file format—a hardware-agnostic data structure that unifies sensor capture (e-noses) and AI-driven semantic interpretation.

## The `.scent` Format
The `.scent` format is a JSON-based container (extensible to binary) structured into four layers:
1. **Context**: Environmental metadata (Temp, Humidity, Pressure).
2. **Signature**: Normalized raw sensor data or chemical fingerprints.
3. **Chemical**: Standard molecular mapping (SMILES, PubChem CID).
4. **Semantic**: Hierarchical ontology based on the Dravnieks standard.

## Roadmap
- [x] v1.0 Schema Specification (JSON Schema).
- [x] Global Taxonomy Definition (`categories_v1.json`).
- [ ] Pyrfume-to-Scent Bootstrapping Scripts.
- [ ] Core Python SDK (Read/Write/Validate).
- [ ] Binary Support (`SCNT` format via MessagePack).

## Setup & Development

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Ezdev2/ScentLib.git](https://github.com/Ezdev2/ScentLib.git)
   cd ScentLib
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```
4. Utilisation Rapide
   ```bash
   # Voir le catalogue
   scentlib list

   # Comparer deux molécules
   scentlib compare fichier1.scent fichier2.scent
   ```

## Distribution
- **Development Phase**: Currently, install directly via GitHub: `pip install -e .`
- **Future Release**: ScentLib will be available on PyPI for `pip install scentlib` once the core API is stabilized.

## Contributing
ScentLib is currently in **Pre-alpha / RFC (Request for Comments)**. We welcome suggestions regarding the schema or ontology via GitHub Issues.

---
*Distributed under the Apache License 2.0.*