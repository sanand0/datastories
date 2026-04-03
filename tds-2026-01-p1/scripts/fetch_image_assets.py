#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.28",
#   "orjson>=3.10",
#   "pandas>=2.2",
#   "pillow>=11.2",
#   "pillow-avif-plugin>=1.5.2",
#   "pyarrow>=20.0",
#   "rich>=14.0",
#   "tenacity>=9.1",
#   "typer>=0.16",
# ]
# ///

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any
from urllib.parse import urlparse

import httpx
import orjson
import pandas as pd
import pillow_avif  # noqa: F401
from PIL import ExifTags, Image
from rich.traceback import install
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
import typer

from tds_p1_common import (
    ASSETS_DIR,
    DERIVED_DIR,
    IMAGE_QUESTION_IDS,
    QUESTION_LABELS,
    ensure_dir,
    parse_submission_urls,
    stable_name,
)

install(show_locals=True)

app = typer.Typer(add_completion=False)
Image.MAX_IMAGE_PIXELS = None

EXIF_TAGS = {value: key for key, value in ExifTags.TAGS.items()}
MIME_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/avif": ".avif",
}


@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def fetch_bytes(client: httpx.Client, url: str) -> httpx.Response:
    response = client.get(url)
    response.raise_for_status()
    return response


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def extension_for(url: str, content_type: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".avif"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return MIME_EXTENSIONS.get(content_type.split(";")[0].strip().lower(), ".bin")


def fetch_to_path(client: httpx.Client, url: str, path: Path) -> tuple[int, str]:
    if path.exists() and path.stat().st_size > 0:
        return path.stat().st_size, ""
    response = fetch_bytes(client, url)
    ensure_dir(path.parent)
    path.write_bytes(response.content)
    content_type = response.headers.get("content-type", "")
    return len(response.content), content_type


def open_image_metadata(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        exif = image.getexif()
        software = exif.get(EXIF_TAGS.get("Software"), "") if exif else ""
        user_comment = exif.get(EXIF_TAGS.get("UserComment"), "") if exif else ""
        description = exif.get(EXIF_TAGS.get("ImageDescription"), "") if exif else ""
        return {
            "image_format": image.format or "",
            "image_mode": image.mode,
            "image_width": int(image.width),
            "image_height": int(image.height),
            "short_side": int(min(image.width, image.height)),
            "long_side": int(max(image.width, image.height)),
            "aspect_ratio": round(image.width / image.height, 4) if image.height else None,
            "metadata_keys": ",".join(sorted(str(key) for key in image.info.keys())),
            "software": str(software)[:500],
            "description": str(description)[:500],
            "parameters": str(image.info.get("parameters", ""))[:1000],
            "comment": str(image.info.get("comment", ""))[:1000],
            "user_comment": str(user_comment)[:1000],
        }


def create_thumbnail(image_path: Path, thumb_path: Path) -> None:
    if thumb_path.exists():
        return
    ensure_dir(thumb_path.parent)
    with tempfile.TemporaryDirectory() as tmp_dir:
        resized = Path(tmp_dir) / "resized.png"
        subprocess.run(
            [
                "magick",
                str(image_path),
                "-auto-orient",
                "-strip",
                "-resize",
                "640x640>",
                str(resized),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                "avifenc",
                "-q",
                "30",
                "--jobs",
                "all",
                str(resized),
                str(thumb_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )


def extract_prompt_features(prompt: str) -> dict[str, Any]:
    text = prompt or ""
    lower = text.lower()
    return {
        "prompt_chars": len(text),
        "prompt_words": len([word for word in text.split() if word]),
        "prompt_commas": text.count(","),
        "has_negative_prompt": any(
            token in lower for token in ["negative prompt", "negative_prompts", "negative:", "--no", "avoid text"]
        ),
        "has_generation_params": bool(
            re.search(
                r"--[a-z]+|\bseed\b|\bsteps\b|\bcfg\b|\baspect ratio\b|\bar\b|\bstylize\b|\bchaos\b",
                lower,
            )
        ),
        "has_style_reference": any(
            token in lower
            for token in ["in the style of", "style:", "ukiyo", "bauhaus", "constructiv", "engraving", "cinematic"]
        ),
    }


def process_row(row: dict[str, Any], client: httpx.Client) -> dict[str, Any]:
    question_dir = ensure_dir(ASSETS_DIR / row["question_id"])
    answer = str(row.get("answer_text") or "")
    parsed = parse_submission_urls(answer)
    base_name = stable_name(row["submission_id"], row["question_id"])
    record: dict[str, Any] = {
        "submission_id": int(row["submission_id"]),
        "email": row["email"],
        "question_id": row["question_id"],
        "question_label": QUESTION_LABELS[row["question_id"]],
        "score": float(row["score"]),
        "image_url": "",
        "json_url": "",
        "image_host": "",
        "json_host": "",
        "status": "blank-answer",
        "image_path": "",
        "json_path": "",
        "thumbnail_path": "",
        "image_fetch_error": "",
        "json_fetch_error": "",
        "thumbnail_error": "",
        "json_parse_error": "",
        "image_bytes": 0,
        "json_bytes": 0,
        "image_sha256": "",
        "publish_email": False,
        "prompt": "",
        "model": "",
        "dataset_name": "",
        "dataset_url": "",
        "insight": "",
        "concept": "",
        "metaphor": "",
        "tradition_name": "",
        "tradition_period": "",
        "tradition_approach": "",
        "paradox": "",
        "visual_logic": "",
        "image_format": "",
        "image_mode": "",
        "image_width": None,
        "image_height": None,
        "short_side": None,
        "long_side": None,
        "aspect_ratio": None,
        "metadata_keys": "",
        "software": "",
        "description": "",
        "parameters": "",
        "comment": "",
        "user_comment": "",
        "prompt_chars": 0,
        "prompt_words": 0,
        "prompt_commas": 0,
        "has_negative_prompt": False,
        "has_generation_params": False,
        "has_style_reference": False,
    }
    if not parsed:
        record["status"] = "invalid-answer-format"
        return record

    image_url, json_url = parsed
    record["image_url"] = image_url
    record["json_url"] = json_url
    record["image_host"] = urlparse(image_url).netloc
    record["json_host"] = urlparse(json_url).netloc

    image_path = question_dir / f"{base_name}{extension_for(image_url, '')}"
    json_path = question_dir / f"{base_name}-submission.json"
    thumb_path = question_dir / f"{base_name}-thumb.avif"
    record["image_path"] = str(image_path.relative_to(ASSETS_DIR.parent))
    record["json_path"] = str(json_path.relative_to(ASSETS_DIR.parent))
    record["thumbnail_path"] = str(thumb_path.relative_to(ASSETS_DIR.parent))

    try:
        record["image_bytes"], image_content_type = fetch_to_path(client, image_url, image_path)
        if image_path.suffix == ".bin":
            renamed_path = image_path.with_suffix(extension_for(image_url, image_content_type))
            image_path.rename(renamed_path)
            image_path = renamed_path
            record["image_path"] = str(image_path.relative_to(ASSETS_DIR.parent))
    except Exception as exc:  # noqa: BLE001
        record["status"] = "image-fetch-error"
        record["image_fetch_error"] = str(exc)
        return record

    try:
        record["json_bytes"], _ = fetch_to_path(client, json_url, json_path)
        payload = orjson.loads(json_path.read_bytes())
    except Exception:
        try:
            json_path.unlink(missing_ok=True)
            record["json_bytes"], _ = fetch_to_path(client, json_url, json_path)
            payload = orjson.loads(json_path.read_bytes())
        except Exception as exc:  # noqa: BLE001
            record["status"] = "json-fetch-error"
            record["json_fetch_error"] = str(exc)
            return record

    if not isinstance(payload, dict):
        record["status"] = "json-parse-error"
        record["json_parse_error"] = "Submission JSON is not an object"
        return record

    prompt = str(payload.get("prompt", ""))
    record.update(
        {
            "publish_email": bool(payload.get("publish_email", False)),
            "prompt": prompt,
            "model": str(payload.get("model", "")),
            "dataset_name": str(payload.get("dataset_name", "")),
            "dataset_url": str(payload.get("dataset_url", "")),
            "insight": str(payload.get("insight", "")),
            "concept": str(payload.get("concept", "")),
            "metaphor": str(payload.get("metaphor", "")),
            "tradition_name": str(payload.get("tradition_name", "")),
            "tradition_period": str(payload.get("tradition_period", "")),
            "tradition_approach": str(payload.get("tradition_approach", "")),
            "paradox": str(payload.get("paradox", "")),
            "visual_logic": str(payload.get("visual_logic", "")),
            **extract_prompt_features(prompt),
        }
    )

    try:
        record.update(open_image_metadata(image_path))
        record["image_sha256"] = file_sha256(image_path)
    except Exception as exc:  # noqa: BLE001
        record["status"] = "image-metadata-error"
        record["image_fetch_error"] = str(exc)
        return record

    try:
        create_thumbnail(image_path, thumb_path)
    except Exception as exc:  # noqa: BLE001
        record["thumbnail_error"] = str(exc)
        record["status"] = "thumbnail-error"
        return record

    record["status"] = "ok"
    return record


@app.command()
def main() -> None:
    """Download latest image submissions, fetch JSON metadata, and build AVIF thumbnails."""

    latest_positive = pd.read_parquet(DERIVED_DIR / "latest_positive.parquet")
    attempts = pd.read_parquet(DERIVED_DIR / "question_attempts.parquet")
    latest_ids = set(latest_positive["submission_id"].astype(int).tolist())
    image_rows = attempts[
        attempts["submission_id"].isin(latest_ids)
        & attempts["question_id"].isin(IMAGE_QUESTION_IDS)
        & attempts["has_answer"]
    ].copy()
    if image_rows.empty:
        raise typer.BadParameter("No latest image answers found. Run normalize_submissions.py first.")

    ensure_dir(ASSETS_DIR)
    rows = image_rows.to_dict(orient="records")
    manifest_rows: list[dict[str, Any]] = []
    with httpx.Client(timeout=90, follow_redirects=True, headers={"User-Agent": "tds-p1-image-fetch"}) as client:
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(process_row, row, client) for row in rows]
            for index, future in enumerate(as_completed(futures), start=1):
                manifest_rows.append(future.result())
                if index % 50 == 0 or index == len(rows):
                    typer.echo(f"[images] processed {index}/{len(rows)}")

    manifest = pd.DataFrame.from_records(manifest_rows).sort_values(["question_id", "submission_id"])
    manifest.to_parquet(DERIVED_DIR / "image_manifest.parquet", index=False)
    typer.echo(
        "[images] done: "
        + str(manifest["status"].value_counts().to_dict())
    )


if __name__ == "__main__":
    app()
