from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import re
import tempfile
from typing import Any

import orjson

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DERIVED_DIR = DATA_DIR / "derived"
ASSETS_DIR = DATA_DIR / "assets"
ANALYSIS_DIR = ROOT / "analysis"
HISTORY_PAGES_DIR = RAW_DIR / "history-pages"
HISTORY_URL = "https://exam.sanand.workers.dev/filter"
QUIZ_ID = "tds-2026-01-p1"
LOCAL_DUMP_PATH = Path("/home/sanand/code/exam/dumps/tds-2026-01-p1.json")
DEADLINE_UTC = datetime(2026, 3, 30, 18, 29, 59, tzinfo=UTC)

QUESTION_IDS = [
    "q-share-secret-server",
    "q-transcribe-numbers-server",
    "q-pr-merge-server",
    "q-markdown-parser-server",
    "q-generate-affective-chart",
    "q-generate-concept-incarnation",
    "q-generate-style-transplant",
    "q-generate-paradox-portrait",
    "q-network-game-labyrinth",
    "q-network-game-detective",
    "q-network-game-signal",
]

IMAGE_QUESTION_IDS = [
    "q-generate-affective-chart",
    "q-generate-concept-incarnation",
    "q-generate-style-transplant",
    "q-generate-paradox-portrait",
]

QUESTION_LABELS = {
    "q-share-secret-server": "Share Secret",
    "q-transcribe-numbers-server": "Transcribe Numbers",
    "q-pr-merge-server": "PR Merge",
    "q-markdown-parser-server": "Markdown Parser",
    "q-generate-affective-chart": "Affective Chart",
    "q-generate-concept-incarnation": "Concept Incarnation",
    "q-generate-style-transplant": "Style Transplant",
    "q-generate-paradox-portrait": "Paradox Portrait",
    "q-network-game-labyrinth": "Data Labyrinth",
    "q-network-game-detective": "Graph Detective",
    "q-network-game-signal": "The Signal",
}


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path) -> Any:
    return orjson.loads(path.read_bytes())


def write_json(path: Path, payload: Any, *, compact: bool = False) -> None:
    ensure_dir(path.parent)
    option = orjson.OPT_SORT_KEYS | (0 if compact else orjson.OPT_INDENT_2)
    data = orjson.dumps(payload, option=option)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        handle.write(data)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def load_rows_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"]
    if isinstance(payload, list):
        return payload
    raise TypeError("Unsupported payload shape")


def history_page_paths() -> list[Path]:
    return sorted(HISTORY_PAGES_DIR.glob("page-*.json"))


def load_history_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in history_page_paths():
        rows.extend(load_rows_from_payload(read_json(path)))
    return rows


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def stable_name(*parts: Any) -> str:
    return "-".join(safe_slug(str(part)) for part in parts if str(part).strip())


def sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def parse_submission_urls(value: str | None) -> tuple[str, str] | None:
    urls = re.split(r"\s+", str(value or "").strip())
    urls = [url for url in urls if url]
    if len(urls) != 2:
        return None
    return urls[0], urls[1]


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    def escape(value: Any) -> str:
        text = "" if value is None else str(value)
        return text.replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(escape(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)
