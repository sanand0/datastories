#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "google-genai>=1.30.0",
#   "orjson>=3.10",
#   "pandas>=2.2",
#   "pillow>=11.2",
#   "pillow-avif-plugin>=1.5.2",
#   "pyarrow>=20.0",
#   "python-dotenv>=1.0",
#   "rich>=14.0",
#   "tenacity>=9.1",
#   "typer>=0.16",
# ]
# ///

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import io
import os
import re
import sys
from time import perf_counter
from typing import Any

from dotenv import dotenv_values
from google import genai
from google.genai import types
import orjson
import pandas as pd
import pillow_avif  # noqa: F401
from PIL import Image, ImageOps
from rich.traceback import install
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
import typer

from tds_p1_common import ANALYSIS_DIR, DERIVED_DIR, IMAGE_QUESTION_IDS, QUESTION_LABELS, ROOT, ensure_dir, read_json, safe_slug, write_json

install(show_locals=True)

app = typer.Typer(add_completion=False)
Image.MAX_IMAGE_PIXELS = None

MODEL_NAME = "gemini-3.1-pro-preview"
MAX_IMAGE_SIZE = (768, 768)
QUESTION_SOURCE_DIR = Path("/home/sanand/code/exam/src")
QUESTION_SOURCE_PATHS = {
    "q-generate-affective-chart": QUESTION_SOURCE_DIR / "q-generate-affective-chart.js",
    "q-generate-concept-incarnation": QUESTION_SOURCE_DIR / "q-generate-concept-incarnation.js",
    "q-generate-style-transplant": QUESTION_SOURCE_DIR / "q-generate-style-transplant.js",
    "q-generate-paradox-portrait": QUESTION_SOURCE_DIR / "q-generate-paradox-portrait.js",
}
MODEL_SLUG = safe_slug(MODEL_NAME)
OUTPUT_ROOT = ANALYSIS_DIR / "image-evals" / MODEL_SLUG
RESULTS_DIR = OUTPUT_ROOT / "results"
RESIZED_DIR = OUTPUT_ROOT / "resized"
RUNS_DIR = OUTPUT_ROOT / "runs"
SUMMARIES_DIR = OUTPUT_ROOT / "summaries"
PROGRESS_PATH = OUTPUT_ROOT / "progress.json"
MANIFEST_PATH = DERIVED_DIR / "image_manifest.parquet"
BRIEF_MARKDOWN_RE = re.compile(r"briefMarkdown:\s*`(?P<content>[\s\S]*?)`,\s*bonusEvaluationNotice:", re.S)
SYSTEM_PROMPT_RE = re.compile(r"### System Prompt\s+```text\n(?P<prompt>[\s\S]*?)\n```", re.S)
USER_PROMPT_RE = re.compile(r"### User Message to Send with Your Image[\s\S]*?```text\n(?P<prompt>[\s\S]*?)\n```", re.S)
PLACEHOLDER_RE = re.compile(r"\{([A-Z_]+)\}")

QUESTION_FIELDS = {
    "q-generate-affective-chart": (),
    "q-generate-concept-incarnation": ("concept",),
    "q-generate-style-transplant": ("concept", "tradition_name", "tradition_period", "tradition_approach"),
    "q-generate-paradox-portrait": ("paradox", "visual_logic"),
}
QUESTION_USER_REPLACEMENTS = {
    "q-generate-affective-chart": {},
    "q-generate-concept-incarnation": {"[paste your concept here]": "concept"},
    "q-generate-style-transplant": {
        "Concept: [paste from your JSON]": "Concept: {concept}",
        "Tradition: [tradition_name] ([tradition_period])": "Tradition: {tradition_name} ({tradition_period})",
        "Approach: [tradition_approach]": "Approach: {tradition_approach}",
    },
    "q-generate-paradox-portrait": {
        "Paradox: [paste from your JSON]": "Paradox: {paradox}",
        "Visual logic: [paste from your JSON]": "Visual logic: {visual_logic}",
    },
}


def score_block_schema(reason_description: str, improvement_description: str) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "score": {"type": "number", "minimum": 0.0, "maximum": 10.0},
            "reason": {"type": "string", "description": reason_description},
            "improvement": {"type": "string", "description": improvement_description},
        },
        "required": ["score", "reason", "improvement"],
    }


RESPONSE_SCHEMAS = {
    "q-generate-affective-chart": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "scores": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "emotional_impact": score_block_schema(
                        "Specific emotional impact assessment tied to the image.",
                        "One actionable improvement suggestion.",
                    ),
                    "constraint_adherence": score_block_schema(
                        "Constraint adherence assessment tied to the image.",
                        "One actionable improvement suggestion.",
                    ),
                    "visual_originality": score_block_schema(
                        "Assessment of whether the image escapes default AI data-visualization clichés.",
                        "One actionable improvement suggestion.",
                    ),
                    "legibility_without_labels": score_block_schema(
                        "Assessment of whether the insight reads from the image without labels.",
                        "One actionable improvement suggestion.",
                    ),
                    "compositional_intent": score_block_schema(
                        "Assessment of deliberate composition and craft.",
                        "One actionable improvement suggestion.",
                    ),
                },
                "required": [
                    "emotional_impact",
                    "constraint_adherence",
                    "visual_originality",
                    "legibility_without_labels",
                    "compositional_intent",
                ],
            },
            "overall_score": {"type": "number", "minimum": 0.0, "maximum": 10.0},
            "brief_met": {"type": "boolean"},
            "model_default_escaped": {"type": "boolean"},
            "exhibition_worthy": {"type": "boolean"},
            "one_line_verdict": {"type": "string"},
        },
        "required": ["scores", "overall_score", "brief_met", "model_default_escaped", "exhibition_worthy", "one_line_verdict"],
    },
    "q-generate-concept-incarnation": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "concept_identified_by_evaluator": {"type": "string"},
            "concept_match": {"type": "boolean"},
            "scores": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "concept_recognition": score_block_schema(
                        "Whether a domain expert would recognize the concept from the image alone.",
                        "One actionable improvement suggestion.",
                    ),
                    "constraint_adherence": score_block_schema(
                        "Which constraints are met or violated.",
                        "One actionable improvement suggestion.",
                    ),
                    "physical_plausibility": score_block_schema(
                        "Whether the scene feels physically plausible.",
                        "One actionable improvement suggestion.",
                    ),
                    "structural_fidelity": score_block_schema(
                        "Whether the scene maps to the deep structure of the concept.",
                        "One actionable improvement suggestion.",
                    ),
                    "visual_execution": score_block_schema(
                        "Assessment of composition, coherence, and craft.",
                        "One actionable improvement suggestion.",
                    ),
                },
                "required": [
                    "concept_recognition",
                    "constraint_adherence",
                    "physical_plausibility",
                    "structural_fidelity",
                    "visual_execution",
                ],
            },
            "overall_score": {"type": "number", "minimum": 0.0, "maximum": 10.0},
            "model_default_escaped": {"type": "boolean"},
            "exhibition_worthy": {"type": "boolean"},
            "one_line_verdict": {"type": "string"},
        },
        "required": [
            "concept_identified_by_evaluator",
            "concept_match",
            "scores",
            "overall_score",
            "model_default_escaped",
            "exhibition_worthy",
            "one_line_verdict",
        ],
    },
    "q-generate-style-transplant": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "tradition_identified_by_evaluator": {"type": "string"},
            "tradition_match": {"type": "boolean"},
            "concept_identified_by_evaluator": {"type": "string"},
            "concept_match": {"type": "boolean"},
            "anachronisms_detected": {"type": "string"},
            "scores": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "tradition_authenticity": score_block_schema(
                        "Whether the image genuinely inhabits the stated tradition.",
                        "One actionable improvement suggestion.",
                    ),
                    "tradition_identifiability": score_block_schema(
                        "Whether a knowledgeable viewer would identify the tradition without prompting.",
                        "One actionable improvement suggestion.",
                    ),
                    "concept_discernibility": score_block_schema(
                        "Whether the data-science concept is recognizable and integrated.",
                        "One actionable improvement suggestion.",
                    ),
                    "grammar_over_surface": score_block_schema(
                        "Whether the image applies grammar rather than surface texture alone.",
                        "One actionable improvement suggestion.",
                    ),
                    "integration": score_block_schema(
                        "Whether the concept and tradition feel genuinely fused.",
                        "One actionable improvement suggestion.",
                    ),
                },
                "required": [
                    "tradition_authenticity",
                    "tradition_identifiability",
                    "concept_discernibility",
                    "grammar_over_surface",
                    "integration",
                ],
            },
            "overall_score": {"type": "number", "minimum": 0.0, "maximum": 10.0},
            "exhibition_worthy": {"type": "boolean"},
            "one_line_verdict": {"type": "string"},
        },
        "required": [
            "tradition_identified_by_evaluator",
            "tradition_match",
            "concept_identified_by_evaluator",
            "concept_match",
            "anachronisms_detected",
            "scores",
            "overall_score",
            "exhibition_worthy",
            "one_line_verdict",
        ],
    },
    "q-generate-paradox-portrait": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "paradox_identified_by_evaluator": {"type": "string"},
            "paradox_match": {"type": "boolean"},
            "scores": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "paradox_embodiment": score_block_schema(
                        "Whether the image embodies the paradox's structural essence.",
                        "One actionable improvement suggestion.",
                    ),
                    "constraint_adherence": score_block_schema(
                        "Which constraints are met or violated.",
                        "One actionable improvement suggestion.",
                    ),
                    "expert_recognition": score_block_schema(
                        "Whether an expert would recognize the paradox.",
                        "One actionable improvement suggestion.",
                    ),
                    "uncanny_quality": score_block_schema(
                        "Whether the image produces contradiction or unease.",
                        "One actionable improvement suggestion.",
                    ),
                    "avoidance_of_literalism": score_block_schema(
                        "Whether the image avoids literal illustration and finds the paradox's core.",
                        "One actionable improvement suggestion.",
                    ),
                },
                "required": [
                    "paradox_embodiment",
                    "constraint_adherence",
                    "expert_recognition",
                    "uncanny_quality",
                    "avoidance_of_literalism",
                ],
            },
            "overall_score": {"type": "number", "minimum": 0.0, "maximum": 10.0},
            "diptych": {"type": "boolean"},
            "diptych_justified": {"type": ["boolean", "null"]},
            "exhibition_worthy": {"type": "boolean"},
            "one_line_verdict": {"type": "string"},
        },
        "required": [
            "paradox_identified_by_evaluator",
            "paradox_match",
            "scores",
            "overall_score",
            "diptych",
            "diptych_justified",
            "exhibition_worthy",
            "one_line_verdict",
        ],
    },
}


def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "unknown"
    total_seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def load_api_key() -> str:
    direct = os.environ.get("GEMINI_API_KEY", "").strip()
    if direct:
        return direct
    for directory in [ROOT, ROOT.parent, ROOT.parent.parent]:
        env_path = directory / ".env"
        if not env_path.exists():
            continue
        value = str(dotenv_values(env_path).get("GEMINI_API_KEY") or "").strip()
        if value:
            return value
    return ""


def load_params_value(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    candidate = value.strip()
    if not candidate:
        return {}
    path = Path(candidate)
    if path.exists():
        payload = orjson.loads(path.read_bytes())
    else:
        payload = orjson.loads(candidate)
    if not isinstance(payload, dict):
        raise typer.BadParameter("--params must be a JSON object or a path to one.")
    return payload


def resolve_option(value: Any, params: dict[str, Any], key: str, default: Any = None) -> Any:
    if value not in (None, (), [], ""):
        return value
    if key in params:
        return params[key]
    return default


def resolve_sequence(value: list[Any] | None, params: dict[str, Any], key: str) -> list[Any]:
    if value:
        return list(value)
    from_params = params.get(key, [])
    if from_params is None:
        return []
    if not isinstance(from_params, list):
        raise typer.BadParameter(f"--params.{key} must be a JSON array.")
    return list(from_params)


def normalize_question_ids(question_ids: list[str]) -> list[str]:
    if not question_ids:
        return list(IMAGE_QUESTION_IDS)
    unknown = sorted(set(question_ids) - set(IMAGE_QUESTION_IDS))
    if unknown:
        raise typer.BadParameter(f"Unknown question IDs: {', '.join(unknown)}")
    return question_ids


def format_choice(value: Any) -> str:
    if pd.isna(value):
        return ""
    return "" if value is None else str(value)


def output_format(requested: str, json_alias: bool) -> str:
    if json_alias:
        return "json"
    if requested != "auto":
        return requested
    return "text" if sys.stdout.isatty() else "json"


def describe_payload() -> dict[str, Any]:
    return {
        "command": "evaluate_images.py",
        "description": "Evaluate q-generate image submissions with Gemini and save structured outputs per submission.",
        "model": MODEL_NAME,
        "inputs": {
            "manifest": str(MANIFEST_PATH),
            "question_sources": {question_id: str(path) for question_id, path in QUESTION_SOURCE_PATHS.items()},
            "env": ["GEMINI_API_KEY"],
        },
        "params": {
            "question_ids": {"type": "array", "items": {"type": "string", "enum": IMAGE_QUESTION_IDS}},
            "emails": {"type": "array", "items": {"type": "string"}},
            "submission_ids": {"type": "array", "items": {"type": "integer"}},
            "limit": {"type": "integer", "minimum": 1},
            "offset": {"type": "integer", "minimum": 0},
            "shard_count": {"type": "integer", "minimum": 1},
            "shard_index": {"type": "integer", "minimum": 0},
            "force": {"type": "boolean"},
            "dry_run": {"type": "boolean"},
            "run_label": {"type": "string"},
            "format": {"type": "string", "enum": ["auto", "json", "text"]},
        },
        "outputs": {
            "result_files": f"{RESULTS_DIR}/<question_id>/<email-slug>--submission-<id>.json",
            "resized_images": f"{RESIZED_DIR}/<question_id>/<email-slug>--submission-<id>.<png|jpg>",
            "run_summaries": f"{RUNS_DIR}/<timestamp>--<label>.json",
            "aggregate_summary": str(SUMMARIES_DIR / "summary.json"),
            "aggregate_parquet": str(SUMMARIES_DIR / "summary.parquet"),
        },
        "notes": [
            "The script skips existing successful evaluations by default.",
            "Use --force with filters to re-evaluate existing results for a targeted subset.",
            "Use --shard-count and --shard-index for process-level parallelism.",
        ],
    }


def load_manifest() -> pd.DataFrame:
    if not MANIFEST_PATH.exists():
        raise typer.BadParameter(f"Missing manifest: {MANIFEST_PATH}")
    frame = pd.read_parquet(MANIFEST_PATH).copy()
    frame = frame[(frame["status"] == "ok") & frame["question_id"].isin(IMAGE_QUESTION_IDS)].copy()
    frame = frame.sort_values(["question_id", "email", "submission_id"]).reset_index(drop=True)
    return frame


def has_force_scope(question_ids: list[str], emails: list[str], submission_ids: list[int], limit: int, offset: int, shard_count: int) -> bool:
    return bool(question_ids or emails or submission_ids or limit or offset or shard_count > 1)


def result_path(row: pd.Series) -> Path:
    email_slug = safe_slug(str(row["email"]))
    return RESULTS_DIR / str(row["question_id"]) / f"{email_slug}--submission-{int(row['submission_id'])}.json"


def resized_path(row: pd.Series, suffix: str) -> Path:
    email_slug = safe_slug(str(row["email"]))
    return RESIZED_DIR / str(row["question_id"]) / f"{email_slug}--submission-{int(row['submission_id'])}{suffix}"


def resolve_existing_path(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    project_relative = ROOT / value
    if project_relative.exists():
        return project_relative
    data_relative = ROOT / "data" / value
    if data_relative.exists():
        return data_relative
    raise FileNotFoundError(f"Could not resolve file path: {value}")


def question_source_text(question_id: str) -> str:
    path = QUESTION_SOURCE_PATHS[question_id]
    text = path.read_text(encoding="utf-8")
    match = BRIEF_MARKDOWN_RE.search(text)
    if not match:
        raise ValueError(f"Could not extract briefMarkdown from {path}")
    return match.group("content").replace("\\`", "`")


QUESTION_PROMPT_CACHE: dict[str, dict[str, str]] = {}


def question_prompts(question_id: str) -> dict[str, str]:
    if question_id in QUESTION_PROMPT_CACHE:
        return QUESTION_PROMPT_CACHE[question_id]
    markdown = question_source_text(question_id)
    system_match = SYSTEM_PROMPT_RE.search(markdown)
    user_match = USER_PROMPT_RE.search(markdown)
    if not system_match or not user_match:
        raise ValueError(f"Could not extract evaluation prompts for {question_id}")
    QUESTION_PROMPT_CACHE[question_id] = {
        "system": system_match.group("prompt"),
        "user": user_match.group("prompt"),
    }
    return QUESTION_PROMPT_CACHE[question_id]


def required_question_values(row: pd.Series) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in QUESTION_FIELDS[str(row["question_id"])]:
        value = str(row.get(field) or "").strip()
        if not value:
            raise ValueError(f"Missing required field '{field}' for {row['question_id']} submission {int(row['submission_id'])}")
        values[field] = value
    return values


def apply_placeholder_values(template: str, values: dict[str, str]) -> str:
    def replacer(match: re.Match[str]) -> str:
        key = match.group(1).lower()
        if key not in values:
            raise ValueError(f"Missing placeholder value for {match.group(0)}")
        return values[key]

    return PLACEHOLDER_RE.sub(replacer, template)


def apply_user_replacements(question_id: str, template: str, values: dict[str, str]) -> str:
    rendered = template
    for pattern, replacement in QUESTION_USER_REPLACEMENTS[question_id].items():
        rendered = rendered.replace(pattern, replacement.format(**values))
    return rendered


def build_prompts(row: pd.Series) -> tuple[str, str, dict[str, str]]:
    question_id = str(row["question_id"])
    prompts = question_prompts(question_id)
    values = required_question_values(row)
    system_prompt = apply_placeholder_values(prompts["system"], values)
    user_prompt = apply_user_replacements(question_id, prompts["user"], values)
    return system_prompt, user_prompt, values


def open_and_resize_image(image_path: Path) -> tuple[bytes, str, dict[str, Any]]:
    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image)
        original = {"width": int(image.width), "height": int(image.height)}
        image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        if "A" in image.getbands():
            converted = image.convert("RGBA")
            mime_type = "image/png"
            suffix = ".png"
            format_name = "PNG"
            save_kwargs: dict[str, Any] = {"optimize": True}
        else:
            converted = image.convert("RGB")
            mime_type = "image/jpeg"
            suffix = ".jpg"
            format_name = "JPEG"
            save_kwargs = {"quality": 90, "optimize": True}
        buffer = io.BytesIO()
        converted.save(buffer, format=format_name, **save_kwargs)
        data = buffer.getvalue()
        metadata = {
            "original_width": original["width"],
            "original_height": original["height"],
            "resized_width": int(converted.width),
            "resized_height": int(converted.height),
            "mime_type": mime_type,
            "suffix": suffix,
            "bytes": len(data),
        }
        return data, mime_type, metadata


def write_resized_copy(path: Path, data: bytes) -> None:
    ensure_dir(path.parent)
    path.write_bytes(data)


def serialize_response(response: Any) -> dict[str, Any]:
    if response is None:
        return {}
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json", exclude_none=True)
    return {"text": getattr(response, "text", "")}


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def call_gemini(
    client: genai.Client,
    *,
    image_bytes: bytes,
    mime_type: str,
    system_prompt: str,
    user_prompt: str,
    response_schema: dict[str, Any],
) -> Any:
    return client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            user_prompt,
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_json_schema=response_schema,
            temperature=0,
            thinking_config=types.ThinkingConfig(thinking_level="low"),
        ),
    )


def parse_response_json(response: Any) -> dict[str, Any]:
    text = getattr(response, "text", "")
    if not text:
        raise ValueError("Gemini response.text was empty")
    payload = orjson.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Gemini response was not a JSON object")
    return payload


def flatten_scores(payload: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {
        "overall_score": payload.get("overall_score"),
        "exhibition_worthy": payload.get("exhibition_worthy"),
        "one_line_verdict": payload.get("one_line_verdict", ""),
    }
    for key, value in (payload.get("scores") or {}).items():
        if isinstance(value, dict):
            flat[f"{key}_score"] = value.get("score")
            flat[f"{key}_reason"] = value.get("reason", "")
            flat[f"{key}_improvement"] = value.get("improvement", "")
    return flat


def summary_from_result_files() -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(RESULTS_DIR.glob("*/*.json")):
        payload = read_json(path)
        if not isinstance(payload, dict):
            continue
        response_payload = payload.get("response") or {}
        row = {
            "path": str(path.relative_to(OUTPUT_ROOT)),
            "status": payload.get("status", ""),
            "question_id": payload.get("question_id", ""),
            "question_label": payload.get("question_label", ""),
            "email": payload.get("email", ""),
            "submission_id": payload.get("submission_id"),
            "evaluated_at_utc": payload.get("evaluated_at_utc", ""),
            "model": payload.get("model", ""),
            "api_error": payload.get("api_error", ""),
        }
        if isinstance(response_payload, dict):
            row.update(flatten_scores(response_payload))
        rows.append(row)
    frame = pd.DataFrame.from_records(rows)
    if frame.empty:
        return frame, {"results": 0, "ok_results": 0, "errors": 0, "generated_at_utc": now_utc(), "by_question": []}
    frame = frame.sort_values(["question_id", "email", "submission_id"]).reset_index(drop=True)
    ok = frame[frame["status"] == "ok"].copy()
    by_question: list[dict[str, Any]] = []
    if not ok.empty:
        grouped = (
            ok.groupby(["question_id", "question_label"], as_index=False)
            .agg(
                evaluations=("submission_id", "size"),
                mean_overall_score=("overall_score", "mean"),
                median_overall_score=("overall_score", "median"),
                exhibition_worthy_share=("exhibition_worthy", "mean"),
            )
            .sort_values(["question_id"])
        )
        for row in grouped.itertuples(index=False):
            by_question.append(
                {
                    "question_id": str(row.question_id),
                    "question_label": str(row.question_label),
                    "evaluations": int(row.evaluations),
                    "mean_overall_score": round(float(row.mean_overall_score), 3),
                    "median_overall_score": round(float(row.median_overall_score), 3),
                    "exhibition_worthy_share": round(float(row.exhibition_worthy_share * 100), 2),
                }
            )
    summary = {
        "results": int(len(frame)),
        "ok_results": int((frame["status"] == "ok").sum()),
        "errors": int((frame["status"] != "ok").sum()),
        "generated_at_utc": now_utc(),
        "by_question": by_question,
    }
    return frame, summary


def write_aggregate_summaries() -> dict[str, Any]:
    ensure_dir(SUMMARIES_DIR)
    frame, summary = summary_from_result_files()
    if not frame.empty:
        frame.to_parquet(SUMMARIES_DIR / "summary.parquet", index=False)
    write_json(SUMMARIES_DIR / "summary.json", summary)
    return summary


def manifest_subset(
    manifest: pd.DataFrame,
    *,
    question_ids: list[str],
    emails: list[str],
    submission_ids: list[int],
    limit: int,
    offset: int,
    shard_count: int,
    shard_index: int,
) -> pd.DataFrame:
    subset = manifest.copy()
    if question_ids:
        subset = subset[subset["question_id"].isin(question_ids)]
    if emails:
        email_set = {email.strip().lower() for email in emails}
        subset = subset[subset["email"].str.lower().isin(email_set)]
    if submission_ids:
        subset = subset[subset["submission_id"].isin(submission_ids)]
    subset = subset.sort_values(["question_id", "email", "submission_id"]).reset_index(drop=True)
    if shard_count > 1:
        positions = pd.Series(range(len(subset)), index=subset.index)
        subset = subset[(positions % shard_count) == shard_index]
    if offset:
        subset = subset.iloc[offset:]
    if limit:
        subset = subset.head(limit)
    return subset.reset_index(drop=True)


def print_payload(payload: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        typer.echo(orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode("utf-8"))
        return
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            typer.echo(f"{key}:")
            typer.echo(orjson.dumps(value, option=orjson.OPT_INDENT_2).decode("utf-8"))
        else:
            typer.echo(f"{key}: {value}")


def validate_force(force: bool, question_ids: list[str], emails: list[str], submission_ids: list[int], limit: int, offset: int, shard_count: int) -> None:
    if force and not has_force_scope(question_ids, emails, submission_ids, limit, offset, shard_count):
        raise typer.BadParameter("--force requires a narrowing filter such as --question-id, --email, --submission-id, --limit, or sharding options.")


def dry_run_rows(subset: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in subset.itertuples(index=False):
        candidate = pd.Series(row._asdict())
        rows.append(
            {
                "question_id": str(candidate["question_id"]),
                "question_label": QUESTION_LABELS[str(candidate["question_id"])],
                "email": str(candidate["email"]),
                "submission_id": int(candidate["submission_id"]),
                "result_path": str(result_path(candidate)),
            }
        )
    return rows


def safe_question_label(question_id: str) -> str:
    return QUESTION_LABELS.get(question_id, question_id)


def build_progress_payload(
    *,
    run_id: str,
    label: str,
    model: str,
    total_rows: int,
    processed: int,
    evaluated: int,
    skipped_existing: int,
    errors: int,
    started_perf: float,
    started_at_utc: str,
    filters: dict[str, Any],
    current_item: dict[str, Any] | None,
    status: str,
) -> dict[str, Any]:
    elapsed_seconds = perf_counter() - started_perf
    rate_rows_per_second = processed / elapsed_seconds if processed and elapsed_seconds > 0 else 0.0
    remaining_rows = max(total_rows - processed, 0)
    eta_seconds = remaining_rows / rate_rows_per_second if remaining_rows and rate_rows_per_second > 0 else (0.0 if remaining_rows == 0 else None)
    eta_at_utc = (
        (datetime.now(UTC) + timedelta(seconds=eta_seconds)).isoformat()
        if eta_seconds is not None
        else ""
    )
    return {
        "status": status,
        "run_id": run_id,
        "run_label": label,
        "model": model,
        "selected_rows": total_rows,
        "processed": processed,
        "evaluated": evaluated,
        "skipped_existing": skipped_existing,
        "errors": errors,
        "remaining_rows": remaining_rows,
        "started_at_utc": started_at_utc,
        "updated_at_utc": now_utc(),
        "elapsed_seconds": round(elapsed_seconds, 1),
        "elapsed": format_duration(elapsed_seconds),
        "rate_rows_per_minute": round(rate_rows_per_second * 60, 2),
        "eta_seconds": round(eta_seconds, 1) if eta_seconds is not None else None,
        "eta": format_duration(eta_seconds),
        "eta_at_utc": eta_at_utc,
        "filters": filters,
        "current": current_item or {},
    }


def write_progress(progress_path: Path, payload: dict[str, Any], fmt: str) -> None:
    write_json(progress_path, payload)
    if fmt != "text":
        return
    current = payload.get("current") or {}
    current_text = ""
    if current:
        current_text = f" | current={current.get('email', '')}:{current.get('question_id', '')}:{current.get('status', '')}"
    typer.echo(
        "[progress] "
        f"{payload['processed']}/{payload['selected_rows']} "
        f"({(payload['processed'] / payload['selected_rows'] * 100) if payload['selected_rows'] else 100:.1f}%)"
        f" | eval={payload['evaluated']}"
        f" skip={payload['skipped_existing']}"
        f" err={payload['errors']}"
        f" | rate={payload['rate_rows_per_minute']:.2f}/min"
        f" | elapsed={payload['elapsed']}"
        f" | eta={payload['eta']}"
        f"{current_text}"
    )


@app.command()
def main(
    question_ids: list[str] | None = typer.Option(None, "--question-id", help="Filter to one or more q-generate-* question IDs."),
    emails: list[str] | None = typer.Option(None, "--email", help="Filter to one or more student emails."),
    submission_ids: list[int] | None = typer.Option(None, "--submission-id", help="Filter to specific submission IDs."),
    limit: int = typer.Option(0, "--limit", min=0, help="Evaluate at most this many selected rows."),
    offset: int = typer.Option(0, "--offset", min=0, help="Skip this many selected rows before processing."),
    shard_count: int = typer.Option(1, "--shard-count", min=1, help="Split the filtered rows into N shards."),
    shard_index: int = typer.Option(0, "--shard-index", min=0, help="Process only shard K out of --shard-count."),
    run_label: str = typer.Option("", "--run-label", help="Optional label for the saved run summary."),
    force: bool = typer.Option(False, "--force", help="Re-evaluate existing successful outputs for the filtered subset."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would run without calling Gemini or writing files."),
    params: str = typer.Option("", "--params", help="JSON object or path to JSON containing CLI parameters."),
    progress_every: int = typer.Option(25, "--progress-every", min=1, help="Write progress and ETA every N processed rows."),
    progress_path: Path = typer.Option(PROGRESS_PATH, "--progress-path", help="Path to the live progress JSON file."),
    fmt: str = typer.Option("auto", "--format", "--output", help="Output format: auto, json, or text."),
    json_output: bool = typer.Option(False, "--json", help="Alias for --format json."),
    describe: bool = typer.Option(False, "--describe", help="Print machine-readable command metadata and exit."),
) -> None:
    """Evaluate q-generate submissions with Gemini using the question-authored evaluation prompts."""

    if describe:
        print_payload(describe_payload(), output_format(fmt, json_output))
        raise typer.Exit()

    params_payload = load_params_value(params)
    question_filter_supplied = bool(question_ids or params_payload.get("question_ids"))
    resolved_question_ids = normalize_question_ids(resolve_sequence(question_ids, params_payload, "question_ids"))
    resolved_emails = [str(value) for value in resolve_sequence(emails, params_payload, "emails")]
    resolved_submission_ids = [int(value) for value in resolve_sequence(submission_ids, params_payload, "submission_ids")]
    resolved_limit = int(resolve_option(limit, params_payload, "limit", 0) or 0)
    resolved_offset = int(resolve_option(offset, params_payload, "offset", 0) or 0)
    resolved_shard_count = int(resolve_option(shard_count, params_payload, "shard_count", 1) or 1)
    resolved_shard_index = int(resolve_option(shard_index, params_payload, "shard_index", 0) or 0)
    resolved_run_label = str(resolve_option(run_label, params_payload, "run_label", "") or "")
    resolved_force = bool(resolve_option(force, params_payload, "force", False))
    resolved_dry_run = bool(resolve_option(dry_run, params_payload, "dry_run", False))
    resolved_progress_every = int(resolve_option(progress_every, params_payload, "progress_every", 25) or 25)
    resolved_progress_path = Path(str(resolve_option(str(progress_path), params_payload, "progress_path", str(PROGRESS_PATH))))
    if resolved_shard_index >= resolved_shard_count:
        raise typer.BadParameter("--shard-index must be less than --shard-count.")
    validate_force(
        resolved_force,
        resolved_question_ids if question_filter_supplied else [],
        resolved_emails,
        resolved_submission_ids,
        resolved_limit,
        resolved_offset,
        resolved_shard_count,
    )

    manifest = load_manifest()
    subset = manifest_subset(
        manifest,
        question_ids=resolved_question_ids,
        emails=resolved_emails,
        submission_ids=resolved_submission_ids,
        limit=resolved_limit,
        offset=resolved_offset,
        shard_count=resolved_shard_count,
        shard_index=resolved_shard_index,
    )

    fmt_resolved = output_format(fmt, json_output)
    planned = {
        "selected_rows": int(len(subset)),
        "question_ids": resolved_question_ids,
        "emails": resolved_emails,
        "submission_ids": resolved_submission_ids,
        "limit": resolved_limit,
        "offset": resolved_offset,
        "shard_count": resolved_shard_count,
        "shard_index": resolved_shard_index,
        "force": resolved_force,
        "dry_run": resolved_dry_run,
        "output_root": str(OUTPUT_ROOT),
        "model": MODEL_NAME,
        "progress_path": str(resolved_progress_path),
        "progress_every": resolved_progress_every,
    }
    if resolved_dry_run:
        planned["rows"] = dry_run_rows(subset.head(20))
        if len(subset) > 20:
            planned["rows_truncated"] = True
        print_payload(planned, fmt_resolved)
        raise typer.Exit()

    ensure_dir(OUTPUT_ROOT)
    ensure_dir(RUNS_DIR)
    ensure_dir(RESULTS_DIR)
    ensure_dir(RESIZED_DIR)

    api_key = load_api_key()
    if not api_key:
        raise typer.BadParameter("GEMINI_API_KEY is required. Put it in .env or export it in the environment.")

    client = genai.Client(api_key=api_key)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    label = safe_slug(resolved_run_label) if resolved_run_label else "batch"
    run_path = RUNS_DIR / f"{run_id}--{label}.json"
    started_at_utc = now_utc()
    started_perf = perf_counter()
    filters_payload = {
        "question_ids": resolved_question_ids,
        "emails": resolved_emails,
        "submission_ids": resolved_submission_ids,
        "limit": resolved_limit,
        "offset": resolved_offset,
        "shard_count": resolved_shard_count,
        "shard_index": resolved_shard_index,
        "force": resolved_force,
    }

    processed = 0
    evaluated = 0
    skipped_existing = 0
    errors = 0
    results_for_run: list[dict[str, Any]] = []
    ensure_dir(resolved_progress_path.parent)
    write_progress(
        resolved_progress_path,
        build_progress_payload(
            run_id=run_id,
            label=label,
            model=MODEL_NAME,
            total_rows=int(len(subset)),
            processed=0,
            evaluated=0,
            skipped_existing=0,
            errors=0,
            started_perf=started_perf,
            started_at_utc=started_at_utc,
            filters=filters_payload,
            current_item=None,
            status="running",
        ),
        fmt_resolved,
    )

    for row in subset.itertuples(index=False):
        processed += 1
        series = pd.Series(row._asdict())
        output_path = result_path(series)
        current_item: dict[str, Any] = {
            "email": str(series["email"]),
            "question_id": str(series["question_id"]),
            "submission_id": int(series["submission_id"]),
            "status": "started",
        }
        if output_path.exists() and not resolved_force:
            existing = read_json(output_path)
            if isinstance(existing, dict) and existing.get("status") == "ok":
                skipped_existing += 1
                results_for_run.append(
                    {
                        "question_id": str(series["question_id"]),
                        "email": str(series["email"]),
                        "submission_id": int(series["submission_id"]),
                        "status": "skipped-existing",
                        "result_path": str(output_path),
                    }
                )
                current_item["status"] = "skipped-existing"
                if processed % resolved_progress_every == 0 or processed == len(subset):
                    write_progress(
                        resolved_progress_path,
                        build_progress_payload(
                            run_id=run_id,
                            label=label,
                            model=MODEL_NAME,
                            total_rows=int(len(subset)),
                            processed=processed,
                            evaluated=evaluated,
                            skipped_existing=skipped_existing,
                            errors=errors,
                            started_perf=started_perf,
                            started_at_utc=started_at_utc,
                            filters=filters_payload,
                            current_item=current_item,
                            status="running",
                        ),
                        fmt_resolved,
                    )
                continue

        question_id = str(series["question_id"])
        try:
            source_image_path = resolve_existing_path(str(series["image_path"]))
            image_bytes, mime_type, image_meta = open_and_resize_image(source_image_path)
            resized_output_path = resized_path(series, image_meta["suffix"])
            if not resized_output_path.exists() or resolved_force:
                write_resized_copy(resized_output_path, image_bytes)

            system_prompt, user_prompt, prompt_values = build_prompts(series)
            response = call_gemini(
                client,
                image_bytes=image_bytes,
                mime_type=mime_type,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=RESPONSE_SCHEMAS[question_id],
            )
            parsed_response = parse_response_json(response)
            payload = {
                "status": "ok",
                "question_id": question_id,
                "question_label": safe_question_label(question_id),
                "email": str(series["email"]),
                "submission_id": int(series["submission_id"]),
                "model": MODEL_NAME,
                "evaluated_at_utc": now_utc(),
                "source": {
                    "image_path": str(source_image_path),
                    "manifest_row": {
                        key: format_choice(series[key])
                        for key in [
                            "image_url",
                            "json_url",
                            "model",
                            "dataset_name",
                            "dataset_url",
                            "insight",
                            "concept",
                            "metaphor",
                            "tradition_name",
                            "tradition_period",
                            "tradition_approach",
                            "paradox",
                            "visual_logic",
                        ]
                        if key in series.index
                    },
                },
                "image": {
                    "resized_path": str(resized_output_path),
                    **image_meta,
                },
                "request": {
                    "system_instruction": system_prompt,
                    "user_message": user_prompt,
                    "response_json_schema": RESPONSE_SCHEMAS[question_id],
                    "prompt_values": prompt_values,
                },
                "response": parsed_response,
                "api_response": serialize_response(response),
            }
            write_json(output_path, payload)
            evaluated += 1
            current_item["status"] = "ok"
            results_for_run.append(
                {
                    "question_id": question_id,
                    "email": str(series["email"]),
                    "submission_id": int(series["submission_id"]),
                    "status": "ok",
                    "overall_score": parsed_response.get("overall_score"),
                    "result_path": str(output_path),
                }
            )
        except Exception as exc:  # noqa: BLE001
            errors += 1
            current_item["status"] = "error"
            current_item["error"] = str(exc)
            error_payload = {
                "status": "error",
                "question_id": question_id,
                "question_label": safe_question_label(question_id),
                "email": str(series["email"]),
                "submission_id": int(series["submission_id"]),
                "model": MODEL_NAME,
                "evaluated_at_utc": now_utc(),
                "api_error": str(exc),
            }
            write_json(output_path, error_payload)
            results_for_run.append(
                {
                    "question_id": question_id,
                    "email": str(series["email"]),
                    "submission_id": int(series["submission_id"]),
                    "status": "error",
                    "error": str(exc),
                    "result_path": str(output_path),
                }
            )
        if processed % resolved_progress_every == 0 or processed == len(subset):
            write_progress(
                resolved_progress_path,
                build_progress_payload(
                    run_id=run_id,
                    label=label,
                    model=MODEL_NAME,
                    total_rows=int(len(subset)),
                    processed=processed,
                    evaluated=evaluated,
                    skipped_existing=skipped_existing,
                    errors=errors,
                    started_perf=started_perf,
                    started_at_utc=started_at_utc,
                    filters=filters_payload,
                    current_item=current_item,
                    status="running",
                ),
                fmt_resolved,
            )

    aggregate_summary = write_aggregate_summaries()
    run_summary = {
        "run_id": run_id,
        "run_label": label,
        "model": MODEL_NAME,
        "selected_rows": int(len(subset)),
        "processed": processed,
        "evaluated": evaluated,
        "skipped_existing": skipped_existing,
        "errors": errors,
        "filters": filters_payload,
        "results": results_for_run,
        "aggregate_summary": aggregate_summary,
        "generated_at_utc": now_utc(),
        "progress_path": str(resolved_progress_path),
    }
    write_json(run_path, run_summary)
    write_progress(
        resolved_progress_path,
        build_progress_payload(
            run_id=run_id,
            label=label,
            model=MODEL_NAME,
            total_rows=int(len(subset)),
            processed=processed,
            evaluated=evaluated,
            skipped_existing=skipped_existing,
            errors=errors,
            started_perf=started_perf,
            started_at_utc=started_at_utc,
            filters=filters_payload,
            current_item={"status": "completed"},
            status="completed",
        ),
        "json",
    )
    run_summary["run_path"] = str(run_path)
    print_payload(run_summary, fmt_resolved)


if __name__ == "__main__":
    app()
