# ScentLib — Research Protocol (Updated 7 May 2026)

**Title:** *A Unified Multi-modal Framework for Digital Olfaction: Bridging Chemical Structure, Sensor Signals, and Human Perception via the .scent Standard.*

* **Author:** Ezra Fanomezantsoa
* **Status:** Master’s Thesis Protocol - AI/ML Track
* **Focus:** Multi-modal Latent Mapping & Safety-Aware Prediction

---

## 1. Updated Research Question

> *"Can a Multi-modal Graph Neural Network (GNN) architecture create a unified latent space that aligns molecular structures (SMILES) and raw sensor signals (ScentBox) into a standardized perceptual output (.scent), while simultaneously identifying potential chemical hazards?"*

This evolution moves the research from a simple "prediction" task to a **Translation Task** between three worlds: **Chemistry** (SMILES), **Electronics** (Hardware signals), and **Senses** (Human Descriptors).

---

## 2. Updated Methodology: The Multi-modal Alignment

### 2.1 The "ScentPredictor" Core (P5) - AI Research Subject
The research will focus on a **Dual-Encoder Architecture**:
* **Encoder A (Chemical):** D-MPNN (Directed Message Passing Neural Network) to process molecular graphs.
* **Encoder B (Signal):** CNN-LSTM or Transformer-based encoder to process time-series data from the ScentBox (P4) sensors.
* **Shared Latent Space:** The goal is to "force" both encoders to map their inputs to the same vector representation for a given substance. 

### 2.2 Reverse Mapping (Scent-to-Molecule)
The framework will include a **Generative Decoder** capable of performing "Virtual Screening". Given a `.scent` target, the model will query a verified chemical database (PubChem/RDKit) to propose the most likely molecular candidates (Reverse Design).

---

## 3. New Research Axis: Safety & Ethics (The "Guardian" AI)

A critical addition to the research is the **Safety Classification Head**. 
* **The Hazard Predictor:** Alongside the 146 perceptual descriptors, the model will feature a binary classifier trained on toxicological data.
* **Goal:** Predict if a molecular structure or a detected gas signature presents a toxicity risk (LD50 thresholds, hazardous volatiles).
* **Impact:** This transforms ScentLib from a creative tool into a **Protected System**, capable of blocking the "ScentOutput" (P6) if a signature is deemed dangerous.

---

## 4. The "Studio Workflow" (Product Implementation)

The research results will be implemented into the **ScentLib Ecosystem** as follows:

| Component | Product Role | Connection to AI Research |
| :--- | :--- | :--- |
| **ScentLib Core (P1)** | The Language. | Validates the AI's output against the `.scent` schema. |
| **Scent Player (P3)** | The "Studio" / Console. | Real-time visualization of the AI's "Sensor-to-Scent" translation. |
| **ScentPredictor (P5)** | The Intelligence Engine. | **The Research Output.** Multi-modal mapping & Reverse Search. |
| **ScentBox (P4)** | The "Microphone". | Provides the raw training data for the Signal Encoder. |
| **Scent Explorer (P2)** | The Global Hub. | Cloud-based AI inference and "Open-Odor" community database. |

---

## 5. Revised Objectives (Master level)

1.  **Multi-modal Accuracy:** Achieve a high correlation (Cosine Similarity > 0.80) between predictions made from a *molecule* and those made from a *sensor capture* of the same substance.
2.  **Inversion Fidelity:** Demonstrate that the "Scent2Molecule" engine can correctly identify a top-5 match for a target profile in 70% of cases.
3.  **Hazard Detection:** Achieve > 90% accuracy in identifying hazardous molecules within the test set.

---

## 6. Geographical & Environmental Context (Mauritius)

The tropical conditions of Mauritius (high humidity) will be used to train the **Signal Encoder**. By feeding temperature and humidity (BME280) as metadata into the AI, the model will learn to "de-noise" sensor readings, making ScentLib's hardware-software bridge more robust than standard laboratory e-noses.

---

### **Summary of the "Originality" for PhD Committees:**
* **Architecture:** Multi-modal alignment (Graph + Time-series).
* **Innovation:** First open-source "Reverse Scent Design" engine.
* **Ethics:** Integrated safety-filter based on molecular toxicity prediction.

---

### **Abstract**

**Title:** *ScentLib: A Multi-modal Generative Framework for Standardizing and Translating Digital Olfactory Signatures*

**Keywords:** Digital Olfaction, Graph Neural Networks (GNN), Multi-modal Learning, Open Standards, Chemoinformatics.

**Background:** Digital olfaction remains fragmented due to the absence of a universal data standard and the high complexity of the "molecule-to-odor" mapping problem. While significant progress has been made in predictive AI, open-source frameworks that bridge the gap between chemical structure, hardware sensor signals, and human perception are still non-existent.

**Objectives:** This research introduces **ScentLib**, an open-source ecosystem centered around the `.scent` data standard. The primary objective is to develop a unified **Multi-modal GNN architecture** capable of aligning two disparate input types—molecular graphs (SMILES) and raw time-series gas sensor data—into a single, standardized latent space mapped to human perceptual descriptors.

**Methodology:** The framework utilizes a Dual-Encoder approach: a Directed Message Passing Neural Network (D-MPNN) for chemical featurization and a temporal encoder for e-nose signal processing. By training on the Dravnieks 1985 Atlas via the Pyrfume platform, the model performs multi-label classification of olfactory descriptors. Furthermore, a **Reverse Mapping** engine is implemented to enable virtual screening, allowing for the reconstruction of molecular candidates from target perceptual profiles.

**Significance & Originality:** Unlike proprietary models, ScentLib provides a transparent, end-to-end pipeline from digital capture to physical synthesis. The research introduces a novel **Safety-Aware Head** to identify hazardous molecular signatures, ensuring ethical deployment. Conducted in a tropical climate (Mauritius), the study also addresses environmental sensor drift, offering a robust compensation model for low-cost hardware in non-laboratory settings.

**Expected Impact:** ScentLib aims to become the "MP3 of Olfaction," democratizing digital scent technology for medical diagnostics, environmental monitoring, and interactive digital experiences, while providing the academic community with a rigorous, interoperable foundation for future olfactory research.

---
