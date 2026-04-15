#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pandas", "pyarrow", "orjson"]
# ///
"""
Generate analysis/scores.csv with per-student per-question overall scores.

Columns: email, time (ISO), q-generate-affective-chart,
         q-generate-concept-incarnation, q-generate-paradox-portrait,
         q-generate-style-transplant, total (= 0.75 × sum of 4 scores)

All students who have a latest positive submission are included.
Students with no evaluation result get score 0 for that question.
"""

import orjson
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent

QUESTIONS = [
    "q-generate-affective-chart",
    "q-generate-concept-incarnation",
    "q-generate-paradox-portrait",
    "q-generate-style-transplant",
]


def main():
    # Latest positive submission per student (has email, time, submission_id)
    lp = pd.read_parquet(ROOT / "data/derived/latest_positive.parquet")
    # Use the actual submission time (ms epoch → ISO)
    lp["time_iso"] = pd.to_datetime(lp["time"], unit="ms", utc=True).dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # Load gallery summary which has per-question evaluation results
    summary = orjson.loads((ROOT / "gallery/summary.json").read_bytes())
    results = summary["results"]

    # Build lookup: submission_id → {question: overall_score}
    scores_by_id: dict[int, dict[str, float]] = {}
    for row in results:
        sid = row["id"]
        q = row["question"]
        overall = (row.get("response") or {}).get("overall_score", 0.0) or 0.0
        scores_by_id.setdefault(sid, {})[q] = overall

    # Build output rows
    rows = []
    for _, student in lp.iterrows():
        sid = student["submission_id"]
        q_scores = scores_by_id.get(sid, {})
        row = {
            "email": student["email"],
            "time": student["time_iso"],
        }
        for q in QUESTIONS:
            row[q] = q_scores.get(q, 0.0)
        # Each question contributes max 0.75 to the total (scores are 0–10)
        row["total"] = round(0.075 * sum(row[q] for q in QUESTIONS), 4)
        rows.append(row)

    df = pd.DataFrame(rows).sort_values("email").reset_index(drop=True)

    out = ROOT / "analysis/scores.csv"
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows to {out}")
    print(df[["email", "total"] + QUESTIONS].describe().round(3).to_string())


if __name__ == "__main__":
    main()
