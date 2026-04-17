import json
import os
import jsonschema
from pathlib import Path
from .models import ScentFile


def _resolve_schemas_dir() -> Path:
    env_path = os.environ.get("SCENTLIB_SCHEMAS_DIR")
    if env_path:
        p = Path(env_path)
        if p.is_dir():
            return p
        raise FileNotFoundError(
            f"SCENTLIB_SCHEMAS_DIR is set to '{env_path}' but this directory does not exist."
        )

    # validator.py est dans scentlib/core/ → remonter 2 niveaux = racine du projet
    repo_root = Path(__file__).resolve().parent.parent.parent
    candidate = repo_root / "schemas"
    if candidate.is_dir():
        return candidate

    cwd_candidate = Path.cwd() / "schemas"
    if cwd_candidate.is_dir():
        return cwd_candidate

    raise FileNotFoundError(
        "Cannot locate 'schemas/' directory. "
        "Set the SCENTLIB_SCHEMAS_DIR environment variable to its absolute path, "
        "or run the project from its repository root."
    )


class ScentValidator:
    """
    Validateur en 3 passes pour les fichiers .scent :
      1. Validation structurelle (JSON Schema)
      2. Validation sémantique (taxonomie categories_v1.json)
      3. Mapping objet (Pydantic — types, plages de valeurs, cohérence dimensions)
    """

    def __init__(self, schemas_dir: Path = None):
        """
        Initialise le validateur en chargeant les schémas depuis le disque.
        Input  : schemas_dir (optionnel) — chemin explicite vers le dossier schemas/
                 Si None, _resolve_schemas_dir() est utilisé automatiquement.
        Output : instance prête à valider
        Raises : FileNotFoundError si les fichiers de schéma sont introuvables
        """
        base = schemas_dir if schemas_dir is not None else _resolve_schemas_dir()

        schema_path = base / "scent_schema.json"
        cat_path    = base / "categories_v1.json"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        if not cat_path.exists():
            raise FileNotFoundError(f"Categories file not found: {cat_path}")

        with open(schema_path, "r") as f:
            self.schema = json.load(f)

        with open(cat_path, "r") as f:
            cat_data = json.load(f)
            self.allowed_ids: list[str] = [c["id"] for c in cat_data["categories"]]

    def validate_file(self, data: dict) -> ScentFile:
        jsonschema.validate(instance=data, schema=self.schema)

        cat_id = data["labels"]["layer1_category"]
        if cat_id not in self.allowed_ids:
            raise ValueError(
                f"Invalid category ID: '{cat_id}'. "
                f"Must be one of: {self.allowed_ids}"
            )

        return ScentFile(**data)


# ---------------------------------------------------------------------------
# Quick test (python -m scentlib.core.validator ou python validator.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    v = ScentValidator()
    print(f"Validator ready. {len(v.allowed_ids)} valid categories loaded: {v.allowed_ids}")