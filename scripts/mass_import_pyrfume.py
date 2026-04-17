import polars as pl
import json
from datetime import datetime
from pathlib import Path
from scentlib.core.validator import ScentValidator

# Configuration
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def mass_import():
    validator = ScentValidator()
    
    # Simulation de 50 molécules pour le test
    data_rows = []
    for i in range(1, 51):
        data_rows.append({
            "CID": 1000 + i,
            "name": f"Molecule_{i}",
            "smiles": "C" * (i % 10 + 1), # SMILES fictif
            "category": "green_herbal" if i % 2 == 0 else "fruity_citrus",
            "intensity": 0.5 + (i / 100),
            "sweetness": 0.1 + (i / 200),
            "spiciness": 0.05
        })
    
    df = pl.DataFrame(data_rows)
    
    # Définition de map de dimensions
    dim_map = ["Intensity", "Sweetness", "Spiciness"]

    print(f"Mass Import started: {len(df)} molecules to process...")

    success_count = 0
    for row in df.to_dicts():
        try:
            scent_data = {
                "schema_version": "1.0.0",
                "header": {
                    "capture_type": "static",
                    "data_origin": "human_perceptual",
                    "dimension_map": dim_map,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                "chemical_info": {
                    "pubchem_cid": row["CID"],
                    "smiles": row["smiles"]
                },
                "labels": {
                    "layer1_category": row["category"],
                    "layer3_descriptor": row["name"]
                },
                "data": [row["intensity"], row["sweetness"], row["spiciness"]]
            }

            # Validation automatique
            validator.validate_file(scent_data)

            # Sauvegarde individuelle
            file_name = f"cid_{row['CID']}.scent"
            with open(OUTPUT_DIR / file_name, "w") as f:
                json.dump(scent_data, f, indent=2)
            
            success_count += 1

        except Exception as e:
            print(f"Skipped {row['name']}: {e}")

    print(f"\n Done! {success_count} files generated in {OUTPUT_DIR}")

if __name__ == "__main__":
    mass_import()