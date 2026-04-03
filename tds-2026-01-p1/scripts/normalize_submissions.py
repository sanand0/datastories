#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "orjson>=3.10",
#   "pandas>=2.2",
#   "pyarrow>=20.0",
#   "rich>=14.0",
#   "typer>=0.16",
# ]
# ///

from __future__ import annotations

import re
from typing import Any

import pandas as pd
from rich.traceback import install
import typer

from tds_p1_common import (
    DERIVED_DIR,
    QUESTION_IDS,
    RAW_DIR,
    ensure_dir,
    load_history_rows,
    load_rows_from_payload,
    read_json,
    sha256_text,
    write_json,
)

install(show_locals=True)

app = typer.Typer(add_completion=False)
QUESTION_RE = re.compile(r"(q-[a-z0-9-]+)")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def classify_error(error: str) -> tuple[str, str]:
    text = (error or "").strip()
    lower = text.lower()
    question_match = QUESTION_RE.search(text)
    question_id = question_match.group(1) if question_match else ""
    if not text:
        return "missing-error", question_id
    if "deadline was" in lower:
        return "deadline", question_id
    if "total " in lower and "sum of scores" in lower:
        return "score-mismatch", question_id
    if "invalid signature" in lower or "invalid email" in lower:
        return "auth", question_id
    if "exam opens at" in lower:
        return "exam-not-open", question_id
    if "unknown exam" in lower:
        return "unknown-exam", question_id
    if question_id:
        return "server-validation", question_id
    return "other", question_id


def build_frames(rows: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    submission_rows: list[dict[str, Any]] = []
    attempt_rows: list[dict[str, Any]] = []

    for row in rows:
        result = row.get("result") or {}
        answers = result.get("answers") or {}
        scores = row.get("scores") or {}
        error = normalize_text(result.get("error"))
        error_category, error_question_id = classify_error(error)
        submission_id = int(row["id"])

        submission_rows.append(
            {
                "submission_id": submission_id,
                "email": normalize_text(row.get("email")),
                "quiz": normalize_text(row.get("quiz")),
                "time": int(row.get("time") or 0),
                "total": float(row.get("total")),
                "max_score": float(row.get("max") or 0),
                "is_negative": float(row.get("total")) < 0,
                "result_error": error,
                "error_category": error_category,
                "error_question_id": error_question_id,
            }
        )

        for question_id in QUESTION_IDS:
            answer_text = normalize_text(answers.get(question_id))
            score = float(scores.get(question_id, 0) or 0)
            stripped = answer_text.strip()
            attempt_rows.append(
                {
                    "submission_id": submission_id,
                    "email": normalize_text(row.get("email")),
                    "time": int(row.get("time") or 0),
                    "total": float(row.get("total")),
                    "is_negative": float(row.get("total")) < 0,
                    "result_error": error,
                    "error_category": error_category,
                    "error_question_id": error_question_id,
                    "question_id": question_id,
                    "score": score,
                    "solved": score > 0,
                    "answer_text": answer_text,
                    "answer_chars": len(stripped),
                    "has_answer": bool(stripped),
                    "meaningful_attempt": bool(stripped) or score > 0,
                    "answer_sha256": sha256_text(stripped) if stripped else "",
                }
            )

    submissions = pd.DataFrame.from_records(submission_rows).sort_values(["email", "time", "submission_id"])
    submissions["submitted_at_utc"] = pd.to_datetime(submissions["time"], unit="ms", utc=True)
    submissions["student_submission_index"] = submissions.groupby("email").cumcount() + 1

    attempts = pd.DataFrame.from_records(attempt_rows).sort_values(
        ["email", "question_id", "time", "submission_id"]
    )
    attempts["submitted_at_utc"] = pd.to_datetime(attempts["time"], unit="ms", utc=True)
    attempts["question_attempt_index"] = attempts.groupby(["email", "question_id"]).cumcount() + 1
    return submissions, attempts


def flatten_local_dump() -> pd.DataFrame:
    local_dump_path = RAW_DIR / "local-dump.json"
    if not local_dump_path.exists():
        return pd.DataFrame()
    rows = load_rows_from_payload(read_json(local_dump_path))
    records = [
        {
            "submission_id": int(row["id"]),
            "email": normalize_text(row.get("email")),
            "time": int(row.get("time") or 0),
            "total": float(row.get("total")),
        }
        for row in rows
    ]
    frame = pd.DataFrame.from_records(records).sort_values(["email", "time", "submission_id"])
    frame["submitted_at_utc"] = pd.to_datetime(frame["time"], unit="ms", utc=True)
    return frame


def snapshot_ids(name: str) -> set[int]:
    path = RAW_DIR / name
    if not path.exists():
        return set()
    rows = load_rows_from_payload(read_json(path))
    return {int(row["id"]) for row in rows}


@app.command()
def main() -> None:
    """Normalize the paginated API history into analysis-ready parquet files."""

    ensure_dir(DERIVED_DIR)
    rows = load_history_rows()
    if not rows:
        raise typer.BadParameter("No history pages found. Run download_history.py first.")

    submissions, attempts = build_frames(rows)
    latest_any = submissions[submissions["submission_id"].isin(snapshot_ids("latest-all.json"))].sort_values("email")
    latest_positive = submissions[
        submissions["submission_id"].isin(snapshot_ids("latest-positive.json"))
    ].sort_values("email")
    ever_positive_latest = (
        submissions[submissions["total"] >= 0]
        .groupby("email", as_index=False)
        .tail(1)
        .sort_values("email")
    )
    negative_events = submissions[submissions["is_negative"]].copy().sort_values(["time", "submission_id"])
    local_dump = flatten_local_dump()

    submissions.to_parquet(DERIVED_DIR / "submission_history.parquet", index=False)
    attempts.to_parquet(DERIVED_DIR / "question_attempts.parquet", index=False)
    latest_any.to_parquet(DERIVED_DIR / "latest_any.parquet", index=False)
    latest_positive.to_parquet(DERIVED_DIR / "latest_positive.parquet", index=False)
    ever_positive_latest.to_parquet(DERIVED_DIR / "ever_positive_latest.parquet", index=False)
    negative_events.to_parquet(DERIVED_DIR / "negative_events.parquet", index=False)
    if not local_dump.empty:
        local_dump.to_parquet(DERIVED_DIR / "local_dump_latest.parquet", index=False)

    comparison = {
        "history_rows": int(len(submissions)),
        "history_students": int(submissions["email"].nunique()),
        "latest_any_rows": int(len(latest_any)),
        "latest_positive_rows": int(len(latest_positive)),
        "ever_positive_latest_rows": int(len(ever_positive_latest)),
        "negative_rows": int(len(negative_events)),
        "local_dump_rows": int(len(local_dump)),
        "local_dump_email_overlap": int(
            len(set(latest_positive["email"]).intersection(set(local_dump["email"]))) if not local_dump.empty else 0
        ),
    }
    write_json(DERIVED_DIR / "normalization-summary.json", comparison)
    typer.echo(f"[normalize] done: {comparison}")


if __name__ == "__main__":
    app()
