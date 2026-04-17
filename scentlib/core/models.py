from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class Header(BaseModel):
    """
    En-tête d'un fichier .scent.
    capture_type  : 'static' (snapshot) ou 'stream' (série temporelle)
    data_origin   : source du vecteur de données
    dimension_map : noms des dimensions — optionnel si feature_set_ref est fourni
    feature_set_ref : URI d'un feature set externe (ex: Mordred 1826 features)
    timestamp     : date/heure ISO 8601 de la capture
    """
    capture_type: str
    data_origin: str
    dimension_map: Optional[List[str]] = None
    feature_set_ref: Optional[str] = None
    timestamp: datetime
    environment: Optional[Dict[str, float]] = None
    source_dataset: Optional[str] = None

    @model_validator(mode="after")
    def check_dimension_ref_exclusive(self) -> "Header":
        """
        Règle du schéma : dimension_map OU feature_set_ref doit être fourni,
        mais pas nécessairement les deux. L'absence des deux est une erreur.
        """
        if self.dimension_map is None and self.feature_set_ref is None:
            raise ValueError(
                "Header must provide either 'dimension_map' or 'feature_set_ref'."
            )
        return self


class ChemicalInfo(BaseModel):
    """
    Identifiants chimiques reliant un .scent aux bases de données publiques.
    Tous les champs sont optionnels car absents des données capteurs brutes.
    """
    pubchem_cid: Optional[int] = None
    smiles: Optional[str] = None
    inchi_key: Optional[str] = None
    iupac_name: Optional[str] = None
    common_name: Optional[str] = None
    molecular_weight: Optional[float] = None


class Labels(BaseModel):
    """
    Étiquettes sémantiques d'un profil olfactif.
    layer1_category    : famille globale (ex: 'floral') — obligatoire
    layer2_sub_category: sous-famille (ex: 'rose')
    layer3_descriptor  : descripteur précis Dravnieks (ex: 'ROSE')
    intensity          : intensité globale normalisée [0–1]
    confidence         : confiance dans l'attribution de catégorie [0–1]
    """
    layer1_category: str
    layer2_sub_category: Optional[str] = None
    layer3_descriptor: Optional[str] = None
    intensity: Optional[float] = Field(None, ge=0, le=1)
    confidence: Optional[float] = Field(None, ge=0, le=1)


class ScentFile(BaseModel):
    """
    Représentation complète d'un fichier .scent.
    Mappe exactement la structure de scent_schema.json v1.1.0.
    """
    schema_version: str
    header: Header
    chemical_info: Optional[ChemicalInfo] = None
    labels: Labels
    data: List[float]
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("data")
    @classmethod
    def validate_data_range(cls, v: List[float]) -> List[float]:
        """
        Vérifie que toutes les valeurs du vecteur sont dans [0.0, 1.0].
        Input  : liste de floats
        Output : liste validée
        Raises : ValueError si une valeur est hors bornes
        """
        out_of_range = [x for x in v if not (0.0 <= x <= 1.0)]
        if out_of_range:
            raise ValueError(
                f"All data values must be between 0.0 and 1.0. "
                f"Found {len(out_of_range)} invalid value(s): {out_of_range[:5]}{'...' if len(out_of_range) > 5 else ''}"
            )
        return v

    @model_validator(mode="after")
    def validate_dimension_consistency(self) -> "ScentFile":
        """
        Vérifie que la longueur de data correspond à dimension_map quand il est fourni.
        Input  : ScentFile complet
        Output : ScentFile validé
        Raises : ValueError si len(data) != len(dimension_map)
        """
        dim_map = self.header.dimension_map
        if dim_map is not None and len(self.data) != len(dim_map):
            raise ValueError(
                f"'data' length ({len(self.data)}) must match "
                f"'dimension_map' length ({len(dim_map)})."
            )
        return self