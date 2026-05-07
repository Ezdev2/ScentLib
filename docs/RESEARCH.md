# ScentLib — Research Protocol

**Title:** *A Unified Generative-Discriminative Framework for Digital Olfaction: From Molecular Graph to Perceptual Signal*

* **Author:** Ezra Fanomezantsoa  
* **Research Classification:** Applied Research - Experimental Development  
* **Status:** Pre-experimental - Protocol under construction 
* **Last Updated:** 7 May 2026

---

## 1. Research Question

> *"Can a Unified Generative-Discriminative Framework (VAE/GAN architecture) outperform traditional regression models in both classifying and synthesizing digital olfactory signals, using molecular graph representations as input?"*

This question sits at the intersection of three fields:
- **Cheminformatics** — molecular graph representation (SMILES → graph)
- **Deep Learning** — Graph Neural Networks (GNN), generative models (VAE, GAN)
- **Psychophysics** — human perceptual ratings (Dravnieks 1985 Atlas)

The practical output is a system capable of receiving a molecular structure and producing a `.scent` file with `data_origin: "ai_generated"` — a digital olfactory fingerprint that can be compared against real human panel data and physically rendered by the ScentOutput (P6).

---

## 2. Research Context & Motivation

### 2.1 The Gap in Digital Olfaction

Sound has MP3. Image has JPEG. Olfaction has no universally accepted digital format, no open pipeline from molecule to perceptual signal, and no low-cost hardware standard. ScentLib addresses this gap with the `.scent` format as the unifying standard.

The scientific challenge is the **molecule-to-odor prediction problem**: given a molecular structure (SMILES string), predict how it will be perceived by a human panel across the 146 Dravnieks descriptors. This is a high-dimensional regression problem on sparse, noisy human data.

### 2.2 Why a Generative-Discriminative Approach?

Traditional approaches treat molecule-to-odor prediction as a pure regression problem (input: molecular fingerprint → output: perceptual vector). This has two limitations:

1. **Data scarcity** — The Dravnieks dataset covers only ~160 molecules. Standard supervised models overfit on this scale.
2. **No synthesis capability** — A discriminative-only model can classify but cannot generate novel olfactory profiles for molecules outside the training set.

A **generative model** (VAE or GAN) solves both problems:
- The generative "brain" can produce synthetic training data to augment the small Dravnieks dataset (data augmentation)
- The same model can synthesize novel `.scent` profiles for molecules it has never seen, moving from "Digital Nose" (recognition) to "Digital Architect" (synthesis)

### 2.3 Geographical Relevance — Madagascar Context

This research is conducted in a tropical environment (Mahajanga, Madagascar). High humidity and temperature directly affect the sensitivity curves of MQ-series gas sensors used in the ScentBox (P4). This creates a unique research opportunity: quantifying the impact of tropical environmental conditions on e-nose precision and developing a compensation model specific to this context. This is the basis for Axis 3 of the publication plan (Section 7).

---

## 3. Objectives

### Primary Objective
Develop and validate a GNN-based generative model (ScentPredictor, P5) capable of predicting normalized Dravnieks perceptual vectors from molecular SMILES strings, with a Mean Squared Error (MSE) below `0.05` on the held-out test set.

### Secondary Objectives
1. Demonstrate that the generative component (VAE/GAN) outperforms a discriminative-only baseline (Morgan fingerprint + MLP regression) on the Dravnieks test set.
2. Quantify the perceptual fidelity of the ScentOutput (P6) reconstruction relative to the original molecule, using a double-blind human panel.
3. Characterize the impact of tropical humidity and temperature on MQ-sensor accuracy and develop a BME280-based compensation model.

---

## 4. Hypotheses

**H1 — Generative Superiority:** A VAE/GAN architecture trained on molecular graphs will achieve lower MSE on Dravnieks perceptual vectors than a Morgan fingerprint + MLP baseline, due to its ability to learn latent chemical-perceptual relationships rather than fixed fingerprint patterns.

**H2 — Perceptual Fidelity:** A double-blind panel will rate the ScentOutput reconstruction of a ScentPredictor-generated profile at ≥ 7/10 similarity to the original molecule's odor, demonstrating that the digital-to-physical pipeline preserves perceptual meaning.

**H3 — Environmental Sensitivity:** MQ-sensor readings will vary by more than 15% across the humidity range 60–95% RH (typical Mahajanga range) without compensation, and the BME280-based correction will reduce this variance to below 5%.

---

## 5. Methodology — Triple Validation Protocol

The experimental design uses three sequential validation layers, each targeting a different component of the ScentLib pipeline.

---

### Validation A — Chemical Metrology (ScentBox P4 Stability)

**Objective:** Establish that the ScentBox produces stable, repeatable sensor readings before using its output as training data.

**Procedure:**
1. Select 3 pure reference molecules with well-characterized odor profiles: **d-Limonene** (citrus), **Vanillin** (vanilla), **Ethyl acetate** (fruity/solvent).
2. Prepare 3 concentrations of each molecule: 10 ppm, 50 ppm, 100 ppm (diluted in odorless mineral oil).
3. Run 50 consecutive captures per concentration per molecule with the ScentBox (P4).
4. Record all captures as `sensor_raw` `.scent` files via the ScentLib Core logging mode.
5. Compute the standard deviation of each sensor channel across the 50 captures.

**Acceptance Metric:** Coefficient of Variation (CV) ≤ 5% on all sensor channels across 50 captures. This corresponds to ≥ 95% repeatability.

**Environmental Control:** All captures performed at controlled temperature (25°C ± 1°C) and humidity (50% RH ± 5%), using a sealed capture chamber. A separate capture series at ambient tropical conditions (32°C, 80% RH) will quantify H3.

**Reference Instrument:** A PID (Photoionization Detector) will be used as an independent reference to validate the absolute concentration of the test samples, establishing a calibration baseline for the MQ sensors.

---

### Validation B — Algorithmic Validation (ScentPredictor P5 Accuracy)

**Objective:** Measure the prediction accuracy of the GNN model against held-out human perceptual data.

**Dataset:** Dravnieks 1985 Atlas via Pyrfume (144 molecules, 146 descriptors, already processed into `.scent` files). Split: 80% training, 20% test (held-out, never seen during training).

**Model Architecture:**

*Baseline (discriminative):*
- Input: Morgan Fingerprint (radius=2, 2048 bits) from RDKit
- Model: Multi-Layer Perceptron (3 layers, ReLU activation)
- Output: 146-dimensional vector, Sigmoid activation → `[0.0, 1.0]`

*Proposed model (generative-discriminative):*
- Input: Molecular graph from SMILES (atoms as nodes, bonds as edges) via RDKit + PyTorch Geometric
- Encoder: D-MPNN (Directed Message Passing Neural Network) — learns bond topology
- Latent space: VAE bottleneck (reparameterization trick)
- Decoder: Produces 146-dimensional Dravnieks vector, Sigmoid activation
- Loss: Weighted MSE (sparse vector) + KL divergence regularization

**Training Protocol:**
- Optimizer: Adam, learning rate `1e-3` with cosine annealing
- Batch size: 16 (small dataset constraint)
- Data augmentation: VAE generative sampling from the latent space to produce synthetic training molecules
- Early stopping: patience = 20 epochs on validation loss

**Evaluation Metrics:**

| Metric | Formula | Threshold |
|---|---|---|
| MSE | `mean((y_pred - y_true)²)` | < 0.05 |
| Cosine Similarity | `(A·B) / (‖A‖×‖B‖)` | > 0.85 |
| Perceptual Distance | Euclidean distance in Dravnieks space | < 0.3 |
| Top-1 Category Accuracy | `layer1_category` correct | > 80% |

All predicted outputs are stored as `.scent` files with `data_origin: "ai_generated"` and a `labels.confidence` score derived from the VAE reconstruction probability.

---

### Validation C — Sensory Validation (Double-Blind Panel)

**Objective:** Validate the end-to-end perceptual fidelity of the pipeline — from ScentPredictor prediction to ScentOutput physical synthesis.

**Panel:** Minimum 12 participants, non-expert, no known anosmia.

**Procedure:**

1. Select 5 test molecules from the held-out test set (chosen to cover diverse `layer1_category` values).
2. For each molecule, prepare two samples:
   - **Sample A:** The real molecule at standardized concentration (ground truth).
   - **Sample B:** The ScentOutput (P6) reconstruction driven by the ScentPredictor (P5) predicted `.scent` vector.
3. Present A and B to each participant in randomized order (double-blind: neither participant nor evaluator knows which is A or B).
4. Participants rate similarity on a **0–10 scale** and identify the top 3 Dravnieks descriptors using the Scent Player (P3) interface.

**Evaluation Metrics:**

| Metric | Description | Threshold |
|---|---|---|
| Similarity Score | Mean panel rating A vs B | ≥ 7.0 / 10 |
| Descriptor Agreement | % overlap between panel-selected descriptors for A and B | ≥ 60% |
| Blind Identification | % of participants who cannot distinguish A from B | ≥ 40% |

**Ethical note:** Participants will be informed that they are evaluating synthetic reconstructions of natural scents. All molecules used are non-toxic at experimental concentrations (GRAS — Generally Recognized As Safe).

---

## 6. Data Collection Timeline

| Phase | Activity | Tool | Expected Output |
|---|---|---|---|
| **01 — Calibration** | ScentBox stability (50 captures × 3 molecules × 3 concentrations) | ScentBox P4 + PID reference | Validated `sensor_raw` baseline, CV ≤ 5% |
| **02 — Featurization** | SMILES → molecular graphs for all 144 Dravnieks molecules | RDKit + PyTorch Geometric | Graph dataset ready for GNN training |
| **03 — Training** | GNN baseline + VAE/GAN model training | PyTorch, GPU (Dr. Geerish lab) | Trained model weights, MSE < 0.05 |
| **04 — Generation** | Predict 100 virtual `.scent` profiles for novel molecules | ScentPredictor P5 | 100 `ai_generated` `.scent` files |
| **05 — Synthesis** | Physical rendering of 5 selected predictions | ScentOutput P6 | Blended scent samples for panel |
| **06 — Panel** | Double-blind sensory evaluation | Scent Player P3 + panel | Similarity scores, descriptor agreement |
| **07 — Correlation** | Cross-validation: sensor_raw vs ai_generated vs human_perceptual | ScentLib Core P1 | Confusion matrix, perceptual distance map |

---

## 7. Publication Axes

**Axis 1 — Standard & Interoperability**
> *"The `.scent` Format: An Open Standard for Interoperable Digital Olfaction Data"*

Target: Journal of Chemical Information and Modeling (JCIM) or Sensors (MDPI).
Contribution: The schema, taxonomy, and validation pipeline as a reusable open standard.

**Axis 2 — Generative AI for Olfaction**
> *"From Molecular Graph to Perceptual Signal: A Generative-Discriminative GNN Framework for Odor Synthesis"*

Target: NeurIPS Workshop on AI for Science, or Chemosensory Perception journal.
Contribution: The VAE/GAN architecture, the data augmentation strategy, and the digital-to-physical validation protocol.

**Axis 3 — Low-Cost E-Nose in Tropical Environments**
> *"Humidity-Aware MQ-Sensor Compensation for Low-Cost E-Nose Deployment in Tropical Climates"*

Target: Sensors and Actuators B: Chemical (Elsevier).
Contribution: The BME280-based compensation model and its validation at Madagascar ambient conditions. This axis is unique to this research context and fills a documented gap in the e-nose literature (most studies conducted at 20–25°C, 40–60% RH).

---

## 8. Required Materials & Infrastructure

### Chemicals
| Molecule | CAS | Odor Profile | Role |
|---|---|---|---|
| d-Limonene | 5989-27-5 | Citrus, orange | Reference — citrus family |
| Vanillin | 121-33-5 | Vanilla, sweet | Reference — spicy/warm family |
| Ethyl acetate | 141-78-6 | Fruity, solvent | Reference — fruity/chemical boundary |
| Benzaldehyde | 100-52-7 | Almond, cherry | Reference — fruity family |
| Linalool | 78-70-6 | Floral, lavender | Reference — floral family |

### Hardware
- ScentBox (P4) — ESP32 + MQ-3, MQ-135, MQ-138, BME280
- ScentOutput (P6) — Arduino + micro-pumps + PWM driver
- PID reference sensor (e.g., ppbRAE 3000) — for concentration calibration
- Sealed glass capture chamber (chemically neutral)

### Software & Compute
- ScentLib Core (P1) — validation, analytics, `.scent` generation
- RDKit — SMILES parsing, Morgan fingerprints
- PyTorch + PyTorch Geometric — GNN training
- GPU access — Dr. Geerish laboratory (training phase)
- ScentLib logging mode — continuous `sensor_raw` recording at 100ms intervals

---

## 9. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Dravnieks dataset too small for GNN | High | High | VAE data augmentation + transfer learning from larger olfaction datasets (GOODSCENTS, Leffingwell) |
| MQ sensors drift in tropical humidity | High | Medium | BME280 real-time compensation (H3 research axis) |
| ScentOutput imprecision at low concentrations | Medium | High | PWM calibration curve per pump, minimum pulse width characterization |
| Panel subjectivity bias | Medium | Medium | Double-blind protocol, minimum 12 participants, statistical significance testing (t-test, p < 0.05) |
| GPU unavailability | Low | Medium | Model designed to train on CPU in < 48h for small dataset size |

---

## 10. Connection to ScentLib Architecture

Every experimental phase maps directly to a ScentLib pillar:

```
Molecule (SMILES)
    ↓ P5 ScentPredictor (GNN inference)
.scent file [ai_generated]
    ↓ P1 Core (validation + analytics)
    ↓ P3 Scent Player (visualization + panel interface)
    ↓ P6 ScentOutput (physical synthesis)
Physical odor sample
    ↓ Human panel + P4 ScentBox (capture)
.scent file [human_perceptual] + [sensor_raw]
    ↓ P1 Core (compare, match, cosine similarity)
Validation result
```

The `.scent` format is the thread that connects every step. Without the standard, the pipeline cannot be validated end-to-end. This is why the Core (P1) was built first.

---

*This document is a living research protocol. It will be updated as the project progresses through each experimental phase. The final version will serve as the methodology chapter of the thesis.*