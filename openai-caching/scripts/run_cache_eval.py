#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer>=0.12",
#     "tiktoken>=0.7",
#     "orjson>=3.9",
# ]
# ///

from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence

import orjson
import typer
import tiktoken


app = typer.Typer(help="Hybrid prompt caching evaluation harness.")


API_URL = "https://api.openai.com/v1/chat/completions"
SYSTEM_PROMPT = "Summarize into one sentence."
TOKEN_POOL_TARGET = 5000
SEGMENT_TOKEN_LENGTH = 128
TARGET_TOTAL_TOKENS = {
    "approx_1040": 1100,
    "approx_2048": 2050,
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_token_pool(encoding: tiktoken.Encoding, total_tokens: int) -> List[int]:
    ids: List[int] = []
    index = 1
    while len(ids) < total_tokens:
        chunk = f"word{index:04d} "
        ids.extend(encoding.encode(chunk))
        index += 1
    return ids


def decode_slice(
    encoding: tiktoken.Encoding, token_ids: Sequence[int], start: int, end: int
) -> str:
    return encoding.decode(token_ids[start:end])


def chunk_segments(
    encoding: tiktoken.Encoding,
    token_ids: Sequence[int],
    segment_length: int,
) -> List[str]:
    segments: List[str] = []
    for start in range(0, len(token_ids), segment_length):
        end = min(start + segment_length, len(token_ids))
        segments.append(decode_slice(encoding, token_ids, start, end))
    return segments


def count_chat_tokens(
    encoding: tiktoken.Encoding,
    messages: Sequence[Dict[str, str]],
) -> int:
    tokens_per_message = 3
    tokens_per_name = 1
    total = 0
    for message in messages:
        total += tokens_per_message
        total += len(encoding.encode(message["content"]))
        if message.get("name"):
            total += tokens_per_name
    total += 3
    return total


def format_curl_command(api_key: str) -> List[str]:
    return [
        "curl",
        "-sS",
        "-D",
        "-",
        "-H",
        f"Authorization: Bearer {api_key}",
        "-H",
        "Content-Type: application/json",
        API_URL,
        "--data-binary",
        "@-",
    ]


def parse_response(stdout: bytes) -> Dict[str, object]:
    text = stdout.decode("utf-8", errors="replace")
    separator = "\r\n\r\n"
    if separator not in text:
        separator = "\n\n"
    if separator not in text:
        return {
            "raw": text,
            "error": "Unable to split response headers/body",
        }
    header_blob, body_blob = text.split(separator, 1)
    headers = []
    status = None
    for line in header_blob.splitlines():
        if not line:
            continue
        if line.lower().startswith("http/"):
            status = line.strip()
            continue
        key, _, value = line.partition(":")
        headers.append({"name": key.strip(), "value": value.strip()})
    body_parsed = None
    body_error = None
    try:
        body_parsed = orjson.loads(body_blob)
    except orjson.JSONDecodeError as exc:
        body_error = f"{exc.__class__.__name__}: {exc}"
    return {
        "status_line": status,
        "headers": headers,
        "body_text": body_blob,
        "body_json": body_parsed,
        "body_error": body_error,
    }


def parse_request_headers(stderr: bytes) -> List[Dict[str, str]]:
    headers: List[Dict[str, str]] = []
    for line in stderr.decode("utf-8", errors="replace").splitlines():
        if not line.startswith("> "):
            continue
        stripped = line[2:]
        if not stripped or stripped.upper().startswith(
            ("GET ", "POST ", "PUT ", "DELETE ", "PATCH ")
        ):
            continue
        key, _, value = stripped.partition(":")
        if not value:
            continue
        name = key.strip()
        val = value.strip()
        if name.lower() == "authorization":
            headers.append({"name": name, "value": "Bearer [redacted]"})
        else:
            headers.append({"name": name, "value": val})
    return headers


def log_request(
    log_path: Path,
    entry: Dict[str, object],
) -> None:
    with log_path.open("ab") as handle:
        handle.write(orjson.dumps(entry))
        handle.write(b"\n")


def ensure_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        typer.secho("OPENAI_API_KEY is required", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    return key


def execute_request(
    *,
    messages: List[Dict[str, str]],
    model: str,
    api_key: str,
    run_id: str,
    strategy: str,
    length_label: str,
    stage: str,
    log_path: Path,
    extra: Dict[str, object],
) -> None:
    payload = {
        "model": model,
        "messages": messages,
        "max_completion_tokens": 16,
    }
    start_ts = _utc_now_iso()
    start_time = time.perf_counter()
    command = format_curl_command(api_key)
    process = subprocess.run(
        command,
        input=orjson.dumps(payload),
        capture_output=True,
        check=False,
    )
    end_time = time.perf_counter()
    end_ts = _utc_now_iso()
    response = parse_response(process.stdout)
    request_headers = parse_request_headers(process.stderr)
    entry = {
        "run_id": run_id,
        "strategy": strategy,
        "length_label": length_label,
        "stage": stage,
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "elapsed_ms": (end_time - start_time) * 1000,
        "request": {
            "method": "POST",
            "url": API_URL,
            "headers": request_headers,
            "body": payload,
        },
        "response": response,
        "curl_returncode": process.returncode,
        **extra,
    }
    log_request(log_path, entry)
    status_line = response.get("status_line")
    cached_tokens = None
    body_json = response.get("body_json")
    if body_json and isinstance(body_json, dict):
        usage = body_json.get("usage") or {}
        details = usage.get("prompt_tokens_details") or {}
        cached_tokens = details.get("cached_tokens")
    typer.echo(
        f"[{strategy}][{length_label}][{stage}] status={status_line} "
        f"cached_tokens={cached_tokens} elapsed_ms={entry['elapsed_ms']:.1f}",
    )
    if process.returncode != 0:
        typer.secho(
            f"curl exited with {process.returncode} for stage {stage}",
            fg=typer.colors.YELLOW,
            err=True,
        )


@app.command()
def run(
    output_dir: Path = typer.Option(Path("data"), help="Directory for JSONL logs."),
    model: str = typer.Option("gpt-5-nano", help="Model name to query."),
    run_id: str = typer.Option(
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        help="Identifier embedded into log rows.",
    ),
    ttl_waits: str = typer.Option(
        "60,360,300",
        help="Comma-separated sleep durations (seconds) between TTL probes.",
    ),
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / f"cache-{run_id}.jsonl"
    typer.echo(f"Logging to {log_path}")
    api_key = ensure_api_key()
    encoding = tiktoken.get_encoding("cl100k_base")
    token_ids = build_token_pool(encoding, TOKEN_POOL_TARGET)
    segments = chunk_segments(encoding, token_ids, SEGMENT_TOKEN_LENGTH)
    segment_plan: Dict[str, Dict[str, int]] = {}

    def build_messages(strategy: str, segment_count: int) -> List[Dict[str, str]]:
        content_segments = segments[:segment_count]
        if strategy == "single_message":
            combined = "".join(content_segments)
            return [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": combined},
            ]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for text in content_segments:
            messages.append({"role": "user", "content": text})
        return messages

    for label, target_total in TARGET_TOTAL_TOKENS.items():
        for segment_count in range(1, len(segments) + 1):
            messages = build_messages("single_message", segment_count)
            estimate = count_chat_tokens(encoding, messages)
            if estimate >= target_total:
                segment_plan[label] = {
                    "segment_count": segment_count,
                    "single_estimate_tokens": estimate,
                }
                break
        else:
            raise RuntimeError(f"Unable to satisfy target tokens for {label}")

    if len(segment_plan) != len(TARGET_TOTAL_TOKENS):
        raise RuntimeError("Segment planning incomplete")

    ordered_labels = sorted(
        segment_plan.keys(),
        key=lambda lbl: segment_plan[lbl]["segment_count"],
    )

    ttl_wait_durations = [int(item.strip()) for item in ttl_waits.split(",") if item.strip()]
    for strategy in ("single_message", "multi_message"):
        typer.secho(f"=== Strategy: {strategy} ===", fg=typer.colors.CYAN)
        for length_label in ordered_labels:
            segment_count = segment_plan[length_label]["segment_count"]
            typer.secho(f"-- Target tokens: {length_label}", fg=typer.colors.BLUE)
            user_messages = build_messages(strategy, segment_count)
            local_estimate = count_chat_tokens(encoding, user_messages)
            execute_request(
                messages=user_messages,
                model=model,
                api_key=api_key,
                run_id=run_id,
                strategy=strategy,
                length_label=length_label,
                stage="warm",
                log_path=log_path,
                extra={
                    "ttl_wait_seconds": 0,
                    "message_count": len(user_messages),
                    "local_prompt_token_estimate": local_estimate,
                },
            )
            execute_request(
                messages=user_messages,
                model=model,
                api_key=api_key,
                run_id=run_id,
                strategy=strategy,
                length_label=length_label,
                stage="immediate_repeat",
                log_path=log_path,
                extra={
                    "ttl_wait_seconds": 0,
                    "message_count": len(user_messages),
                    "local_prompt_token_estimate": local_estimate,
                },
            )
            if length_label != ordered_labels[-1]:
                continue
            for index, wait_seconds in enumerate(ttl_wait_durations, start=1):
                typer.echo(f"Sleeping {wait_seconds}s before TTL probe {index}")
                time.sleep(wait_seconds)
                execute_request(
                    messages=user_messages,
                    model=model,
                    api_key=api_key,
                    run_id=run_id,
                    strategy=strategy,
                    length_label=length_label,
                    stage=f"ttl_probe_{index}",
                    log_path=log_path,
                    extra={
                        "ttl_wait_seconds": wait_seconds,
                        "message_count": len(user_messages),
                        "local_prompt_token_estimate": local_estimate,
                    },
                )


if __name__ == "__main__":
    app()
