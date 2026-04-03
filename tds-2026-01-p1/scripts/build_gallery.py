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

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
import re
import shutil
from typing import Any

import pandas as pd
from rich.traceback import install
import typer

from tds_p1_common import ANALYSIS_DIR, DERIVED_DIR, IMAGE_QUESTION_IDS, QUESTION_LABELS, ROOT, ensure_dir, parse_submission_urls, read_json, safe_slug, sha256_text, write_json

install(show_locals=True)

app = typer.Typer(add_completion=False)

DEADLINE_INFO_PATH = Path("/home/sanand/code/exam/src/exam-tds-2026-01-p1.info.js")
DEFAULT_GALLERY_DIR = ROOT / "gallery"
DEFAULT_MODEL = "gemini-3.1-pro-preview"
EVAL_ROOT = ANALYSIS_DIR / "image-evals"
DEADLINE_RE = re.compile(r'end:\s*"(?P<deadline>[^"]+)"')
PRICING = {
    "gemini-3.1-pro-preview": {
        "billing_mode": "standard",
        "input_usd_per_million_tokens": 2.0,
        "output_usd_per_million_tokens": 12.0,
        "source_url": "https://ai.google.dev/gemini-api/docs/pricing?hl=en#gemini-3.1-pro-preview",
    }
}


def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def parse_deadline() -> tuple[str, int]:
    """Return the exam deadline as an ISO string and epoch milliseconds."""

    match = DEADLINE_RE.search(DEADLINE_INFO_PATH.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"Could not parse deadline from {DEADLINE_INFO_PATH}")
    deadline_iso = match.group("deadline")
    deadline = datetime.fromisoformat(deadline_iso)
    deadline_ms = int(deadline.timestamp() * 1000)
    return deadline_iso, deadline_ms


def eval_result_path(model_slug: str, email: str, question_id: str, submission_id: int) -> Path:
    return (
        EVAL_ROOT
        / model_slug
        / "results"
        / question_id
        / f"{safe_slug(email)}--submission-{submission_id}.json"
    )


def resolve_project_path(value: str) -> Path:
    """Resolve manifest-relative paths that may be rooted at project/ or project/data/."""

    direct = ROOT / value
    if direct.exists():
        return direct
    data_relative = ROOT / "data" / value
    if data_relative.exists():
        return data_relative
    return direct


def gallery_user(email: str) -> str:
    return sha256_text(email.strip().lower())[:5]


def gallery_thumb_path(gallery_dir: Path, user: str, question_id: str, submission_id: int) -> Path:
    return gallery_dir / "thumbs" / question_id / f"{user}--submission-{submission_id}.avif"


def text_value(value: Any) -> str:
    try:
        if value is None or pd.isna(value):
            return ""
    except Exception:  # noqa: BLE001
        if value is None:
            return ""
    return str(value)


def bool_value(value: Any) -> bool:
    try:
        if value is None or pd.isna(value):
            return False
    except Exception:  # noqa: BLE001
        if value is None:
            return False
    return bool(value)


def existing_project_path(value: str | None) -> Path | None:
    candidate = text_value(value)
    if not candidate:
        return None
    resolved = resolve_project_path(candidate)
    return resolved if resolved.exists() else None


def load_latest_gallery_rows(deadline_ms: int, model_slug: str) -> pd.DataFrame:
    """Load latest pre-deadline image answers for all students with publish/release status."""

    attempts = pd.read_parquet(DERIVED_DIR / "question_attempts.parquet")
    manifest_source = pd.read_parquet(DERIVED_DIR / "image_manifest.parquet")
    manifest = manifest_source.rename(
        columns={column: f"manifest_{column}" for column in manifest_source.columns if column not in {"email", "question_id", "submission_id"}}
    )
    latest = (
        attempts[
            attempts["question_id"].isin(IMAGE_QUESTION_IDS)
            & attempts["has_answer"]
            & (attempts["time"] <= deadline_ms)
        ]
        .sort_values(["email", "question_id", "time", "submission_id"])
        .groupby(["email", "question_id"], as_index=False)
        .tail(1)
        .copy()
    )
    latest["submitted_at_utc"] = pd.to_datetime(latest["time"], unit="ms", utc=True)
    joined = latest.merge(
        manifest,
        on=["email", "question_id", "submission_id"],
        how="left",
    )
    parsed_urls = joined["answer_text"].map(parse_submission_urls)
    joined["image_url"] = [
        text_value(row.get("manifest_image_url")) or (urls[0] if urls else "")
        for row, urls in zip(joined.to_dict(orient="records"), parsed_urls, strict=False)
    ]
    joined["json_url"] = [
        text_value(row.get("manifest_json_url")) or (urls[1] if urls else "")
        for row, urls in zip(joined.to_dict(orient="records"), parsed_urls, strict=False)
    ]
    joined["manifest_status"] = joined["manifest_status"].fillna("")
    joined["has_local_image"] = joined["manifest_image_path"].map(lambda value: existing_project_path(text_value(value)) is not None)
    joined["has_local_json"] = joined["manifest_json_path"].map(lambda value: existing_project_path(text_value(value)) is not None)
    joined["has_local_thumbnail"] = joined["manifest_thumbnail_path"].map(lambda value: existing_project_path(text_value(value)) is not None)
    joined["has_submission_urls"] = parsed_urls.map(lambda value: value is not None)
    joined["has_eval_result"] = joined.apply(
        lambda row: eval_result_path(model_slug, str(row["email"]), str(row["question_id"]), int(row["submission_id"])).exists()
        if text_value(row.get("manifest_status")) == "ok"
        else False,
        axis=1,
    )

    def publish_status(row: pd.Series) -> str:
        manifest_status = text_value(row.get("manifest_status"))
        if not manifest_status:
            return "assets-not-fetched" if bool(row.get("has_submission_urls")) else "invalid-answer-format"
        if manifest_status != "ok":
            return manifest_status
        if not bool(row.get("has_local_image")):
            return "image-missing"
        if not bool(row.get("has_local_json")):
            return "json-missing"
        if not bool(row.get("has_local_thumbnail")):
            return "thumbnail-missing"
        if not bool(row.get("has_eval_result")):
            return "evaluation-missing"
        return "ok"

    def status_detail(row: pd.Series) -> str:
        status = publish_status(row)
        if status == "assets-not-fetched":
            return "Latest pre-deadline submission was not fetched into image_manifest.parquet."
        if status == "invalid-answer-format":
            return text_value(row.get("manifest_json_parse_error")) or "Answer does not contain exactly two submission URLs."
        if status in {"image-fetch-error", "image-metadata-error", "image-missing"}:
            return text_value(row.get("manifest_image_fetch_error")) or "Image file is unavailable locally."
        if status in {"json-fetch-error", "json-missing"}:
            return text_value(row.get("manifest_json_fetch_error")) or text_value(row.get("manifest_json_parse_error")) or "Submission JSON is unavailable locally."
        if status in {"thumbnail-error", "thumbnail-missing"}:
            return text_value(row.get("manifest_thumbnail_error")) or "Thumbnail is unavailable locally."
        if status == "evaluation-missing":
            return "Gemini evaluation result JSON is missing for this submission."
        return ""

    joined["status"] = joined.apply(publish_status, axis=1)
    joined["status_detail"] = joined.apply(status_detail, axis=1)
    return joined.sort_values(["email", "question_id"]).reset_index(drop=True)


def select_rows(rows: pd.DataFrame, requested: list[str], student_limit: int, all_students: bool) -> tuple[pd.DataFrame, dict[str, str]]:
    """Return the selected gallery rows and a human-readable selection strategy."""

    if requested:
        requested_set = {email.strip().lower() for email in requested}
        selected = rows[rows["email"].str.lower().isin(requested_set)].copy()
        found = {email.lower() for email in selected["email"].unique().tolist()}
        missing = sorted(email for email in requested if email.lower() not in found)
        if missing:
            raise typer.BadParameter("These emails have no latest pre-deadline image-answer rows: " + ", ".join(missing))
        strategy = {
            "mode": "requested-emails",
            "description": "Latest pre-deadline answered image submission per requested email/question, including rows with missing local assets or evaluations.",
        }
        return selected.sort_values(["email", "question_id"]).reset_index(drop=True), strategy

    if all_students:
        strategy = {
            "mode": "all-students",
            "description": "Latest pre-deadline answered image submission per email/question for all students, including rows with missing local assets or evaluations.",
        }
        return rows.copy().sort_values(["email", "question_id"]).reset_index(drop=True), strategy

    eligible = (
        rows.groupby("email", as_index=False)
        .agg(question_count=("question_id", "nunique"), latest_time=("time", "max"))
        .query("question_count == 4")
        .sort_values(["latest_time", "email"])
    )
    selected_emails = eligible["email"].head(student_limit).tolist()
    selected = rows[rows["email"].isin(selected_emails)].copy().sort_values(["email", "question_id"]).reset_index(drop=True)
    strategy = {
        "mode": "first-complete-students",
        "description": "Latest pre-deadline answered image submission per email/question, restricted to the first students with all four image-question answers present before the deadline.",
    }
    return selected, strategy


def question_metadata(result_payload: dict[str, Any]) -> dict[str, Any]:
    request = result_payload.get("request") or {}
    response = result_payload.get("response") or {}
    return {
        "label": str(result_payload.get("question_label", "")),
        "system_instruction": request.get("system_instruction", ""),
        "user_message": request.get("user_message", ""),
        "response_json_schema": request.get("response_json_schema", {}),
        "score_dimensions": sorted((response.get("scores") or {}).keys()),
    }


def native_submission(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {str(key): native_submission(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [native_submission(value) for value in payload]
    return payload


def sharing_allowed(row: pd.Series, submission_payload: dict[str, Any]) -> bool:
    if "publish_email" in submission_payload:
        return bool_value(submission_payload.get("publish_email"))
    return bool_value(row.get("manifest_publish_email", False))


def load_submission_payload(row: pd.Series) -> dict[str, Any] | None:
    path = existing_project_path(text_value(row.get("manifest_json_path")))
    if not path:
        return None
    try:
        payload = read_json(path)
    except Exception:  # noqa: BLE001
        return None
    return payload if isinstance(payload, dict) else None


def build_result(
    row: pd.Series,
    *,
    result_payload: dict[str, Any] | None,
    submission_payload: dict[str, Any] | None,
    thumb_rel: str | None,
) -> dict[str, Any]:
    email = str(row["email"]).strip().lower()
    result = {
        "user": gallery_user(email),
        "question": str(row["question_id"]),
        "id": int(row["submission_id"]),
        "time": int(row["time"]),
        "status": str(row["status"]),
        "image_url": text_value(row.get("image_url")),
        "json_url": text_value(row.get("json_url")),
    }
    if text_value(row.get("status_detail")):
        result["status_detail"] = text_value(row.get("status_detail"))
    if result_payload is not None:
        result["evaluated_at_utc"] = str(result_payload.get("evaluated_at_utc", ""))
        result["response"] = native_submission(result_payload.get("response") or {})
    if submission_payload is not None:
        result["submission"] = native_submission(submission_payload)
    if thumb_rel:
        result["thumbnail"] = thumb_rel
    if sharing_allowed(row, submission_payload or {}):
        result["email"] = email
    return result


def summary_payload(
    *,
    deadline_iso: str,
    deadline_ms: int,
    model: str,
    student_count: int,
    public_email_count: int,
    selection: dict[str, str],
    expected_result_count: int,
    ok_result_count: int,
    status_counts: dict[str, int],
    question_meta: dict[str, dict[str, Any]],
    results: list[dict[str, Any]],
    cost_estimate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "format": "gallery-summary.v4",
        "generated_at_utc": now_utc(),
        "deadline": {
            "iso": deadline_iso,
            "time_ms": deadline_ms,
        },
        "model": model,
        "complete": len(results) == expected_result_count,
        "student_count": student_count,
        "public_email_count": public_email_count,
        "result_count": len(results),
        "expected_result_count": expected_result_count,
        "ok_result_count": ok_result_count,
        "gap_count": max(len(results) - ok_result_count, 0),
        "status_counts": status_counts,
        "selection": selection,
        "questions": {key: question_meta[key] for key in sorted(question_meta)},
        "cost_estimate": cost_estimate,
        "results": results,
    }


def write_gallery_summary(summary_path: Path, payload: dict[str, Any]) -> None:
    write_json(summary_path, payload, compact=True)


def cost_estimate(model: str, all_rows: pd.DataFrame, usage_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Estimate observed and projected Gemini cost from saved token usage."""

    pricing = PRICING.get(model)
    if not pricing or not usage_rows:
        return {}

    usage = pd.DataFrame.from_records(usage_rows)
    observed_prompt_tokens = int(usage["prompt_token_count"].sum())
    observed_output_tokens = int(usage["candidates_token_count"].sum())
    observed_cost_usd = (
        observed_prompt_tokens * pricing["input_usd_per_million_tokens"] / 1_000_000
        + observed_output_tokens * pricing["output_usd_per_million_tokens"] / 1_000_000
    )

    question_counts = all_rows.groupby("question_id").size().to_dict()
    question_averages = (
        usage.groupby("question_id", as_index=False)
        .agg(
            avg_prompt_token_count=("prompt_token_count", "mean"),
            avg_output_token_count=("candidates_token_count", "mean"),
            observed_evaluations=("question_id", "size"),
        )
        .sort_values("question_id")
    )

    projected_prompt_tokens = 0.0
    projected_output_tokens = 0.0
    by_question: list[dict[str, Any]] = []
    for row in question_averages.itertuples(index=False):
        full_count = int(question_counts.get(row.question_id, 0))
        projected_prompt_tokens += float(row.avg_prompt_token_count) * full_count
        projected_output_tokens += float(row.avg_output_token_count) * full_count
        by_question.append(
            {
                "question_id": str(row.question_id),
                "question_label": QUESTION_LABELS[str(row.question_id)],
                "observed_evaluations": int(row.observed_evaluations),
                "full_cohort_evaluations": full_count,
                "avg_prompt_token_count": round(float(row.avg_prompt_token_count), 2),
                "avg_output_token_count": round(float(row.avg_output_token_count), 2),
            }
        )

    projected_cost_usd = (
        projected_prompt_tokens * pricing["input_usd_per_million_tokens"] / 1_000_000
        + projected_output_tokens * pricing["output_usd_per_million_tokens"] / 1_000_000
    )

    return {
        "pricing": pricing,
        "observed": {
            "evaluations": int(len(usage)),
            "prompt_token_count": observed_prompt_tokens,
            "output_token_count": observed_output_tokens,
            "estimated_cost_usd": round(float(observed_cost_usd), 4),
        },
        "projected_full_image_cohort": {
            "evaluations": int(len(all_rows)),
            "prompt_token_count": int(round(projected_prompt_tokens)),
            "output_token_count": int(round(projected_output_tokens)),
            "estimated_cost_usd": round(float(projected_cost_usd), 4),
        },
        "by_question": by_question,
    }


@app.command()
def main(
    emails: list[str] | None = typer.Option(None, "--email", help="Restrict to specific student emails."),
    student_limit: int = typer.Option(5, "--student-limit", min=1, help="Select the first N eligible students when --email is not provided."),
    all_students: bool = typer.Option(False, "--all-students", help="Include all latest pre-deadline image-answer rows for all students."),
    clean: bool = typer.Option(False, "--clean", help="Remove gallery/thumbs before rebuilding."),
    gallery_dir: Path = typer.Option(DEFAULT_GALLERY_DIR, "--gallery-dir", help="Output gallery directory."),
    model: str = typer.Option(DEFAULT_MODEL, "--model", help="Model subdirectory under analysis/image-evals/."),
) -> None:
    """Build a publishable gallery with copied thumbnails and a summary.json."""

    deadline_iso, deadline_ms = parse_deadline()
    gallery_dir = gallery_dir.resolve()
    model_slug = safe_slug(model)
    rows = load_latest_gallery_rows(deadline_ms, model_slug)
    selected, selection = select_rows(rows, emails or [], student_limit, all_students)
    if selected.empty:
        raise typer.BadParameter("No gallery rows selected.")
    selected_emails = sorted(selected["email"].unique().tolist())

    summary_path = gallery_dir / "summary.json"
    if clean:
        shutil.rmtree(gallery_dir / "thumbs", ignore_errors=True)
    ensure_dir(gallery_dir / "thumbs")

    results: list[dict[str, Any]] = []
    question_meta: dict[str, dict[str, Any]] = {}
    usage_rows: list[dict[str, Any]] = []

    for row in selected.itertuples(index=False):
        series = pd.Series(row._asdict())
        eval_path = eval_result_path(model_slug, str(series["email"]), str(series["question_id"]), int(series["submission_id"]))
        result_payload = read_json(eval_path) if eval_path.exists() else None
        submission_payload = load_submission_payload(series)
        source_thumb = existing_project_path(text_value(series.get("manifest_thumbnail_path")))
        thumb_rel: str | None = None
        if source_thumb is not None:
            user = gallery_user(str(series["email"]))
            gallery_thumb = gallery_thumb_path(gallery_dir, user, str(series["question_id"]), int(series["submission_id"]))
            ensure_dir(gallery_thumb.parent)
            if clean or not gallery_thumb.exists():
                shutil.copy2(source_thumb, gallery_thumb)
            thumb_rel = str(gallery_thumb.relative_to(gallery_dir))

        result = build_result(
            series,
            result_payload=result_payload,
            submission_payload=submission_payload,
            thumb_rel=thumb_rel,
        )
        results.append(result)
        if result_payload is not None:
            question_meta[str(series["question_id"])] = question_metadata(result_payload)
            usage_metadata = (result_payload.get("api_response") or {}).get("usage_metadata") or {}
            usage_rows.append(
                {
                    "question_id": str(series["question_id"]),
                    "prompt_token_count": int(usage_metadata.get("prompt_token_count") or 0),
                    "candidates_token_count": int(usage_metadata.get("candidates_token_count") or 0),
                }
            )

    status_counts = dict(sorted(Counter(result["status"] for result in results).items()))
    ok_result_count = status_counts.get("ok", 0)

    write_gallery_summary(
        summary_path,
        summary_payload(
            deadline_iso=deadline_iso,
            deadline_ms=deadline_ms,
            model=model,
            student_count=len(selected_emails),
            public_email_count=len({result["user"] for result in results if "email" in result}),
            selection=selection,
            expected_result_count=len(selected),
            ok_result_count=ok_result_count,
            status_counts=status_counts,
            question_meta=question_meta,
            results=results,
            cost_estimate=cost_estimate(model, selected, usage_rows),
        ),
    )

    typer.echo(
        f"[gallery] wrote {summary_path.relative_to(ROOT)} with {len(results)}/{len(selected)} rows "
        f"for {len(selected_emails)} students; ok={ok_result_count} gaps={len(results) - ok_result_count}"
    )


if __name__ == "__main__":
    app()
