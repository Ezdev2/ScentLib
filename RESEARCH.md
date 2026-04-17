# Protocole de Recherche : ScentLib-V (Validation)

**Titre :** *Évaluation de la fidélité de reconstruction olfactive par synthèse chimique dirigée par Intelligence Artificielle.*

---

## 1. Problématique de Recherche
Comment garantir qu'une odeur prédite par un modèle de graphes moléculaires (**P5**) et diffusée par une cartouche microfluidique (**P6**) est perçue de manière identique à l'odeur réelle capturée par un nez électronique (**P4**) ?

---

## 2. Méthodologie Expérimentale (Triple Validation)

### A. Validation Chimique (Métrologie)
* **Objectif :** Vérifier que la ScentBox (P4) est stable.
* **Procédure :** Soumettre la **ScentBox** à 3 concentrations différentes d'une molécule pure (ex: *Limonène*).
* **Métrique :** Calcul de l'écart-type des vecteurs `sensor_raw` sur 50 captures. On cherche une répétabilité de **95%**.

### B. Validation Algorithmique (IA vs Humain)
* **Objectif :** Mesurer la précision de prédiction du ScentPredictor (P5).
* **Procédure :** Utiliser un "Test Set" de molécules issues de Pyrfume que l'IA n'a jamais vues.
* **Métrique :** Calcul de la **Distance Cosinus** et de l'**Erreur Quadratique Moyenne (MSE)** entre le vecteur prédit par le GNN et le vecteur perceptuel humain.


### C. Validation Sensorielle (Double-Aveugle)
* **Objectif :** Valider le rendu de la ScentOutput (P6).
* **Procédure :** 1. Présenter à un panel de testeurs une odeur réelle (A).
    2. Présenter la reconstruction synthétique de ScentLib (B).
    3. Demander aux testeurs d'évaluer la similitude sur une échelle de 1 à 10 et d'identifier les descripteurs via le **Scent Player**.


---

## 3. Plan de Collecte de Données (Chronologie)

| Phase | Activité | Outil | Résultat attendu |
| :--- | :--- | :--- | :--- |
| **01** | **Calibration** | ScentBox (P4) | Courbe de réponse sensorielle stable. |
| **02** | **Simulation** | Predictor (P5) | Génération d'un catalogue de 100 odeurs virtuelles. |
| **03** | **Synthèse** | ScentOutput (P6) | Mélange physique des solutions mères. |
| **04** | **Corrélation** | Core (P1) | Matrice de confusion entre Capture vs Prédiction. |

---

## 4. Axes de Publication Possibles
1.  **"Standardisation du format .scent"** : Un nouvel enjeu pour l'interopérabilité des données olfactives numériques.
2.  **"Approche GNN pour la synthèse soustractive"** : Comment l'IA peut optimiser les mélanges chimiques en temps réel.
3.  **"Low-cost E-Nose in Tropical Environments"** : Étude de l'impact de l'humidité (Madagascar) sur la précision des capteurs MQ.

---

## 5. Matériel de Laboratoire requis
* **Échantillons :** Kit de 10 molécules primaires (Limonène, Vanilline, Acétate d'éthyle, etc.).
* **Contrôle :** Un capteur de référence (type PID - Photoionization Detector) pour étalonner la ScentBox.
* **Logiciel :** Le **ScentLib Core** configuré en mode "Logging" pour enregistrer chaque milliseconde de données.

---
