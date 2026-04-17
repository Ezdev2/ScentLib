import numpy as np
import hashlib
import json
from pathlib import Path
from typing import Optional


class ScentAnalytics:
    """
    Moteur de calcul analytique pour les profils olfactifs (.scent).

    Métriques disponibles :
      - generate_fingerprint   : signature MD5 tronquée d'un vecteur
      - calculate_distance     : distance euclidienne (utilisée par find_matches / match CLI)
      - calculate_similarity   : similarité cosinus (utilisée par compare CLI)
      - find_matches           : recherche top-N par distance euclidienne
      - blend_vectors          : moyenne pondérée de deux vecteurs

      La commande `compare` utilise la similarité COSINUS (insensible à l'amplitude,
      mesure l'angle entre deux profils → pertinent pour comparer des "formes" d'odeurs).
      La commande `match` utilise la distance EUCLIDIENNE (sensible à l'amplitude,
      mesure la proximité absolue → pertinent pour trouver des molécules proches dans
      un espace perceptuel homogène comme Dravnieks normalisé).
      Ce choix est intentionnel et documenté ici.
    """

    # ------------------------------------------------------------------
    # Fingerprint
    # ------------------------------------------------------------------

    @staticmethod
    def generate_fingerprint(data: list, precision: int = 2) -> str:
        """
        Génère une signature unique (Hash MD5 tronqué) basée sur le profil.
        Utile pour l'indexation et la détection de doublons.
        Input  : vecteur de données (liste de floats), précision d'arrondi
        Output : chaîne hexadécimale de 10 caractères (ex: 'A1B2C3D4E5')
        """
        # Arrondi pour absorber les micro-variations de capteurs
        normalized = [round(float(x), precision) for x in data]
        data_string = "|".join(map(str, normalized))
        return hashlib.md5(data_string.encode()).hexdigest()[:10]

    # ------------------------------------------------------------------
    # Métriques de distance / similarité
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_distance(v1: list, v2: list) -> float:
        """
        Calcule la distance Euclidienne entre deux vecteurs.
        Plus la valeur est proche de 0, plus les profils sont similaires.
        Utilisée par : find_matches (commande `match`)
        Input  : deux listes de floats de même longueur
        Output : float ≥ 0
        """
        a = np.array(v1, dtype=float)
        b = np.array(v2, dtype=float)
        # Alignement sur la longueur minimale si les vecteurs diffèrent
        min_len = min(len(a), len(b))
        return float(np.linalg.norm(a[:min_len] - b[:min_len]))

    @staticmethod
    def calculate_similarity(v1: list, v2: list) -> float:
        """
        Calcule la similarité cosinus entre deux vecteurs.
        Résultat entre 0.0 (orthogonaux) et 1.0 (identiques en forme).
        Insensible à l'amplitude — mesure uniquement l'angle entre profils.
        Utilisée par : compare_scents (commande `compare`)
        Input  : deux listes de floats de même longueur
        Output : float dans [0.0, 1.0]
        """
        a = np.array(v1, dtype=float)
        b = np.array(v2, dtype=float)
        min_len = min(len(a), len(b))
        a, b = a[:min_len], b[:min_len]

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    # ------------------------------------------------------------------
    # Recherche par proximité
    # ------------------------------------------------------------------

    def find_matches(
        self,
        target_data: list,
        library_path: str,
        top_n: int = 5,
        exclude_zero: bool = True,
    ) -> list[dict]:
        """
        Cherche les profils les plus proches dans la bibliothèque.
        Algorithme : distance euclidienne (voir note de cohérence en en-tête).
        Input  : vecteur cible, chemin du dossier bibliothèque,
                 nombre de résultats, exclure distance 0 (doublon exact)
        Output : liste de dicts triée par distance croissante
        """
        path = Path(library_path)
        results = []

        for f in path.glob("*.scent"):
            with open(f, "r") as file:
                d = json.load(file)
                library_data = d.get("data", [])
                dist = self.calculate_distance(target_data, library_data)

                # Exclure la molécule cible elle-même (distance 0 = doublon exact)
                if exclude_zero and dist == 0.0:
                    continue

                results.append({
                    "Name":     d["labels"].get("layer3_descriptor", "Unknown"),
                    "Category": d["labels"].get("layer1_category", "N/A"),
                    "Distance": round(dist, 4),
                    "File":     f.name,
                })

        return sorted(results, key=lambda x: x["Distance"])[:top_n]

    # ------------------------------------------------------------------
    # Mélange
    # ------------------------------------------------------------------

    @staticmethod
    def blend_vectors(v1: list, v2: list, ratio: float = 0.5) -> list:
        """
        Combine deux vecteurs selon un ratio pondéré.
        Formule : (V1 × ratio) + (V2 × (1 − ratio))
        Si les vecteurs ont des longueurs différentes, on travaille
        sur la longueur minimale (comportement documenté et cohérent
        avec calculate_distance).
        Input  : v1, v2 (listes de floats), ratio ∈ [0.0, 1.0]
        Output : liste de floats normalisée dans [0.0, 1.0]
        """
        a = np.array(v1, dtype=float)
        b = np.array(v2, dtype=float)
        min_len = min(len(a), len(b))
        blended = (a[:min_len] * ratio) + (b[:min_len] * (1 - ratio))
        # Clamp de sécurité — les entrées sont dans [0,1] donc le résultat
        # l'est aussi, mais on garantit les bornes explicitement
        return np.clip(blended, 0.0, 1.0).tolist()

    # ------------------------------------------------------------------
    # Analyse de stream (données temporelles)
    # ------------------------------------------------------------------

    @staticmethod
    def stream_mean(frames: list[list]) -> list:
        """
        Calcule le vecteur moyen sur une série de frames temporelles.
        Utile pour réduire un stream .scent en un profil 'static' résumé.
        Input  : liste de vecteurs (frames), ex: [[0.1, 0.2], [0.3, 0.4]]
        Output : vecteur moyen (liste de floats)
        """
        if not frames:
            return []
        matrix = np.array(frames, dtype=float)
        return matrix.mean(axis=0).tolist()

    @staticmethod
    def stream_peak(frames: list[list]) -> list:
        """
        Extrait le vecteur de pic (valeur maximale par dimension) d'un stream.
        Utile pour capturer l'intensité maximale atteinte sur toute la capture.
        Input  : liste de vecteurs (frames)
        Output : vecteur de pics (liste de floats)
        """
        if not frames:
            return []
        matrix = np.array(frames, dtype=float)
        return matrix.max(axis=0).tolist()

    @staticmethod
    def stream_variance(frames: list[list]) -> list:
        """
        Calcule la variance par dimension sur un stream.
        Une variance élevée = odeur instable / évolution temporelle marquée.
        Utile pour détecter les odeurs transitoires vs persistantes.
        Input  : liste de vecteurs (frames)
        Output : vecteur de variances (liste de floats)
        """
        if not frames:
            return []
        matrix = np.array(frames, dtype=float)
        return matrix.var(axis=0).tolist()

    @staticmethod
    def stream_fingerprint(frames: list[list], precision: int = 2) -> str:
        """
        Génère un fingerprint représentatif d'un stream entier,
        basé sur son vecteur moyen.
        Input  : liste de vecteurs (frames), précision d'arrondi
        Output : chaîne hexadécimale de 10 caractères
        """
        if not frames:
            return hashlib.md5(b"").hexdigest()[:10]
        mean_vec = ScentAnalytics.stream_mean(frames)
        return ScentAnalytics.generate_fingerprint(mean_vec, precision)