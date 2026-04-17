import uvicorn
import argparse
import copy
import json
import math
from pathlib import Path
import polars as pl
from scentlib.core.validator import ScentValidator
from scentlib.core.analytics import ScentAnalytics


def start_server(port: int = 8000) -> None:
    print(f"Starting ScentLib Driver on http://127.0.0.1:{port}")
    uvicorn.run("scentlib.api.server:app", host="127.0.0.1", port=port, reload=True)


def play_scent(file_path: str) -> None:
    """
    Affiche un Scent Player ASCII dans le terminal.
    Input  : chemin vers un fichier .scent
    Output : affichage console avec barres de progression
    """
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File {file_path} not found.")
        return
    with open(path, "r") as f:
        data = json.load(f)
    try:
        validator = ScentValidator()
        scent = validator.validate_file(data)
        print(f"\nScentLib Player | v{scent.schema_version}")
        print(f"PLAYING: {scent.labels.layer3_descriptor}")
        print("=" * 55)
        for name, val in zip(scent.header.dimension_map, scent.data):
            bar = "█" * int(val * 30) + "░" * (30 - int(val * 30))
            print(f"{name.ljust(15)} |{bar}| {val*100:>3.0f}%")
        print("=" * 55)
    except Exception as e:
        print(f"Error: {e}")


def list_scents(directory_path: str, query: str = None) -> None:
    """
    Liste ou filtre les fichiers .scent d'un répertoire.
    Input  : chemin du dossier, mot-clé optionnel
    Output : tableau Polars affiché dans le terminal
    """
    path = Path(directory_path)
    scent_files = list(path.glob("*.scent"))
    analytics = ScentAnalytics()
    all_data = []

    for f in scent_files:
        with open(f, "r") as file:
            d = json.load(file)
            name = d["labels"].get("layer3_descriptor", "N/A")
            cat = d["labels"].get("layer1_category", "N/A")

            if query and query.lower() not in name.lower() and query.lower() not in cat.lower():
                continue

            fprint = analytics.generate_fingerprint(d.get("data", []))

            all_data.append({
                "File": f.name,
                "Name": name,
                "Fingerprint": fprint.upper(),
                "Category": cat,
                "CID": d.get("chemical_info", {}).get("pubchem_cid", "N/A")
            })

    if not all_data:
        print("No scents found.")
        return

    df = pl.DataFrame(all_data)
    print(f"\nSEARCH RESULTS ({len(df)} found)" if query else f"\nCATALOGUE ({len(df)} found)")
    print(df)


def compare_scents(file1: str, file2: str) -> None:
    """
    Calcule la similarité cosinus entre deux fichiers .scent.
    Input  : chemins vers deux fichiers .scent
    Output : score de similarité + interprétation
    """
    def load_data(p: str) -> dict:
        with open(p, "r") as f:
            return json.load(f)

    s1, s2 = load_data(file1), load_data(file2)
    v1, v2 = s1["data"], s2["data"]

    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a**2 for a in v1))
    magnitude2 = math.sqrt(sum(b**2 for b in v2))

    similarity = dot_product / (magnitude1 * magnitude2) if (magnitude1 * magnitude2) > 0 else 0

    print(f"\n COMPARISON")
    print(f"1. {s1['labels']['layer3_descriptor']}")
    print(f"2. {s2['labels']['layer3_descriptor']}")
    print("-" * 30)
    print(f"Similarity Score : {similarity:.2%}")

    if similarity > 0.9:
        print("Result: These scents are nearly identical!")
    elif similarity > 0.5:
        print("Result: They share common olfactory notes.")
    else:
        print("Result: These are very distinct scents.")


def export_scents(directory_path: str, output_file: str) -> None:
    """
    Compile tous les fichiers .scent en un dataset CSV ou Parquet.
    Input  : dossier source, nom du fichier de sortie
    Output : fichier CSV ou Parquet
    """
    path = Path(directory_path)
    scent_files = list(path.glob("*.scent"))

    if not scent_files:
        print("Nothing to export.")
        return

    rows = []
    for f in scent_files:
        with open(f, "r") as file:
            d = json.load(file)
            row = {
                "name": d["labels"].get("layer3_descriptor"),
                "category": d["labels"].get("layer1_category"),
                "cid": d.get("chemical_info", {}).get("pubchem_cid"),
                "smiles": d.get("chemical_info", {}).get("smiles")
            }
            dim_map = d["header"].get("dimension_map", [])
            values = d.get("data", [])
            for i, dim_name in enumerate(dim_map):
                if i < len(values):
                    row[dim_name.lower()] = values[i]
            rows.append(row)

    df = pl.DataFrame(rows)
    output_path = Path(output_file)
    if output_path.suffix == ".csv":
        df.write_csv(output_path)
    elif output_path.suffix == ".parquet":
        df.write_parquet(output_path)
    else:
        print("Unsupported format. Defaulting to CSV.")
        df.write_csv(output_path.with_suffix(".csv"))

    print(f"Export successful: {len(df)} molecules exported to {output_file}")


def show_fingerprint(file_path: str) -> None:
    """
    Génère et affiche la signature MD5 unique d'un fichier .scent.
    Input  : chemin vers un fichier .scent
    Output : hash affiché dans le terminal
    """
    with open(file_path, "r") as f:
        d = json.load(f)

    data = d.get("data", [])
    name = d["labels"].get("layer3_descriptor", "Unknown")

    analytics = ScentAnalytics()
    fprint = analytics.generate_fingerprint(data)

    print(f"\nScent Fingerprint")
    print(f"Molecule : {name}")
    print(f"Signature: {fprint.upper()}")
    print(f"Status   : Unique identifier generated based on {len(data)} dimensions.")


def match_scent(file_path: str, directory: str, top_n: int) -> None:
    """
    Trouve les molécules les plus proches dans la bibliothèque.
    Input  : fichier cible, dossier de la bibliothèque, nombre de résultats
    Output : tableau Polars des top N matches
    """
    with open(file_path, "r") as f:
        target_scent = json.load(f)

    analytics = ScentAnalytics()
    matches = analytics.find_matches(target_scent["data"], directory, top_n)

    print(f"\nTOP {top_n} SCENT MATCHES")
    print(f"Target: {target_scent['labels']['layer3_descriptor']}")
    print("-" * 60)
    df = pl.DataFrame(matches)
    print(df)
    print("-" * 60)


def blend_scents(file1: str, file2: str, ratio: float, output: str = None) -> None:
    """
    Mélange deux profils olfactifs selon un ratio pondéré.
    Input  : deux fichiers .scent, ratio (0.0–1.0), chemin de sauvegarde optionnel
    Output : visualisation du mélange + fichier .scent si --save fourni
    """
    # Validation du ratio avant tout traitement
    if not (0.0 <= ratio <= 1.0):
        print(f"Error: ratio must be between 0.0 and 1.0 (got {ratio}).")
        return

    def load_s(p: str) -> dict:
        with open(p, "r") as f:
            return json.load(f)

    s1, s2 = load_s(file1), load_s(file2)

    # Vérification de compatibilité des dimensions
    if len(s1["data"]) != len(s2["data"]):
        print(
            f"Warning: dimension mismatch — "
            f"{file1} has {len(s1['data'])} dims, "
            f"{file2} has {len(s2['data'])} dims. "
            f"Blend will use the shorter vector length."
        )

    analytics = ScentAnalytics()
    blended_data = analytics.blend_vectors(s1["data"], s2["data"], ratio)

    name1 = s1["labels"]["layer3_descriptor"]
    name2 = s2["labels"]["layer3_descriptor"]

    print(f"\nBLENDING RESULTS ({int(ratio*100)}% {name1} / {int((1-ratio)*100)}% {name2})")
    print("-" * 55)
    for name, val in zip(s1["header"]["dimension_map"], blended_data):
        bar = "█" * int(val * 30) + "░" * (30 - int(val * 30))
        print(f"{name.ljust(15)} |{bar}| {val*100:>3.0f}%")
    print("-" * 55)

    if output:
        # BUG FIX: deepcopy pour éviter de muter s1["labels"] en mémoire
        new_scent = copy.deepcopy(s1)
        new_scent["labels"]["layer3_descriptor"] = f"Blend: {name1}+{name2}"
        new_scent["labels"]["layer1_category"] = "unclassified"  # mélange = catégorie indéfinie
        new_scent["data"] = blended_data
        new_scent["metadata"] = {
            **new_scent.get("metadata", {}),
            "blend_source_1": file1,
            "blend_source_2": file2,
            "blend_ratio": ratio,
        }
        with open(output, "w") as f:
            json.dump(new_scent, f, indent=2)
        print(f"Saved as: {output}")


def main():
    parser = argparse.ArgumentParser(description="ScentLib CLI")
    subparsers = parser.add_subparsers(dest="command")

    s_p = subparsers.add_parser("serve", help="Start the ScentLib API Server (Driver)")
    s_p.add_argument("--port", type=int, default=8000)

    p_p = subparsers.add_parser("play", help="Visualize a scent profile in the terminal")
    p_p.add_argument("file")

    l_p = subparsers.add_parser("list", help="List or search scents in a directory")
    l_p.add_argument("dir", nargs="?", default="data/processed")
    l_p.add_argument("--query", "-q", help="Search keyword")

    c_p = subparsers.add_parser("compare", help="Compute cosine similarity between two scents")
    c_p.add_argument("file1")
    c_p.add_argument("file2")

    export_parser = subparsers.add_parser("export", help="Export all scents to CSV or Parquet")
    export_parser.add_argument("output", help="Output filename (e.g. dataset.csv)")
    export_parser.add_argument("--dir", default="data/processed", help="Source directory")

    fp_parser = subparsers.add_parser("fingerprint", help="Generate a unique hash for a scent")
    fp_parser.add_argument("file")

    match_parser = subparsers.add_parser("match", help="Find similar scents in the library")
    match_parser.add_argument("file", help="The scent file to match")
    match_parser.add_argument("--dir", default="data/processed", help="Library directory")
    match_parser.add_argument("--top", type=int, default=5, help="Number of results")

    b_p = subparsers.add_parser("blend", help="Mix two scents together")
    b_p.add_argument("file1")
    b_p.add_argument("file2")
    b_p.add_argument("--ratio", type=float, default=0.5)
    b_p.add_argument("--save", help="Save the result to a new file")

    args = parser.parse_args()

    if args.command == "play": play_scent(args.file)
    elif args.command == "list": list_scents(args.dir, args.query)
    elif args.command == "compare": compare_scents(args.file1, args.file2)
    elif args.command == "export": export_scents(args.dir, args.output)
    elif args.command == "fingerprint": show_fingerprint(args.file)
    elif args.command == "match": match_scent(args.file, args.dir, args.top)
    elif args.command == "blend": blend_scents(args.file1, args.file2, args.ratio, args.save)
    elif args.command == "serve": start_server(args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()