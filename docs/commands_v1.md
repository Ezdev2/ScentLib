# ScentLib CLI - Manuel des Commandes (v1.0)

Bienvenue dans la documentation technique des commandes de ScentLib. Ce SDK permet de manipuler, visualiser et analyser des profils olfactifs numériques au format `.scent`.

## Commandes de base

### 1. `list` - Exploration du catalogue
Affiche la liste des molécules disponibles dans un répertoire.
* **Usage :** `scentlib list [PATH] [--query QUERY]`
* **Arguments :**
    * `PATH` (optionnel) : Chemin vers le dossier de données (défaut: `data/processed`).
    * `-q`, `--query` : Mot-clé pour filtrer par nom de molécule ou catégorie.
* **Exemple :** `scentlib list -q "citrus"`

### 2. `play` - Visualisation d'un profil
Affiche un "Scent Player" graphique dans le terminal pour un fichier unique.
* **Usage :** `scentlib play [FILE_PATH]`
* **Exemple :** `scentlib play data/processed/cid_1183.scent`

---

## Analyse Avancée

### 3. `compare` - Similarité mathématique
Calcule le score de proximité entre deux odeurs en utilisant la similarité cosinus sur les vecteurs de données.
* **Usage :** `scentlib compare [FILE_1] [FILE_2]`
* **Interprétation :**
    * **> 90%** : Quasi-identique.
    * **50% - 90%** : Notes communes majeures.
    * **< 50%** : Profils distincts.
* **Exemple :** `scentlib compare cid_1183.scent cid_10430.scent`

### 4. 'export' - Exporter les données en csv
Compile la bibliothèque en un dataset unique (CSV/Parquet).
* **Usage :** `scentlib export [FILENAME]`
* **Exemple :** `scentlib export library_research.csv`

### 5. `fingerprint` - Signature Numérique Unique
Génère une empreinte MD5 tronquée basée sur le vecteur de données olfactives.
* **Usage :** `scentlib fingerprint [FILE_PATH]`
* **Utilité technique :**
    * **Détection de doublons :** Permet de vérifier si deux fichiers avec des noms différents décrivent la même intensité olfactive.
    * **Intégrité :** Sert de "checksum" pour vérifier qu'un fichier n'a pas été altéré.
    * **Indexation :** Les signatures (ex: `A1B2C3`) sont plus rapides à comparer en base de données que des listes de nombres flottants.
* **Exemple :** `scentlib fingerprint data/processed/cid_1183.scent`

### 6. `match` - Recherche par proximité
Analyse toute la bibliothèque pour trouver les profils les plus similaires à un fichier source.
* **Usage :** `scentlib match [FILE_PATH] [--top N]`
* **Algorithme :** Utilise la distance Euclidienne sur les vecteurs d'intensité. Plus la distance est proche de 0, plus la ressemblance est forte.
* **Exemple :** `scentlib match data/processed/cid_1183.scent --top 3`

### 7. `blend` - Simulation de mélange olfactif
Permet de combiner mathématiquement deux profils `.scent` pour prédire le résultat d'un mélange physique.
* **Usage :** `scentlib blend [FILE_1] [FILE_2] [--ratio R] [--save PATH]`
* **Arguments :**
    * `ratio` : Valeur entre `0.0` et `1.0`. Définit l'influence du premier fichier (ex: `0.7` = 70% de l'odeur 1).
    * `--save` : Chemin optionnel pour enregistrer le mélange en tant que nouveau fichier `.scent`.
* **Algorithme :** Calcule une moyenne pondérée vectorielle. Le nouveau fichier généré possède ses propres métadonnées et peut être analysé ou "joué" ultérieurement.
* **Exemple :** `scentlib blend vanille.scent menthe.scent --ratio 0.8 --save vanille_menthe.scent`

---

## Maintenance & Data
* **Mass Import :** Utilisez `python scripts/mass_import_pyrfume.py` pour peupler votre bibliothèque à partir de jeux de données scientifiques (Pyrfume/Dravnieks).