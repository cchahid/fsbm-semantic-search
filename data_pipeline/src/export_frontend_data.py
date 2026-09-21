"""Export researcher metrics and publication summaries for the Next.js frontend."""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PARQUET_PATH = ROOT / "data_pipeline" / "data" / "processed" / "fsbm_researchers_clean.parquet"
RAW_PATH = ROOT / "data_pipeline" / "data" / "raw" / "fsbm_researchers_raw.json"
OUTPUT_PATH = ROOT / "frontend" / "data" / "faculty_metrics.json"


def number_or_zero(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def main() -> None:
    dataframe = pd.read_parquet(PARQUET_PATH)
    required_columns = {"chercheur_id", "nom_complet", "Laboratoire"}
    missing_columns = required_columns - set(dataframe.columns)
    if missing_columns:
        raise ValueError(f"Missing required Parquet columns: {sorted(missing_columns)}")

    raw_profiles = {
        profile.get("chercheur_id"): profile
        for profile in json.loads(RAW_PATH.read_text(encoding="utf-8"))
        if profile.get("chercheur_id")
    }

    exported_profiles = []
    for researcher_id, group in dataframe.groupby("chercheur_id", sort=False):
        first_row = group.iloc[0]
        raw_profile = raw_profiles.get(researcher_id, {})
        scraped_metrics = raw_profile.get("metriques", {})
        publications = group.sort_values(
            "date_publication", ascending=False, na_position="last"
        )

        top_papers = [
            {
                "article_id": str(row.get("article_id", "")),
                "title": str(row.get("titre", "Untitled")),
                "year": str(row.get("date_publication", "N/A")),
            }
            for _, row in publications.head(5).iterrows()
        ]

        exported_profiles.append(
            {
                "chercheur_id": str(researcher_id),
                "nom_complet": str(first_row["nom_complet"]),
                "affiliation": raw_profile.get("affiliation", "Universite Hassan II de Casablanca"),
                "laboratoire": str(first_row.get("Laboratoire", "Unknown") or "Unknown"),
                "h_index": number_or_zero(scraped_metrics.get("h_index")),
                "i10_index": number_or_zero(scraped_metrics.get("i10_index")),
                "citations_total": number_or_zero(scraped_metrics.get("citations_totales")),
                "publications_count": int(len(group)),
                "top_papers": top_papers,
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(exported_profiles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Exported {len(exported_profiles)} faculty profiles to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
