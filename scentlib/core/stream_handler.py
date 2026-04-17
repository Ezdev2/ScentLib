import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from .analytics import ScentAnalytics


# ---------------------------------------------------------------------------
# Modèles Pydantic pour le format stream
# ---------------------------------------------------------------------------

class StreamFrame(BaseModel):
    """
    Une frame temporelle individuelle dans un stream.
    t      : timestamp relatif en millisecondes depuis le début de la capture
    values : vecteur normalisé [0.0–1.0] pour cette frame
    """
    t: int = Field(..., ge=0, description="Timestamp relatif en ms")
    values: list[float]

    @field_validator("values")
    @classmethod
    def validate_values_range(cls, v: list[float]) -> list[float]:
        """
        Vérifie que toutes les valeurs de la frame sont dans [0.0, 1.0].
        Input  : liste de floats
        Output : liste validée
        Raises : ValueError si hors bornes
        """
        out = [x for x in v if not (0.0 <= x <= 1.0)]
        if out:
            raise ValueError(
                f"Frame values must be in [0.0, 1.0]. Found invalid: {out[:5]}"
            )
        return v


class ScentStream(BaseModel):
    """
    Représentation complète d'un fichier .scent de type 'stream'.
    Valide que :
      - capture_type == 'stream'
      - data est une liste de StreamFrame
      - toutes les frames ont la même dimension
      - les timestamps sont strictement croissants
    """
    schema_version: str
    capture_type: str
    dimension_map: list[str]
    source_dataset: Optional[str] = None
    frames: list[StreamFrame]

    @model_validator(mode="after")
    def validate_stream_consistency(self) -> "ScentStream":
        """
        Vérifie la cohérence interne du stream.
        Input  : ScentStream partiellement construit
        Output : ScentStream validé
        Raises : ValueError si incohérence détectée
        """
        if self.capture_type != "stream":
            raise ValueError(
                f"Expected capture_type='stream', got '{self.capture_type}'."
            )

        if not self.frames:
            raise ValueError("A stream must contain at least one frame.")

        expected_dim = len(self.dimension_map)
        for i, frame in enumerate(self.frames):
            if len(frame.values) != expected_dim:
                raise ValueError(
                    f"Frame {i} has {len(frame.values)} values, "
                    f"expected {expected_dim} (dimension_map length)."
                )

        # Vérifier que les timestamps sont strictement croissants
        timestamps = [f.t for f in self.frames]
        for i in range(1, len(timestamps)):
            if timestamps[i] <= timestamps[i - 1]:
                raise ValueError(
                    f"Timestamps must be strictly increasing. "
                    f"Frame {i}: t={timestamps[i]} <= frame {i-1}: t={timestamps[i-1]}."
                )

        return self


# ---------------------------------------------------------------------------
# StreamHandler
# ---------------------------------------------------------------------------

class StreamHandler:
    """
    Charge, valide et agrège les fichiers .scent de type 'stream'.

    Usage typique :
        handler = StreamHandler("data/processed/cid_1183_stream.scent")
        summary = handler.summarize()
        # summary contient mean, peak, variance, fingerprint
    """

    def __init__(self, file_path: str):
        """
        Charge et valide un fichier .scent stream depuis le disque.
        Input  : chemin vers le fichier .scent
        Output : instance StreamHandler prête à l'emploi
        Raises : FileNotFoundError, ValueError, pydantic.ValidationError
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Stream file not found: {file_path}")

        with open(path, "r") as f:
            raw = json.load(f)

        # Vérification préliminaire du capture_type avant la validation complète
        capture_type = raw.get("header", {}).get("capture_type", "")
        if capture_type != "stream":
            raise ValueError(
                f"'{path.name}' is not a stream file "
                f"(capture_type='{capture_type}'). Use ScentValidator for static files."
            )

        # Construction du modèle ScentStream depuis le dict brut
        header = raw.get("header", {})
        data_raw = raw.get("data", [])

        # Conversion du format .scent → StreamFrame
        # Le champ 'data' d'un stream est une liste de {"t": ms, "values": [...]}
        frames = []
        for item in data_raw:
            if isinstance(item, dict) and "t" in item and "values" in item:
                frames.append(StreamFrame(t=item["t"], values=item["values"]))
            else:
                raise ValueError(
                    f"Invalid frame format. Expected {{'t': int, 'values': [float, ...]}}. "
                    f"Got: {item}"
                )

        self.stream = ScentStream(
            schema_version=raw.get("schema_version", "1.1.0"),
            capture_type=header.get("capture_type", "stream"),
            dimension_map=header.get("dimension_map", []),
            source_dataset=header.get("source_dataset"),
            frames=frames,
        )
        self.file_path = str(path)

    # ------------------------------------------------------------------
    # Extraction de la matrice brute
    # ------------------------------------------------------------------

    def get_matrix(self) -> list[list[float]]:
        """
        Retourne la matrice brute [n_frames × n_dimensions].
        Input  : -
        Output : liste de listes de floats
        """
        return [frame.values for frame in self.stream.frames]

    def get_timestamps(self) -> list[int]:
        """
        Retourne la liste des timestamps en ms.
        Input  : -
        Output : liste d'entiers
        """
        return [frame.t for frame in self.stream.frames]

    # ------------------------------------------------------------------
    # Agrégation via ScentAnalytics
    # ------------------------------------------------------------------

    def summarize(self) -> dict:
        """
        Calcule les statistiques agrégées du stream et retourne un résumé.
        Input  : -
        Output : dict avec les clés :
                   n_frames     : nombre de frames
                   duration_ms  : durée totale en ms
                   mean_vector  : vecteur moyen
                   peak_vector  : vecteur de pics
                   variance_vector : vecteur de variances
                   fingerprint  : hash MD5 du vecteur moyen
                   dimension_map : noms des dimensions
        """
        matrix = self.get_matrix()
        timestamps = self.get_timestamps()

        mean_vec     = ScentAnalytics.stream_mean(matrix)
        peak_vec     = ScentAnalytics.stream_peak(matrix)
        var_vec      = ScentAnalytics.stream_variance(matrix)
        fingerprint  = ScentAnalytics.stream_fingerprint(matrix)
        duration_ms  = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0

        return {
            "n_frames":        len(matrix),
            "duration_ms":     duration_ms,
            "mean_vector":     mean_vec,
            "peak_vector":     peak_vec,
            "variance_vector": var_vec,
            "fingerprint":     fingerprint.upper(),
            "dimension_map":   self.stream.dimension_map,
        }

    def to_static_scent(self, method: str = "mean") -> dict:
        """
        Convertit le stream en un fichier .scent 'static' agrégé.
        Utile pour stocker un résumé compact d'une capture longue.
        Input  : method — 'mean' (défaut) ou 'peak'
        Output : dict conforme à scent_schema.json, prêt pour json.dump
        Raises : ValueError si method est invalide
        """
        matrix = self.get_matrix()

        if method == "mean":
            aggregated = ScentAnalytics.stream_mean(matrix)
        elif method == "peak":
            aggregated = ScentAnalytics.stream_peak(matrix)
        else:
            raise ValueError(f"Unknown aggregation method: '{method}'. Use 'mean' or 'peak'.")

        # On réutilise les métadonnées du stream source
        summary = self.summarize()

        return {
            "schema_version": self.stream.schema_version,
            "header": {
                "capture_type": "static",
                "data_origin": "computed_features",
                "dimension_map": self.stream.dimension_map,
                "timestamp": None,
                "source_dataset": self.stream.source_dataset,
            },
            "labels": {
                "layer1_category": "unclassified",
            },
            "data": aggregated,
            "metadata": {
                "aggregation_method": method,
                "source_stream":      self.file_path,
                "n_frames":           summary["n_frames"],
                "duration_ms":        summary["duration_ms"],
            },
        }