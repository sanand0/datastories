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

from collections import Counter, defaultdict
from pathlib import Path
import shutil
import subprocess
from typing import Any

import orjson
import pandas as pd
from rich.traceback import install
import typer

from build_gallery import DEFAULT_MODEL, existing_project_path, gallery_user, load_latest_gallery_rows, parse_deadline, text_value
from tds_p1_common import IMAGE_QUESTION_IDS, ROOT, ensure_dir, safe_slug

install(show_locals=True)

app = typer.Typer(add_completion=False)
DEFAULT_OUTPUT_DIR = ROOT / "data" / "release-assets"


def describe_payload() -> dict[str, Any]:
    return {
        "name": "build_question_release_assets.py",
        "description": "Prepare per-question JSON and PNG assets for GitHub releases from latest pre-deadline image submissions.",
        "options": {
            "--question-id": {"type": "array[string]", "default": IMAGE_QUESTION_IDS},
            "--email": {"type": "array[string]", "default": []},
            "--output-dir": {"type": "path", "default": str(DEFAULT_OUTPUT_DIR)},
            "--model": {"type": "string", "default": DEFAULT_MODEL},
            "--force": {"type": "boolean", "default": False},
            "--dry-run": {"type": "boolean", "default": False},
            "--format": {"type": "string", "enum": ["text", "json"], "default": "text"},
        },
        "outputs": {
            "text": "Progress lines plus per-question counts.",
            "json": "Summary object with prepared/skipped counts and file paths.",
        },
    }


def copy_json_asset(source: Path, destination: Path, force: bool) -> str:
    ensure_dir(destination.parent)
    if destination.exists() and not force:
        return "existing"
    shutil.copy2(source, destination)
    return "written"


def write_png_asset(source: Path, destination: Path, force: bool) -> str:
    ensure_dir(destination.parent)
    if destination.exists() and not force:
        return "existing"
    if source.suffix.lower() == ".png":
        shutil.copy2(source, destination)
        return "written"
    subprocess.run(
        [
            "magick",
            str(source),
            "-auto-orient",
            "png24:" + str(destination),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return "written"


@app.command()
def main(
    question_ids: list[str] | None = typer.Option(None, "--question-id", help="Restrict to one or more image question IDs."),
    emails: list[str] | None = typer.Option(None, "--email", help="Restrict to specific student emails."),
    output_dir: Path = typer.Option(DEFAULT_OUTPUT_DIR, "--output-dir", help="Directory where per-question release assets are written."),
    model: str = typer.Option(DEFAULT_MODEL, "--model", help="Model slug source used for evaluation status."),
    force: bool = typer.Option(False, "--force", help="Rebuild PNG/JSON assets even if they already exist."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be prepared without writing files."),
    format: str = typer.Option("text", "--format", help="Output format: text or json."),
    describe: bool = typer.Option(False, "--describe", help="Print machine-readable CLI description and exit."),
) -> None:
    """Prepare per-question release assets as JSON and PNG files."""

    if describe:
        typer.echo(orjson.dumps(describe_payload(), option=orjson.OPT_INDENT_2).decode())
        raise typer.Exit()

    selected_questions = question_ids or IMAGE_QUESTION_IDS
    invalid_questions = sorted(set(selected_questions) - set(IMAGE_QUESTION_IDS))
    if invalid_questions:
        raise typer.BadParameter("Unsupported question IDs: " + ", ".join(invalid_questions))

    deadline_iso, deadline_ms = parse_deadline()
    frame = load_latest_gallery_rows(deadline_ms, safe_slug(model))
    frame = frame[frame["question_id"].isin(selected_questions)].copy()
    if emails:
        requested = {email.strip().lower() for email in emails}
        frame = frame[frame["email"].str.lower().isin(requested)].copy()
    if frame.empty:
        raise typer.BadParameter("No matching latest pre-deadline image submissions found.")

    output_dir = output_dir.resolve()
    prepared_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    status_counts = Counter()
    write_counts = Counter()

    for row in frame.itertuples(index=False):
        series = pd.Series(row._asdict())
        question_id = str(series["question_id"])
        email = str(series["email"]).strip().lower()
        user = gallery_user(email)
        status = str(series["status"])
        json_source = existing_project_path(text_value(series.get("manifest_json_path")))
        image_source = existing_project_path(text_value(series.get("manifest_image_path")))
        json_target = output_dir / question_id / f"{user}--submission-{int(series['submission_id'])}.json"
        png_target = output_dir / question_id / f"{user}--submission-{int(series['submission_id'])}.png"
        item: dict[str, Any] = {
            "question_id": question_id,
            "user": user,
            "submission_id": int(series["submission_id"]),
            "status": status,
            "json_target": str(json_target),
            "png_target": str(png_target),
            "releasable": False,
        }

        if json_source is None or image_source is None:
            status_counts[status] += 1
            prepared_by_question[question_id].append(item)
            continue

        try:
            if not dry_run:
                json_result = copy_json_asset(json_source, json_target, force)
                png_result = write_png_asset(image_source, png_target, force)
            else:
                json_result = "dry-run"
                png_result = "dry-run"
            item.update(
                {
                    "releasable": True,
                    "json_result": json_result,
                    "png_result": png_result,
                }
            )
            write_counts[json_result] += 1
            write_counts[png_result] += 1
        except Exception as exc:  # noqa: BLE001
            item["status"] = "release-build-error"
            item["error"] = str(exc)
            status_counts["release-build-error"] += 1
            prepared_by_question[question_id].append(item)
            continue

        status_counts[status] += 1
        prepared_by_question[question_id].append(item)

    summary = {
        "deadline_iso": deadline_iso,
        "output_dir": str(output_dir),
        "questions": selected_questions,
        "row_count": int(len(frame)),
        "releasable_count": int(sum(1 for items in prepared_by_question.values() for item in items if item["releasable"])),
        "status_counts": dict(sorted(status_counts.items())),
        "write_counts": dict(sorted(write_counts.items())),
        "by_question": {
            question_id: {
                "rows": len(items),
                "releasable": sum(1 for item in items if item["releasable"]),
                "status_counts": dict(sorted(Counter(item["status"] for item in items).items())),
            }
            for question_id, items in sorted(prepared_by_question.items())
        },
    }

    if format == "json":
        typer.echo(orjson.dumps(summary, option=orjson.OPT_INDENT_2).decode())
        raise typer.Exit()
    if format != "text":
        raise typer.BadParameter("--format must be 'text' or 'json'")

    for question_id in selected_questions:
        counts = summary["by_question"].get(question_id, {"rows": 0, "releasable": 0, "status_counts": {}})
        typer.echo(
            f"[release-assets] {question_id}: releasable={counts['releasable']}/{counts['rows']} "
            f"statuses={counts['status_counts']}"
        )
    typer.echo(
        f"[release-assets] total releasable={summary['releasable_count']}/{summary['row_count']} "
        f"writes={summary['write_counts']} output={output_dir.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    app()
