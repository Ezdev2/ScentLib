# ScentLib — Technical Decisions & Scientific Justifications

**Version:** 1.0  
**Author:** Ezra Fanomezantsoa  
**Status:** Living Document — updated as the project evolves  
**Scope:** Covers all architectural, algorithmic, and format decisions made in ScentLib Core (P1)

---

## 1. The `.scent` Format — Why JSON?

**Decision:** The `.scent` format is a JSON object validated against a JSON Schema (Draft-07).

**Justification:**

The primary requirement for ScentLib is interoperability — the ability for any system, any language, and any researcher to read and write olfactory data without proprietary tooling. JSON satisfies this requirement better than any binary-first alternative at this stage of the project for three reasons:

1. **Human readability** — A researcher opening a `.scent` file with a text editor can immediately understand its content without a decoder. This is critical for scientific trust and reproducibility.
2. **Universal tooling** — Every programming language, every operating system, and every database system has native JSON support. No SDK is required to read a `.scent` file.
3. **Extensibility** — New fields can be added to the JSON structure without breaking existing parsers, provided the schema uses `additionalProperties: false` selectively (which it does: only at the root level, not inside `metadata`).

**Binary extension:** The format is explicitly designed to be binarizable into the `SCNT` format (see Section 9). JSON is the canonical exchange format; binary is the storage optimization. This mirrors the relationship between XML and binary in formats like HDF5, or between JSON and MessagePack in network protocols.

---

## 2. Schema Versioning — Why SemVer?

**Decision:** `schema_version` follows Semantic Versioning (`MAJOR.MINOR.PATCH`).

**Justification:**

Olfactory datasets have long lifespans. The Dravnieks dataset we use dates from 1985. A `.scent` file generated today must still be readable by a ScentLib parser in 2035. SemVer provides a machine-readable compatibility contract:

- **PATCH** (e.g., `1.0.0 → 1.0.1`): Bug fix in schema description, no structural change. All existing files remain valid.
- **MINOR** (e.g., `1.0.0 → 1.1.0`): New optional fields added. Existing files remain valid; new parsers gain new capabilities.
- **MAJOR** (e.g., `1.x.x → 2.0.0`): Breaking structural change. Parsers must handle migration explicitly.

This is the same versioning strategy used by Protocol Buffers, Apache Avro, and JSON Schema itself.

---

## 3. Data Normalization — Why `[0.0, 1.0]` and Why `÷5`?

**Decision:** All values in the `data` array must be normalized to `[0.0, 1.0]`. For Dravnieks data, normalization is achieved by dividing raw scores by 5.

**Scientific justification:**

The Dravnieks (1985) Atlas of Odor Character Profiles uses a rating scale of **0 to 5** for each of its 146 descriptors:
- `0` = "the descriptor does not apply at all"
- `5` = "the descriptor applies perfectly"

This scale was chosen by Dravnieks based on panel consensus studies. The division by 5 is a **linear min-max normalization** that maps the original scale to `[0.0, 1.0]` without any distortion of the relative relationships between values:

```
normalized = raw_score / 5.0
```

This preserves the proportionality between scores. A molecule rated `3.0` on ROSE and `1.5` on FLORAL retains its 2:1 ratio after normalization (`0.6` and `0.3`).

**Engineering justification:**

Normalization to `[0.0, 1.0]` is mandatory for three reasons:

1. **Metric compatibility** — Cosine similarity and Euclidean distance are only meaningful when all dimensions share the same scale. A raw sensor reading of `4.2V` and a Dravnieks score of `3.5` cannot be compared in the same vector space without normalization.
2. **Hardware agnosticism** — Different e-nose sensors produce outputs in different voltage ranges (0–3.3V, 0–5V, 12-bit ADC values 0–4095). Normalization to `[0.0, 1.0]` makes all sensor types interoperable within the same schema.
3. **Neural network compatibility** — When the `data` vector is used as input to the ScentPredictor (P5), values in `[0.0, 1.0]` are the expected input range for sigmoid-activated models and match the target range of the output layer.

**Validation enforcement:** The schema enforces `"minimum": 0, "maximum": 1` on every element of the `data` array. Any out-of-range value triggers a fatal `ValidationError` before the file is written to disk.

---

## 4. Three-Layer Taxonomy — Why a Hierarchical Ontology?

**Decision:** Labels are structured in three layers: `layer1_category` (mandatory), `layer2_sub_category` (optional), `layer3_descriptor` (optional).

**Scientific justification:**

Olfactory perception is inherently hierarchical. Psychophysical research (Dravnieks 1985, Carrasco et al. 2016) consistently shows that human odor perception organizes itself at multiple levels of granularity:

- **Level 1 (Family):** "This smells floral." — broad perceptual category, fast and robust classification.
- **Level 2 (Sub-family):** "This smells like rose." — intermediate grouping, useful for perfumery and sensor calibration.
- **Level 3 (Descriptor):** "The dominant note is ROSE." — precise Dravnieks term, useful for scientific reproducibility.

This mirrors established olfactory ontologies: the IFRA taxonomy, the IAWPRC environmental odor wheel, and the Dravnieks NMF cluster analysis all use multi-level classification.

**Engineering justification:**

The three-layer structure enables queries at different levels of precision without schema changes. A perfumer queries by `layer2`; a machine learning model trains on `layer1`; a chemist references `layer3`. A single schema serves all use cases.

**Layer 1 is the only mandatory label** because it is the minimum information needed for meaningful classification. Layers 2 and 3 are optional to accommodate sensor data where chemical identity is unknown.

---

## 5. `data_origin` Field — Why Strict Enumeration?

**Decision:** The `data_origin` field accepts only five values: `human_perceptual`, `sensor_raw`, `simulated`, `ai_generated`, `computed_features`.

**Justification:**

In scientific data management, provenance is not cosmetic — it determines how data can be used, how it should be weighted, and how it can be compared. A vector rated by 50 human panelists (Dravnieks) carries fundamentally different epistemic weight than a vector predicted by a neural network.

The strict enumeration enforces explicit provenance declaration:

| Value | Source | Use Case |
|---|---|---|
| `human_perceptual` | Human sensory panel ratings | Ground truth for ML training |
| `sensor_raw` | E-nose hardware ADC readings | Real-time capture (ScentBox P4) |
| `simulated` | Algorithmically generated | Testing and validation |
| `ai_generated` | Model prediction output | ScentPredictor (P5) inference |
| `computed_features` | Cheminformatics (Mordred, Morgan) | Molecular featurization |

This distinction is enforced at the schema level so that no downstream system can accidentally treat a model prediction as a ground truth measurement.

---

## 6. Similarity Metrics — Why Two Different Metrics?

**Decision:** The `compare` command uses **cosine similarity**. The `match` command uses **Euclidean distance**.

**Mathematical justification:**

These two metrics answer fundamentally different questions:

**Cosine similarity** measures the *angle* between two vectors, independent of their magnitude:

```
cos(θ) = (A · B) / (‖A‖ × ‖B‖)
```

Result: `[0.0, 1.0]` where `1.0` = identical direction (same "shape" of scent profile).

Use case: Comparing the *character* of two odors. A rose at low concentration and a rose at high concentration should be similar — they have the same perceptual profile, just different intensities. Cosine similarity captures this correctly; Euclidean distance would penalize the difference in magnitude.

**Euclidean distance** measures the *absolute spatial separation* between two vectors:

```
d = √(Σ(aᵢ - bᵢ)²)
```

Result: `[0, ∞)` where `0` = identical vectors.

Use case: Finding the *closest match* in a perceptually uniform space like the Dravnieks 146-dimensional space, where all dimensions are already normalized and the magnitude differences are meaningful (a molecule that scores higher on ROSE genuinely smells more like rose).

**Practical rule:** Use cosine for qualitative comparison ("do these smell alike?"). Use Euclidean for quantitative retrieval ("find the 5 molecules most similar to this one in the database.").

---

## 7. Fingerprint — Why MD5 (Truncated)?

**Decision:** The `generate_fingerprint` function uses MD5, truncated to 10 hexadecimal characters.

**Justification:**

The fingerprint serves three purposes: duplicate detection, integrity verification, and fast indexing. MD5 is appropriate for all three in this context for the following reasons:

1. **Not a security hash** — MD5 is cryptographically broken and must never be used for authentication or tamper detection in adversarial contexts. Here, it is used for data deduplication in a trusted scientific pipeline, where collision attacks are not a threat model.
2. **Speed** — MD5 is significantly faster than SHA-256 for this non-security use case. On large libraries (10,000+ files), fingerprint generation speed matters.
3. **Truncation to 10 chars** — The collision probability for a 10-character hex string (40 bits) over a library of 10,000 molecules is approximately `10,000² / 2^41 ≈ 0.005%`. This is acceptable for duplicate detection. For cryptographic integrity, the full MD5 or SHA-256 is used in the binary `SCNT` format footer.

**Precision normalization:** Values are rounded to 2 decimal places before hashing to absorb micro-variations from floating-point arithmetic. Two vectors that are numerically identical up to sensor noise will produce the same fingerprint.

---

## 8. `dimension_map` — Why Self-Contained (Autonomous Mode)?

**Decision:** Every `.scent` file includes the full `dimension_map` array. The `feature_set_ref` shorthand is available but not used by default.

**Justification:**

The canonical design principle here is **self-containment**: a `.scent` file must be interpretable without any external registry, SDK, or network access. This is the same principle that makes CSV universally readable (headers in the file), that makes PNG self-describing (color space in the header), and that makes scientific data reproducible (metadata travels with the data).

The `feature_set_ref` shorthand (`"scentlib:dravnieks_146@v1"`) would reduce file size by ~2 KB per file, but would introduce a dependency on the ScentLib registry being available and stable. For a format intended to last decades and be used by researchers who may not have internet access, this is an unacceptable trade-off at the exchange format level.

**Compact mode** (using `feature_set_ref`) is reserved for internal storage optimization and binary encoding, where the registry is always co-located with the data. It is never the default for file exchange.

---

## 9. Binary Format `SCNT` — Design Rationale

**Decision:** The binary encoding of `.scent` files uses a custom format called `SCNT`, with `Float16` for the data vector and a fixed 16-byte header.

**Justification:**

**Header structure (16 bytes):**
```
Bytes 0–3  : Magic Number 0x53 0x43 0x4E 0x54 ("SCNT")
Bytes 4–5  : Schema version (uint16, e.g., 0x0001 = v1)
Bytes 6–7  : Flags (bit 0: compressed, bit 1: ai_data, bit 2: debug)
Bytes 8–15 : Timestamp (uint64, Unix epoch milliseconds)
```

**Float16 for the data vector:**

The data vector uses `float16` (IEEE 754 half-precision) instead of `float64` (standard Python float). This reduces the data vector size by 75%:
- `float64`: 146 dimensions × 8 bytes = 1,168 bytes
- `float16`: 146 dimensions × 2 bytes = 292 bytes

**Precision loss analysis:** `float16` has a precision of approximately 3 decimal places. Given that Dravnieks scores are normalized from a 0–5 integer scale divided by 5, the actual precision of the input data is 2 decimal places (`0.0, 0.2, 0.4, ... 1.0` in 0.2 steps). `float16` introduces no meaningful information loss for this use case.

**Estimated file sizes:**
| Format | Size per file | 10,000 files |
|---|---|---|
| JSON (current) | ~8 KB | ~80 MB |
| SCNT binary | ~2.7 KB | ~27 MB |
| SCNT + zstd compression | ~1.2 KB | ~12 MB |

**Compression suitability:** Dravnieks vectors are highly compressible because they are sparse — most molecules score `0.0` on most descriptors. zstd achieves ~55% compression on top of the binary encoding.

---

## 10. Three-Pass Validation — Why Not Just JSON Schema?

**Decision:** The `ScentValidator` runs three sequential validation passes: JSON Schema → taxonomy check → Pydantic model.

**Justification:**

Each pass catches a different class of error:

**Pass 1 — JSON Schema (`jsonschema`):**
Validates structure, types, required fields, value ranges, and string patterns. Catches: missing `schema_version`, `data` values outside `[0, 1]`, wrong `capture_type` enum value.

**Pass 2 — Taxonomy check (custom):**
Validates that `layer1_category` is a valid ID from `categories_v1.json`. JSON Schema could do this with an `enum`, but that would require updating the schema every time a category is added. Externalizing the taxonomy to `categories_v1.json` makes the category list the single source of truth, independently versioned.

**Pass 3 — Pydantic model:**
Validates semantic consistency that JSON Schema cannot express: `data` length must equal `dimension_map` length; if `dimension_map` is absent, `feature_set_ref` must be present. These are cross-field constraints that require programmatic logic.

**Error fatality:** All three passes raise exceptions on failure. There is no "soft warning" mode. A `.scent` file is either valid or it does not exist — this is the `Strict Schema Enforcement` invariant from the ScentLib blueprint.

---

## 11. Blend — Why Weighted Average and Why `deepcopy`?

**Decision:** The `blend` operation computes a weighted average of two data vectors. The output file is built from a `deepcopy` of the first input.

**Mathematical justification:**

```
blended[i] = v1[i] × ratio + v2[i] × (1 - ratio)
```

This is a **convex combination** of the two vectors, which guarantees that the result stays within `[0.0, 1.0]` as long as both inputs are within `[0.0, 1.0]` (which the validator enforces). The ratio parameter allows asymmetric blending: `ratio=0.7` means 70% of scent 1 and 30% of scent 2, directly analogous to how a perfumer would blend two concentrates.

**Engineering justification for `deepcopy`:**

Without `deepcopy`, the blend function would mutate the in-memory dictionary of the first scent file (Python dicts are passed by reference). This would corrupt the source data if the function is called multiple times in a pipeline. `deepcopy` creates a fully independent object, ensuring the blend operation has no side effects on its inputs. This is the **pure function** principle applied to data transformation.

---

## 12. `common_name` Sanitization — Why Reject CAS Numbers?

**Decision:** The `common_name` field rejects strings that are purely numeric (CAS registry numbers) and sets them to `null`.

**Justification:**

The Pyrfume dataset sometimes populates the `name` field with the CAS registry number (e.g., `"77-83-8"`) when no common name is available in its database. A CAS number in `common_name` is semantically incorrect — it belongs in a `cas_number` field (which could be added to `chemical_info` in a future schema version). Storing it in `common_name` would mislead any downstream system that displays this field to a user or uses it for text-based search.

The sanitization rule is: if the string, after removing hyphens, consists entirely of digits, treat it as a CAS number and set `common_name` to `null`. This is conservative — it may miss unusual CAS-like strings, but it will never discard a genuine common name.

---

*This document is part of the ScentLib Core documentation. It should be updated whenever a significant algorithmic or architectural decision is made. The goal is that any computer science researcher joining the project can understand not just what the code does, but why every choice was made.*