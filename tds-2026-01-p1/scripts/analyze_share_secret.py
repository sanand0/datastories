#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.28",
#   "orjson>=3.10",
#   "pandas>=2.2",
#   "pyarrow>=20.0",
#   "rich>=14.0",
#   "tenacity>=9.1",
#   "typer>=0.16",
# ]
# ///

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import math
import re
from typing import Any

import httpx
import pandas as pd
from rich.traceback import install
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
import typer

from tds_p1_common import DERIVED_DIR, RAW_DIR, ensure_dir, write_json

install(show_locals=True)

app = typer.Typer(add_completion=False)

QUESTION_ID = "q-share-secret-server"
DECODER_URL = "https://tds-hackkkkkkk.vercel.app/api/solve"
DISCUSSION_URL = "https://github.com/sanand0/tools-in-data-science-public/discussions/277"
IST = "Asia/Kolkata"
AGENT_ID_RE = re.compile(r"\d+")


def normalize_agent_id(value: Any) -> str:
    match = AGENT_ID_RE.search(str(value or ""))
    if not match:
        return ""
    return f"{int(match.group(0)):03d}"


def normalize_email(value: Any) -> str:
    return str(value or "").strip().lower()


def parse_submission(text: str) -> list[dict[str, str]]:
    raw = str(text or "").strip()
    if not raw:
        return []
    try:
        payload = __import__("orjson").loads(raw)
    except Exception:  # noqa: BLE001
        return []
    rows = payload.get("agents") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []
    agents: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        agent_id = normalize_agent_id(
            row.get("agent_id") or row.get("agentId") or row.get("agent") or row.get("id")
        )
        email = normalize_email(row.get("email") or row.get("email_id") or row.get("emailId"))
        password = str(row.get("password") or row.get("pass") or "").strip().lower()
        if agent_id and email and password:
            agents.append({"agent_id": agent_id, "email": email, "password": password})
    return agents


@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def decoder_request(client: httpx.Client, agent_ids: list[str]) -> list[dict[str, Any]]:
    response = client.post(DECODER_URL, json={"agents": agent_ids})
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise TypeError("Decoder returned non-list payload")
    return payload


def fetch_decoder_map(force: bool) -> dict[str, dict[str, str]]:
    decoder_dir = ensure_dir(RAW_DIR / "share-secret-decoder")
    compiled_path = decoder_dir / "agent-map.json"
    if compiled_path.exists() and not force:
        return __import__("orjson").loads(compiled_path.read_bytes())

    mapping: dict[str, dict[str, str]] = {}
    ids = [f"{i:03d}" for i in range(100)]
    chunk_count = math.ceil(len(ids) / 3)
    with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "tds-p1-share-secret"}) as client:
        for chunk_index in range(chunk_count):
            start = chunk_index * 3
            chunk = ids[start : start + 3]
            if len(chunk) < 3:
                chunk = chunk + ids[: 3 - len(chunk)]
            payload = decoder_request(client, chunk)
            write_json(decoder_dir / f"chunk-{chunk_index:03d}.json", payload)
            for row in payload:
                agent_id = normalize_agent_id(row.get("agent_id"))
                email = normalize_email(row.get("email"))
                password = str(row.get("password") or "").strip().lower()
                if agent_id and email and password:
                    mapping[agent_id] = {"email": email, "password": password}
    write_json(compiled_path, mapping)
    return mapping


@app.command()
def main(force_decoder_fetch: bool = False) -> None:
    """Build share-secret diffusion and standardized-decoder metrics."""

    attempts = pd.read_parquet(DERIVED_DIR / "question_attempts.parquet")
    subset = attempts[
        (attempts["question_id"] == QUESTION_ID)
        & (attempts["score"] > 0)
        & (attempts["has_answer"])
    ].copy()
    if subset.empty:
        raise typer.BadParameter("No successful share-secret rows found.")

    parsed_rows: list[dict[str, Any]] = []
    flat_rows: list[dict[str, Any]] = []
    for row in subset.itertuples(index=False):
        agents = parse_submission(row.answer_text)
        if not agents:
            continue
        sorted_agents = sorted(agents, key=lambda agent: (agent["agent_id"], agent["email"]))
        signature = " | ".join(f"{agent['agent_id']}:{agent['email']}" for agent in sorted_agents)
        parsed_rows.append(
            {
                "submission_id": int(row.submission_id),
                "solver_email": row.email,
                "submitted_at_utc": pd.Timestamp(row.submitted_at_utc),
                "agent_count": len(agents),
                "signature": signature,
                "answer_text": row.answer_text,
            }
        )
        for agent in agents:
            flat_rows.append(
                {
                    "submission_id": int(row.submission_id),
                    "solver_email": row.email,
                    "submitted_at_utc": pd.Timestamp(row.submitted_at_utc),
                    "agent_id": agent["agent_id"],
                    "target_email": agent["email"],
                    "password": agent["password"],
                }
            )

    parsed = pd.DataFrame.from_records(parsed_rows).sort_values(["solver_email", "submitted_at_utc", "submission_id"])
    flat = pd.DataFrame.from_records(flat_rows).sort_values(["solver_email", "submitted_at_utc", "submission_id", "agent_id"])
    first_success = parsed.groupby("solver_email", as_index=False).head(1).copy()
    first_success_ids = set(first_success["submission_id"].astype(int).tolist())
    first_success_flat = flat[flat["submission_id"].isin(first_success_ids)].copy()

    decoder_map = fetch_decoder_map(force_decoder_fetch)
    decoder_frame = pd.DataFrame(
        [
            {"agent_id": agent_id, "decoder_email": payload["email"], "decoder_password": payload["password"]}
            for agent_id, payload in sorted(decoder_map.items())
        ]
    )

    dominant = (
        first_success_flat.groupby(["agent_id", "target_email"])
        .size()
        .reset_index(name="uses")
        .sort_values(["agent_id", "uses", "target_email"], ascending=[True, False, True])
    )
    dominant["distinct_emails_for_agent"] = dominant.groupby("agent_id")["target_email"].transform("nunique")
    dominant["total_uses_for_agent"] = dominant.groupby("agent_id")["uses"].transform("sum")
    dominant["rank"] = dominant.groupby("agent_id").cumcount() + 1
    dominant["top_share"] = dominant["uses"] / dominant["total_uses_for_agent"]
    top_choices = dominant[dominant["rank"] == 1].merge(decoder_frame, on="agent_id", how="left")
    top_choices["decoder_matches_top_email"] = top_choices["target_email"] == top_choices["decoder_email"]

    first_success_flat = first_success_flat.merge(decoder_frame, on="agent_id", how="left")
    first_success_flat["decoder_email_match"] = first_success_flat["target_email"] == first_success_flat["decoder_email"]
    student_match = (
        first_success_flat.groupby(["submission_id", "solver_email", "submitted_at_utc"])
        .agg(
            decoder_match_count=("decoder_email_match", "sum"),
            agent_rows=("agent_id", "size"),
        )
        .reset_index()
    )
    student_match["decoder_match_share"] = student_match["decoder_match_count"] / student_match["agent_rows"]
    student_match["all_three_match_decoder"] = student_match["decoder_match_count"] == student_match["agent_rows"]
    student_match["ist_day"] = student_match["submitted_at_utc"].dt.tz_convert(IST).dt.strftime("%Y-%m-%d")

    first_success = first_success.merge(
        student_match[
            [
                "submission_id",
                "decoder_match_count",
                "decoder_match_share",
                "all_three_match_decoder",
                "ist_day",
            ]
        ],
        on="submission_id",
        how="left",
    )
    first_success = first_success.sort_values("submitted_at_utc").reset_index(drop=True)
    first_success["solve_order"] = first_success.index + 1

    early_100 = first_success.head(100)
    late_100 = first_success.tail(100)
    first_week_cutoff = pd.Timestamp("2026-02-18T00:00:00+05:30").tz_convert("UTC")
    last_week_cutoff = pd.Timestamp("2026-03-24T00:00:00+05:30").tz_convert("UTC")
    first_week = first_success[first_success["submitted_at_utc"] < first_week_cutoff]
    last_week = first_success[first_success["submitted_at_utc"] >= last_week_cutoff]

    daily = (
        first_success.groupby("ist_day")
        .agg(
            first_successes=("submission_id", "size"),
            decoder_exact_matches=("all_three_match_decoder", "sum"),
        )
        .reset_index()
        .sort_values("ist_day")
    )
    daily["decoder_exact_match_share"] = daily["decoder_exact_matches"] / daily["first_successes"]

    triplets = (
        first_success.groupby("signature")
        .size()
        .reset_index(name="students")
        .sort_values(["students", "signature"], ascending=[False, True])
    )

    summary = {
        "successful_rows": int(len(parsed)),
        "successful_students": int(first_success["solver_email"].nunique()),
        "agent_ids_with_decoder_map": int(len(decoder_map)),
        "agent_ids_with_top_choice": int(len(top_choices)),
        "agent_ids_where_decoder_matches_top_email": int(top_choices["decoder_matches_top_email"].sum()),
        "decoder_match_rate_agent_ids": round(
            float(top_choices["decoder_matches_top_email"].mean() * 100), 2
        )
        if not top_choices.empty
        else 0.0,
        "students_all_three_match_decoder": int(first_success["all_three_match_decoder"].sum()),
        "students_all_three_match_decoder_rate": round(
            float(first_success["all_three_match_decoder"].mean() * 100), 2
        ),
        "early_100_exact_decoder_rate": round(
            float(early_100["all_three_match_decoder"].mean() * 100), 2
        )
        if not early_100.empty
        else 0.0,
        "late_100_exact_decoder_rate": round(
            float(late_100["all_three_match_decoder"].mean() * 100), 2
        )
        if not late_100.empty
        else 0.0,
        "first_week_exact_decoder_rate": round(
            float(first_week["all_three_match_decoder"].mean() * 100), 2
        )
        if not first_week.empty
        else 0.0,
        "last_week_exact_decoder_rate": round(
            float(last_week["all_three_match_decoder"].mean() * 100), 2
        )
        if not last_week.empty
        else 0.0,
        "peak_day": daily.sort_values(["first_successes", "ist_day"], ascending=[False, True]).iloc[0]["ist_day"],
        "peak_day_first_successes": int(
            daily.sort_values(["first_successes", "ist_day"], ascending=[False, True]).iloc[0]["first_successes"]
        ),
        "cross_student_duplicate_signatures": int((triplets["students"] > 1).sum()),
        "top_discussion_url": DISCUSSION_URL,
        "decoder_source_url": DECODER_URL,
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }

    first_success.to_parquet(DERIVED_DIR / "share_secret_first_success.parquet", index=False)
    first_success_flat.to_parquet(DERIVED_DIR / "share_secret_first_success_flat.parquet", index=False)
    top_choices.to_parquet(DERIVED_DIR / "share_secret_top_choices.parquet", index=False)
    daily.to_parquet(DERIVED_DIR / "share_secret_daily.parquet", index=False)
    triplets.to_parquet(DERIVED_DIR / "share_secret_triplets.parquet", index=False)
    write_json(DERIVED_DIR / "share_secret_summary.json", summary)
    typer.echo(f"[share-secret] done: {summary}")


if __name__ == "__main__":
    app()
