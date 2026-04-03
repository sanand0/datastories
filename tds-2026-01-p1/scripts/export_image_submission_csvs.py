#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "orjson>=3.10",
#   "pandas>=2.2",
#   "rich>=14.0",
#   "typer>=0.16",
# ]
# ///

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import orjson
import pandas as pd
from rich.traceback import install
import typer

from tds_p1_common import ANALYSIS_DIR, ASSETS_DIR, IMAGE_QUESTION_IDS, ROOT, ensure_dir

install(show_locals=True)

app = typer.Typer(add_completion=False)

META_COLUMNS = [
    "submission_id",
    "question_id",
    "json_filename",
    "json_path",
    "parse_status",
    "parse_error",
]


def infer_submission_id(path: Path, question_id: str) -> int | None:
    suffix = f"-{question_id}-submission.json"
    if not path.name.endswith(suffix):
        return None
    prefix = path.name[: -len(suffix)]
    return int(prefix) if prefix.isdigit() else None


def load_payload(path: Path) -> tuple[Any, str, str | None]:
    raw = path.read_bytes()
    try:
        return orjson.loads(raw), "ok", None
    except orjson.JSONDecodeError as exc:
        text = raw.decode("utf-8", errors="replace")
        try:
            return json.loads(text), "utf8-replaced", str(exc)
        except json.JSONDecodeError as nested_exc:
            return {}, "parse-error", f"{exc}; {nested_exc}"


def flatten_payload(payload: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(payload, dict):
        rows: dict[str, Any] = {}
        for key in sorted(payload):
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.update(flatten_payload(payload[key], child_prefix))
        if not rows and prefix:
            rows[prefix] = "{}"
        return rows
    if isinstance(payload, list):
        key = prefix or "value"
        return {key: orjson.dumps(payload).decode("utf-8")}
    key = prefix or "value"
    return {key: payload}


def export_question_csv(question_id: str) -> tuple[Path, pd.DataFrame]:
    question_dir = ASSETS_DIR / question_id
    paths = sorted(question_dir.glob("*-submission.json"))
    rows: list[dict[str, Any]] = []
    extra_columns: set[str] = set()

    for path in paths:
        payload, parse_status, parse_error = load_payload(path)
        row = {
            "submission_id": infer_submission_id(path, question_id),
            "question_id": question_id,
            "json_filename": path.name,
            "json_path": path.relative_to(ROOT).as_posix(),
            "parse_status": parse_status,
            "parse_error": parse_error,
        }
        row.update(flatten_payload(payload))
        rows.append(row)
        extra_columns.update(row)

    frame = pd.DataFrame(rows)
    ordered_columns = META_COLUMNS + sorted(column for column in extra_columns if column not in META_COLUMNS)
    frame = frame.reindex(columns=ordered_columns)
    if not frame.empty:
        frame = frame.sort_values(["submission_id", "json_filename"], kind="stable", na_position="last")

    output_path = ANALYSIS_DIR / f"{question_id}.csv"
    ensure_dir(output_path.parent)
    frame.to_csv(output_path, index=False)
    return output_path, frame


@app.command()
def main() -> None:
    for question_id in IMAGE_QUESTION_IDS:
        output_path, frame = export_question_csv(question_id)
        counts = frame["parse_status"].value_counts(dropna=False).to_dict() if not frame.empty else {}
        typer.echo(
            f"{question_id}: wrote {len(frame)} rows to {output_path.relative_to(ROOT)}"
            f" ({', '.join(f'{key}={value}' for key, value in counts.items()) or 'no rows'})"
        )


if __name__ == "__main__":
    app()
