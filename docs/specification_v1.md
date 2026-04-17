# ScentLib Technical Specification (v1.0)

This document defines the structure and rules of the `.scent` format as specified in the official schema files.

## 1. File Structure
A `.scent` file is a JSON object validated by `schemas/scent_schema.json`. It relies on three main pillars:
- **`schema_version`**: Ensures backward compatibility.
- **`header`**: Metadata about the capture type and data origin.
- **`data`**: A normalized numerical vector.

## 2. Global Taxonomy (Ontology)
Classification is hierarchical to allow for both broad searching and precise description:
- **Layer 1 (Category)**: **Mandatory**. Defined in `schemas/categories_v1.json`.
- **Layer 2 (Sub-category)**: Optional intermediate grouping.
- **Layer 3 (Descriptor)**: Specific term (e.g., Dravnieks 146 descriptors).

## 3. Data Normalization
To ensure interoperability between different sensors (e-noses) and datasets (Pyrfume), all numerical values in the `data` array **must be normalized between 0.0 and 1.0**.

## 4. Data Origins
- `human_perceptual`: Data from human sensory panels.
- `sensor_raw`: Raw signals from physical electronic noses.
- `simulated`: Algorithmically generated data for model testing.
- `ai_generated`: Predictions from AI models (e.g., Molecule-to-Odor).