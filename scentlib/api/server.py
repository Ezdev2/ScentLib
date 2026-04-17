from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from scentlib.core.analytics import ScentAnalytics

app = FastAPI(title="ScentLib API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("data/processed")

# Palette de couleurs alignée sur les IDs de categories_v1.json (v1.1.0)
CATEGORY_COLORS: dict[str, dict] = {
    "floral":              {"hex": "#f48fb1", "label": "Soft Pink"},
    "fruity":              {"hex": "#ffb74d", "label": "Fruity Orange"},
    "citrus":              {"hex": "#ffee58", "label": "Citrus Yellow"},
    "woody_earthy":        {"hex": "#8d6e63", "label": "Warm Brown"},
    "spicy_warm":          {"hex": "#e64a19", "label": "Deep Amber"},
    "minty_fresh":         {"hex": "#66bb6a", "label": "Mint Green"},
    "animalic":            {"hex": "#795548", "label": "Dark Leather"},
    "chemical_industrial": {"hex": "#90a4ae", "label": "Steel Blue"},
    "savory_food":         {"hex": "#fdd835", "label": "Golden Yellow"},
    "putrid_decay":        {"hex": "#558b2f", "label": "Moss Green"},
    "medicinal":           {"hex": "#4fc3f7", "label": "Clinical Blue"},
    "unclassified":        {"hex": "#bdbdbd", "label": "Neutral Grey"},
}


def _load_scent(scent_id: str) -> dict:
    """
    Charge et retourne le contenu brut d'un fichier .scent.
    Input  : identifiant de la molécule (ex: cid_1183)
    Output : dict Python issu du JSON
    Raises : HTTPException 404 si le fichier n'existe pas
    """
    file_path = DATA_DIR / f"{scent_id}.scent"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Scent '{scent_id}' not found")
    with open(file_path, "r") as f:
        return json.load(f)


@app.get("/")
def read_root():
    return {"status": "ScentLib Driver Online", "version": "1.0.0"}


@app.get("/scents")
def list_all_scents():
    """
    Liste tous les identifiants disponibles dans la bibliothèque.
    Output : {"count": N, "scents": ["cid_1183", ...]}
    """
    files = [f.stem for f in DATA_DIR.glob("*.scent")]
    return {"count": len(files), "scents": sorted(files)}


@app.get("/scents/{scent_id}")
def get_scent_details(scent_id: str):
    """
    Récupère les données complètes d'une odeur + son fingerprint.
    Output : objet .scent enrichi avec le champ 'fingerprint'
    """
    data = _load_scent(scent_id)
    response = {**data, "fingerprint": ScentAnalytics.generate_fingerprint(data["data"])}
    return response


@app.get("/scents/{scent_id}/color")
def get_scent_color(scent_id: str):
    """
    Retourne la signature chromatique basée sur la catégorie olfactive.
    Mapping réel par catégorie — aligné sur categories_v1.json.
    Output : {"category": "floral", "hex": "#f48fb1", "label": "Soft Pink"}
    """
    data = _load_scent(scent_id)
    category = data.get("labels", {}).get("layer1_category", "unclassified")
    color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["unclassified"])
    return {"category": category, **color}


@app.get("/categories")
def list_categories():
    """
    Retourne la palette complète catégorie → couleur.
    Utile pour construire des légendes côté frontend.
    Output : {"floral": {"hex": "...", "label": "..."}, ...}
    """
    return CATEGORY_COLORS