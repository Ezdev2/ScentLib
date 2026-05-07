# ScentLib: Master Blueprint

Ce document est la source de vérité pour l'écosystème **ScentLib**. Il définit la structure, la vision et les interactions entre les 6 piliers du projet.

* **Version :** V1
* **Auteur :** Ezra Fanomezantsoa  
* **Status :** Production Ready

---

## 1. Architecture des 6 Piliers

| Pilier | Nom | Rôle | Technologie Clé |
| :--- | :--- | :--- | :--- |
| **P1** | **ScentLib Core** | La Loi (SDK, API, Standard `.scent`, Mathématiques & Validation) et le codex (Binarisation) | Python, FastAPI, Polars, Pydantic, Struct (Binary En/Decoder) |
| **P2** | **Scent Explorer** | Visualiseur Cloud & Banque de données mondiale. (Cloud & Collaboration) | React TSX, Tailwind, PostgreSQL |
| **P3** | **Scent Player** | Le Décodeur, Lecteur local natif, léger et offline (Desktop Natif Offline) | Python, CustomTkinter, Matplotlib |
| **P4** | **ScentBox** | L'Encodeur, Hardware d'acquisition (Nez électronique) | ESP32, Capteurs MQ, BME280, C++ Binary Stream |
| **P5** | **ScentPredictor** | L'Oracle (IA de prédiction moléculaire & Machine Learning) | PyTorch, GNN, RDKit |
| **P6** | **ScentOutput** | Le Rendu, Cartouche de synthèse physique. (Synthèse Physique) | Arduino, PWM, Micro-pompes |

---

## 2. Spécifications Techniques

### Pilier 01 : ScentLib Core (SDK & API)

* **Validation Pydantic :** Forçage du typage au runtime. Toute donnée non conforme au `scent_schema.json` déclenche une `ValidationError` fatale.
* **Moteur Polars :** Utilisation de `polars.DataFrame` pour les calculs de similarité (Cosine Similarity) sur les vecteurs Dravnieks. 
* **API Standard :** Endpoints REST avec support "Stream" pour les flux temps réel de la ScentBox.
* **Module Codex (`binary.py`) :** Implémentation du protocole **`SCNT`**. 
    * Conversion bidirectionnelle : `JSON <-> Binary`.
    * Support du **Mode Debug** : Possibilité de forcer la lecture humaine via un flag `--decompile` pour les développeurs.
    * Optimisation : Passage des vecteurs de `float64` (JSON) à `float16` (Binaire) pour diviser le poids par 4 sans perte de précision olfactive.
* **Rôle :** C'est le "Cerveau Administratif". Il vérifie que tout le monde respecte le schéma JSON qu'on a créé.

---

### Pilier 02 : Scent Explorer (Web Cloud)

* **Emplacement :** `/scent-explorer/`
* **Techno :** React TSX, Tailwind CSS, `3Dmol.js` (Visualisation moléculaire).
* **Travaux à faire :**
    * Développer le visualiseur de molécules 3D à partir des chaînes SMILES contenues dans le `.scent`.
    * Créer une interface de comparaison "Side-by-Side" pour comparer deux fichiers (ex: Perceptuel vs IA).
    * Mettre en place le système de "Drag & Drop" pour uploader un fichier local vers la banque de données globale.
* **Indexation Vectorielle :** Recherche par proximité olfactive via base de données vectorielle.
* **Visualisation Moléculaire :** Intégration de `3Dmol.js` pour le rendu des structures PubChem en temps réel. 
* **Authenticité :** Hashage SHA-256 de chaque fichier pour garantir l'intégrité des données de recherche.
* **Rôle :** C'est la "Bibliothèque Mondiale". Il permet de stocker les 15 000 fichiers issus de Pyrfume pour que tout le monde puisse les voir.

---

### Pilier 03 : Scent Player (App Native Desktop)

* **Emplacement :** `/scent-player-native/`
* **Techno :** Python 3.10+, CustomTkinter (UI), Matplotlib (Radar Chart), PySerial (Liaison P6).
* **Travaux à faire :**
    * Créer un `FileWatcher` qui détecte l'ajout de nouveaux fichiers `.scent` dans `/data/processed/`.
    * Développer le composant **Radar Chart** dynamique capable de mapper les 146 descripteurs de Dravnieks ou les 8 catégories simplifiées.
    * Implémenter un moteur de recherche local ultra-léger basé sur les métadonnées (CID, Nom commun).
* **Performance Native :** Architecture multi-thread (GUI vs Serial I/O) pour éviter tout freeze durant la diffusion.
* **Philosophie :** "VLC for Scent". Fonctionnement 100% offline avec mise en cache locale de la bibliothèque.
* **Interface :** Radar Chart dynamique et visualisation Moléculaire.
* **Liaison Output :** Interface Serial/USB prête à piloter le Pilier 06 via protocole de messagerie binaire.
* **Rôle :** C'est le "Lecteur VLC". Il est sur un PC, il fonctionne sans internet, et il permet de visualiser un fichier `.scent` local instantanément avant de l'envoyer vers la cartouche.

---

### Pilier 04 : ScentBox (Hardware Acquisition)

* **Emplacement :** `/hardware/scentbox/`
* **Techno :** C++ (Arduino/PlatformIO), ESP32, I2C (BME280).
* **Travaux à faire :**
    * Écrire le driver de lecture synchrone pour la matrice de capteurs MQ.
    * Implémenter la **Compensation d'Humidité** : ajuster les valeurs brutes des capteurs en fonction des courbes de sensibilité fournies dans les datasheets (via le BME280).
    * **Liaison Wi-Fi / Serial :** Capacité d'envoyer les données en **Binary Stream** direct. Au lieu d'envoyer du texte JSON lourd (qui sature la RAM de l'ESP32), la ScentBox "forge" les octets du fichier `.scent` et les envoie par paquets.
* **Traitement du Signal :** Filtre de Kalman ou moyenne mobile sur ESP32 pour lisser le bruit électronique. 
* **Calibration :** Compensation dynamique des capteurs MQ via les données Temp/Hum du BME280.
* **Protocole "Burn-in" :** Cycle de chauffe automatique de 48h pour stabiliser la membrane des capteurs. 
* **Chambre d'isolement :** Obligatoirement en verre ou métal (neutre).
* **Matrice de capteurs :** MQ-3 (Alcool), MQ-135 (Air), MQ-138 (Bio-Organique), BME280 (Calibrage Temp/Hum).
* **Protocole "Burn-in" :** Cycle de chauffe obligatoire de 48h pour stabiliser la couche d'oxyde d'étain des capteurs.
* **Normalisation :** Toute sortie `ADC` doit être mappée linéairement de $0.0$ à $1.0$ avant transmission.
* **Rôle :** C'est l' "Appareil Photo" de l'odeur. Il transforme la réaction chimique des capteurs MQ en données numériques normalisées.

---

### Pilier 05 : ScentPredictor (IA & Machine Learning)

* **Emplacement :** `/models/`
* **Techno :** PyTorch, PyTorch Geometric (GNN), RDKit.
* **Travaux à faire :**
    * Entraîner un modèle **GNN** (Graph Neural Network) sur le dataset Pyrfume pour prédire les vecteurs Dravnieks à partir des graphes moléculaires.
    * Mettre en place une métrique de validation : la "Perceptual Distance" (distance euclidienne entre le vecteur prédit et le vecteur humain).
    * Exporter le modèle en `.onnx` pour le charger directement dans le SDK Core.
* **Architecture GNN :** Modèle `D-MPNN` pour apprendre la topologie chimique (liaisons atomes).
* **Target Alignment :** Couche de sortie avec activation **Sigmoid** pour rester dans l'invariant $[0, 1]$.
* **Inférence :** Export au format `ONNX` pour une exécution légère sans GPU lourd. 
* **Loss Function :** Utiliser la **BCE (Binary Cross Entropy)** ou la **MSE (Mean Squared Error)** pondérée, car le vecteur d'odeur est souvent "creux" (sparse).
* **Input :** Utiliser le champ `chemical_info.smiles` comme source de vérité.
* **Featurization :** Capacité de basculer entre **Morgan Fingerprints** (similarité) et **Graph Neural Networks** (géométrie 3D). 
* **Output JSON :** Toute prédiction génère un objet avec `header.data_origin = "ai_generated"` et un `labels.confidence` calculé.

---

### Pilier 06 : ScentOutput (La Cartouche de Synthèse)

* **Emplacement :** `/hardware/scentoutput/`
* **Techno :** Arduino Nano/ESP32, Mosfets (pour les pompes), Ventilateur DC.
* **Travaux à faire :**
    * Développer l'interpréteur de commandes Serial (ex: `MIX:0.5,0.2,0.0,0.3`).
    * Coder la boucle de **Purge de Sécurité** : activation du ventilateur pendant 10 secondes après chaque diffusion pour réinitialiser la chambre de mixage.
    * Calibrage physique : Déterminer le volume minimal projeté par impulsion PWM pour assurer la fidélité au fichier `.scent`.
* **Précision PWM :** Contrôle microfluidique des pompes en fonction du vecteur `data` reçu.
* **Algorithme de Linéarité :** Mappage direct (0.5 data = 50% PWM).
* **Sanitization :** Cycle de purge automatique (Fan Max) après chaque diffusion. 
* **Mapping Chimique :** Le firmware possède un dictionnaire index `data` <-> pins micro-pompes.
* **Réactivité :** Le protocole doit assurer un temps de réponse < 200ms pour garantir que l'utilisateur 'sent' l'odeur au moment exact où il clique sur le bouton dans le Player.
* **Safety Lock :** Arrêt si `environment.temperature_c` est critique.
* **Rôle :** La cartouche est l'unité de rendu (Render Unit) du projet.

---

### 2.1 Spécifications du Format `.scent` Binaire

##### Le Format `SCNT` (Standard Binary)
Le fichier `.scent` n'est plus un simple texte, c'est une structure optimisée :

* **Emplacement :** `scentlib/core/binary.py` & `schemas/binary_specs.md`

1.  **En-tête (Header) [16 octets] :**
    * `0-3` : Magic Number `0x53 0x43 0x4E 0x54` ("SCNT").
    * `4-5` : Version du schéma (ex: `0x00 0x01`).
    * `6-7` : Flags (bit 0: `is_compressed`, bit 1: `has_ai_data`, bit 2: `is_debug_enabled`).
    * `8-15` : Timestamp (Uint64).
2.  **Corps (Payload) :**
    * Vecteurs de données encodés en `Float16` pour une lecture directe par le processeur (ALU).
3.  **Metadata (Footer) :** * Signature SHA-256 pour l'intégrité.

---

## 3. Structure de Dossiers Unifiée (Mono-Repo)

```text
ScentLib/
├── scentlib/               # P1: Core, SDK, API
│   ├── core/               # Validation, Mathématiques
│   ├── io/                 # Adaptateurs Hardware & API
│   └── ml/                 # Predictor (Base)
├── scent-explorer/         # P2: Cloud Web App (React)
├── scent-player-native/    # P3: Desktop App (Python)
├── hardware/               
│   ├── scentbox/           # P4: Firmware ESP32 (Input)
│   └── scentoutput/        # P6: Firmware Arduino (Output)
├── models/                 # P5: IA Predictor (Research)
├── schemas/                # scent_schema.json (La Loi)
└── data/                   
    ├── raw/                # CSV Pyrfume
    └── processed/          # Fichiers .scent validés
```

---

## 4. Le Cycle de Vie d'une Donnée Olfactive (Workflow)

La force de ScentLib réside dans la fluidité de la donnée entre chaque module, garantissant qu'aucune information n'est perdue ou corrompue.


#### a. L'Acquisition (P4 ➡️ P1)
* **Action :** La **ScentBox (P4)** **binarise à la source**. Elle n'envoie pas "un dictionnaire", elle envoie un "flux d'octets".
* **Liaison :** Le Core reçoit le binaire, vérifie le **Magic Number**, et valide l'intégrité.

#### b. La Distribution et l'Analyse (P1 ➡️ P2 & P3)
* **Action :** Une fois le fichier créé, il devient disponible sur deux fronts. 
    * Il est synchronisé sur le **Scent Explorer (P2)** (Cloud) pour archivage et collaboration.
    * Il est ouvert instantanément par le **Scent Player (P3)** (Local) pour une visualisation radar et moléculaire immédiate.
* **Liaison :** Le Player local et l'Explorer web utilisent les mêmes algorithmes mathématiques du Core pour interpréter le vecteur `data`.

#### c. L'Intelligence et l'Inférence (P5 ➡️ P1 ➡️ P2/P3)
* **Action :** Le **ScentPredictor (P5)** puise dans la banque de données du Core (notamment les données Pyrfume) pour apprendre. Il peut générer de nouveaux fichiers `.scent` basés sur une simple formule SMILES.
* **Liaison :** Ces fichiers "AI-generated" réintègrent le circuit. Ils sont marqués comme tels dans le `header` et peuvent être comparés aux captures réelles (P4) pour affiner la précision du modèle.

#### d. La Restitution Physique (P3 ➡️ P6)
* **Action :** C'est l'étape finale. L'utilisateur choisit un fichier dans son **Scent Player (P3)** et clique sur "Diffuser".
Le Player ne traduit plus seulement en texte, il envoie un **Binary Command Map** au Pilier 06.
* **Liaison :** Le Player traduit le vecteur numérique en instructions PWM (Pulse Width Modulation). Ces instructions sont envoyées à la **ScentOutput (P6)** qui pilote les micro-pompes pour recréer l'odeur physiquement. L'Arduino (P6) reçoit des octets directs (ex: `0xFF` pour 100% de puissance pompe), ce qui élimine le temps de latence de lecture de texte.

---

## 5. Invariants Techniques (Guardian de liaisaon et transition)

Pour que ces liaisons ne se brisent jamais, trois règles de fer s'appliquent :

1.  **L'Universalité du JSON :** Peu importe si la donnée vient du capteur (P4) ou de l'IA (P5), elle finit toujours par ressembler exactement au même fichier `.scent`.
2.  **L'Agnosticisme du Player :** Le Player (P3) ne sait pas d'où vient l'odeur (humaine, capteur ou IA). Il se contente de lire le champ `data` et de l'afficher. Cela permet de tester des prédictions d'IA avant même qu'elles n'existent.
3.  **La Purge Système (P6) :** La cartouche de sortie est "esclave" du Player. Elle assure la propreté du système pour que la prochaine liaison de données soit pure et non contaminée.
4. **Strict Schema Enforcement :** Toute donnée non-conforme au schéma JSON doit être rejetée avec erreur fatale.
5. **No Ghost Data :** Un vecteur sans `dimension_map` est interdit.
6. **Traçabilité :** Distinction stricte entre `human_perceptual`, `sensor_raw` et `ai_generated`.
7. **P3 ➡️ P6 (Lien critique) :** Le Player doit être capable d'identifier si une cartouche est branchée avant de proposer le bouton "Diffuser".
8. **P1 ➡️ P5 (Lien critique) :** Le SDK Core doit pouvoir charger le modèle IA de manière transparente : `scentlib.predict(smiles="C1=CC=CC=C1")`.

---

## 6. Schéma de Connexion Technique

| Liaison | Type de Flux | Protocole / Interface |
| :--- | :--- | :--- |
| **P4 (Box) → P1 (Core)** | `sensor_raw` (Entrée) | HTTP / JSON via Wi-Fi (ESP32) |
| **P1 (Core) → P2 (Explorer)** | `.scent` (Stockage) | REST API / PostgreSQL |
| **P1 (Core) → P3 (Player)** | `.scent` (Lecture) | Système de fichiers local (Offline) |
| **P5 (IA) ↔ P1 (Core)** | `chemical_info` / `data` | Python SDK (Pydantic models) |
| **P3 (Player) → P6 (Output)** | Instructions de mélange | Serial over USB / PWM |

---

## 7. Stratégique Roadmap (Suivi de Progression)

### Phase 1 : Fondations & Standardisation
- [x] Définition des 6 piliers et de la vision globale.
- [x] Rédaction du `scent_schema.json` officiel (v1.0).
- [x] Implémentation du Validateur Pydantic dans `scentlib.core`.

### Phase 2 : Bootstrapping & Data (Pyrfume)
- [x] Script de conversion `pyrfume_to_scent.py` (Jointure CID/SMILES).
- [x] Mapping sémantique vers l'ontologie Dravnieks (Layer 1-3).
- [ ] Première base de données locale de 10 000+ fichiers `.scent`.

### Phase 3 : Visualisation & Intelligence
- [ ] Développement du **Scent Player** (UI Radar Chart local).
- [ ] Prototype de **Scent Explorer** (Visualiseur web des molécules 3D).
- [ ] Entraînement du premier modèle de prédiction (P5 - ScentPredictor).

### Phase 4 : Hardware & Binarisation
- [ ] **Définition du Codex :** Finaliser le fichier `schemas/binary_specs.md`.
- [ ] **Core Binary :** Développer `json_to_binary` et `binary_to_json` (avec mode `--decompile`).
- [ ] **Firmware Binaire :** Flashage de l'ESP32 pour l'envoi en mode "Byte-Stream".
- [ ] **Validation "Zero-Loss" :** Test de cycle complet (JSON -> Binary -> JSON) avec 0% de différence de valeur.
- [ ] Prototype **ScentBox** (Acquisition de signaux bruts filtrés).
- [ ] Liaison Serial entre le Player et la **ScentOutput** (Cartouche).

---

## 8. Utilisateurs Visés & Workflows

### A. Le Chercheur (Master/PhD)
* **Flow :** Télécharge Pyrfume via `scentlib` -> Entraîne un modèle sur `ScentPredictor` -> Compare les prédictions avec les captures réelles de la `ScentBox`.
* **Besoin :** Précision mathématique et export de données.

### B. Le Créateur (Parfumeur/Designer)
* **Flow :** Utilise le `Scent Explorer` Cloud pour trouver des inspirations -> Utilise le `Scent Player` pour tester des mélanges (`blend`) numériques -> Visualise le résultat en 3D.
* **Besoin :** Interface visuelle intuitive et bibliothèque riche.

### C. L'Utilisateur Lambda
* **Flow :** Pose sa `ScentBox` sur une fleur -> L'app `Scent Player` s'ouvre automatiquement et affiche l'identité de l'odeur -> Partage le fichier `.scent` sur le Cloud.
* **Besoin :** Simplicité (One-click experience).

---

## 9. Vision Finale : "L'Internet des Odeurs"

Le but ultime est de rendre l'odorat aussi digitalisable que le son ou l'image et de faire du format `.scent` le standard universel d'échange olfactif, permettant de numériser, partager et synthétiser n'importe quelle fragrance de manière scientifique et accessible (Low-cost).

1.  **Capture :** `ScentBox` (P4) génère du `sensor_raw`.
2.  **Standardisation :** `ScentLib Core` (P1) transforme en `.scent` validé.
3.  **Analyse :** `Scent Explorer` (P2) et `Player` (P3) affichent la donnée.
4.  **Inférence :** `ScentPredictor` (P5) prédit des variantes `ai_generated`.
5.  **Synthèse :** `ScentOutput` (P6) transforme le numérique en réalité physique.

---

**Note pour plus tard :** Ne jamais oublier que la valeur de ScentLib réside dans sa **rigueur scientifique** (Layer 1-3) alliée à sa **simplicité technique** (JSON/Python).