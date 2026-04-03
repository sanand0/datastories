#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "orjson>=3.10",
#   "typer>=0.16",
# ]
# ///

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
import os
import selectors
import signal
import subprocess
import time
from typing import Any

import typer

from tds_p1_common import ROOT, ensure_dir, read_json, safe_slug, write_json

MODEL_NAME = "gemini-3.1-pro-preview"
MODEL_SLUG = safe_slug(MODEL_NAME)
ANALYSIS_ROOT = ROOT / "analysis" / "image-evals" / MODEL_SLUG
DEFAULT_LOG_PATH = ANALYSIS_ROOT / "parallel-eval-run.log"
DEFAULT_STATUS_PATH = ANALYSIS_ROOT / "parallel-progress.json"
DEFAULT_PID_PATH = ANALYSIS_ROOT / "parallel-run.pid"
DEFAULT_WORKER_DIR = ANALYSIS_ROOT / "parallel-workers"

app = typer.Typer(add_completion=False)
STOP_REQUESTED = False


@dataclass
class Worker:
    index: int
    progress_path: Path
    log_path: Path
    command: list[str]
    process: subprocess.Popen[str] | None = None


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


def append_log(handle, message: str) -> None:
    line = message.rstrip("\n")
    typer.echo(line)
    handle.write(line + "\n")
    handle.flush()


def append_worker_log(path: Path, message: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(message)


def request_stop(signum: int, frame: Any) -> None:  # noqa: ARG001
    global STOP_REQUESTED
    STOP_REQUESTED = True


def build_eval_command(
    *,
    worker_index: int,
    worker_count: int,
    progress_every: int,
    progress_path: Path,
    question_ids: list[str],
    emails: list[str],
    submission_ids: list[int],
    force: bool,
) -> list[str]:
    command = [
        "uv",
        "run",
        "scripts/evaluate_images.py",
        "--format",
        "json",
        "--progress-every",
        str(progress_every),
        "--run-label",
        f"parallel-worker-{worker_index:02d}-of-{worker_count:02d}",
        "--progress-path",
        str(progress_path),
        "--shard-count",
        str(worker_count),
        "--shard-index",
        str(worker_index),
    ]
    for question_id in question_ids:
        command.extend(["--question-id", question_id])
    for email in emails:
        command.extend(["--email", email])
    for submission_id in submission_ids:
        command.extend(["--submission-id", str(submission_id)])
    if force:
        command.append("--force")
    return command


def load_progress(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = read_json(path)
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def worker_state(worker: Worker) -> dict[str, Any]:
    payload = load_progress(worker.progress_path)
    return {
        "worker": worker.index,
        "pid": worker.process.pid if worker.process else None,
        "returncode": worker.process.poll() if worker.process else None,
        "status": payload.get("status", "pending"),
        "processed": int(payload.get("processed") or 0),
        "selected_rows": int(payload.get("selected_rows") or 0),
        "evaluated": int(payload.get("evaluated") or 0),
        "skipped_existing": int(payload.get("skipped_existing") or 0),
        "errors": int(payload.get("errors") or 0),
        "current": payload.get("current") or {},
        "progress_path": str(worker.progress_path),
        "log_path": str(worker.log_path),
    }


def aggregate_status(
    *,
    workers: list[Worker],
    started_at_utc: str,
    started_perf: float,
    status: str,
) -> dict[str, Any]:
    states = [worker_state(worker) for worker in workers]
    selected_rows = sum(state["selected_rows"] for state in states)
    processed = sum(state["processed"] for state in states)
    evaluated = sum(state["evaluated"] for state in states)
    skipped_existing = sum(state["skipped_existing"] for state in states)
    errors = sum(state["errors"] for state in states)
    elapsed_seconds = time.perf_counter() - started_perf
    rate_rows_per_second = processed / elapsed_seconds if processed and elapsed_seconds > 0 else 0.0
    remaining_rows = max(selected_rows - processed, 0)
    eta_seconds = remaining_rows / rate_rows_per_second if remaining_rows and rate_rows_per_second > 0 else (0.0 if remaining_rows == 0 and selected_rows else None)
    eta_at_utc = (
        (datetime.now(UTC) + timedelta(seconds=eta_seconds)).isoformat()
        if eta_seconds is not None
        else ""
    )
    active_workers = sum(1 for worker in workers if worker.process and worker.process.poll() is None)
    current = [state["current"] | {"worker": state["worker"]} for state in states if state["current"]]
    return {
        "status": status,
        "model": MODEL_NAME,
        "workers": len(workers),
        "active_workers": active_workers,
        "processed": processed,
        "selected_rows": selected_rows,
        "evaluated": evaluated,
        "skipped_existing": skipped_existing,
        "errors": errors,
        "remaining_rows": remaining_rows,
        "started_at_utc": started_at_utc,
        "updated_at_utc": now_utc(),
        "elapsed_seconds": round(elapsed_seconds, 1),
        "elapsed": format_duration(elapsed_seconds),
        "rate_basis": "overall",
        "overall_rate_rows_per_minute": round(rate_rows_per_second * 60, 2),
        "rate_rows_per_minute": round(rate_rows_per_second * 60, 2),
        "eta_seconds": round(eta_seconds, 1) if eta_seconds is not None else None,
        "eta": format_duration(eta_seconds),
        "eta_at_utc": eta_at_utc,
        "current": current,
        "worker_states": states,
    }


def terminate_workers(workers: list[Worker]) -> None:
    for worker in workers:
        if worker.process and worker.process.poll() is None:
            worker.process.terminate()
    time.sleep(2)
    for worker in workers:
        if worker.process and worker.process.poll() is None:
            worker.process.kill()


def update_progress_samples(
    samples: list[tuple[float, int]],
    *,
    timestamp: float,
    processed: int,
) -> None:
    if samples and samples[-1][1] == processed:
        return
    samples.append((timestamp, processed))
    cutoff = timestamp - 1800
    while len(samples) > 2 and samples[0][0] < cutoff:
        samples.pop(0)


def apply_recent_rate(
    payload: dict[str, Any],
    *,
    samples: list[tuple[float, int]],
    window_seconds: int = 300,
) -> dict[str, Any]:
    if len(samples) < 2:
        return payload

    latest_time, latest_processed = samples[-1]
    reference: tuple[float, int] | None = None
    for sample in reversed(samples[:-1]):
        sample_time, sample_processed = sample
        if sample_processed >= latest_processed:
            continue
        reference = sample
        if latest_time - sample_time >= window_seconds:
            break

    if reference is None:
        return payload

    delta_seconds = latest_time - reference[0]
    delta_rows = latest_processed - reference[1]
    if delta_seconds <= 0 or delta_rows <= 0:
        return payload

    rate_rows_per_second = delta_rows / delta_seconds
    remaining_rows = max(int(payload["selected_rows"]) - latest_processed, 0)
    eta_seconds = remaining_rows / rate_rows_per_second if remaining_rows else 0.0
    payload["rate_basis"] = f"recent-{window_seconds}s"
    payload["rate_rows_per_minute"] = round(rate_rows_per_second * 60, 2)
    payload["eta_seconds"] = round(eta_seconds, 1)
    payload["eta"] = format_duration(eta_seconds)
    payload["eta_at_utc"] = (datetime.now(UTC) + timedelta(seconds=eta_seconds)).isoformat()
    return payload


def aggregate_line(payload: dict[str, Any]) -> str:
    return (
        "[aggregate] "
        f"{payload['processed']}/{payload['selected_rows']} "
        f"({(payload['processed'] / payload['selected_rows'] * 100) if payload['selected_rows'] else 0:.1f}%)"
        f" | eval={payload['evaluated']}"
        f" skip={payload['skipped_existing']}"
        f" err={payload['errors']}"
        f" | active={payload['active_workers']}/{payload['workers']}"
        f" | rate={payload['rate_rows_per_minute']:.2f}/min"
        f" ({payload['rate_basis']})"
        f" | elapsed={payload['elapsed']}"
        f" | eta={payload['eta']}"
    )


@app.command()
def main(
    workers: int = typer.Option(4, "--workers", min=1, help="Number of parallel shard workers to launch."),
    question_ids: list[str] | None = typer.Option(None, "--question-id", help="Restrict to one or more q-generate-* questions."),
    emails: list[str] | None = typer.Option(None, "--email", help="Restrict to one or more student emails."),
    submission_ids: list[int] | None = typer.Option(None, "--submission-id", help="Restrict to one or more submission IDs."),
    force: bool = typer.Option(False, "--force", help="Re-evaluate existing outputs for the selected subset."),
    progress_every: int = typer.Option(1, "--progress-every", min=1, help="Worker progress update interval in processed rows."),
    poll_seconds: int = typer.Option(15, "--poll-seconds", min=5, help="Aggregate status/log update interval."),
    stagger_seconds: int = typer.Option(2, "--stagger-seconds", min=0, help="Seconds to wait between launching workers."),
    log_path: Path = typer.Option(DEFAULT_LOG_PATH, "--log-path", help="Combined log file path."),
    status_path: Path = typer.Option(DEFAULT_STATUS_PATH, "--status-path", help="Aggregate progress JSON path."),
    pid_path: Path = typer.Option(DEFAULT_PID_PATH, "--pid-path", help="Runner PID file path."),
    worker_dir: Path = typer.Option(DEFAULT_WORKER_DIR, "--worker-dir", help="Directory for per-worker progress files."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the worker commands without executing them."),
) -> None:
    """Run evaluate_images.py in parallel shards without rebuilding gallery summaries."""

    selected_question_ids = question_ids or []
    selected_emails = emails or []
    selected_submission_ids = submission_ids or []

    ensure_dir(log_path.parent)
    ensure_dir(status_path.parent)
    ensure_dir(pid_path.parent)
    ensure_dir(worker_dir)

    worker_specs: list[Worker] = []
    for index in range(workers):
        progress_path = worker_dir / f"worker-{index:02d}-progress.json"
        worker_specs.append(
            Worker(
                index=index,
                progress_path=progress_path,
                log_path=worker_dir / f"worker-{index:02d}.log",
                command=build_eval_command(
                    worker_index=index,
                    worker_count=workers,
                    progress_every=progress_every,
                    progress_path=progress_path,
                    question_ids=selected_question_ids,
                    emails=selected_emails,
                    submission_ids=selected_submission_ids,
                    force=force,
                ),
            )
        )

    if dry_run:
        payload = {
            "workers": workers,
            "commands": [worker.command for worker in worker_specs],
            "status_path": str(status_path),
            "log_path": str(log_path),
            "pid_path": str(pid_path),
            "worker_dir": str(worker_dir),
        }
        typer.echo(str(payload))
        raise typer.Exit()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    pid_path.write_text(str(os.getpid()), encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    started_at_utc = now_utc()
    started_perf = time.perf_counter()

    with log_path.open("a", encoding="utf-8") as log_handle:
        append_log(log_handle, f"[run] started {started_at_utc} pid={os.getpid()}")
        for worker in worker_specs:
            append_log(log_handle, f"[run] worker={worker.index} cmd={' '.join(worker.command)}")

        selector = selectors.DefaultSelector()
        file_to_worker: dict[Any, Worker] = {}

        for index, worker in enumerate(worker_specs):
            worker.process = subprocess.Popen(
                worker.command,
                cwd=ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            if worker.process.stdout is None:
                raise RuntimeError(f"Failed to capture stdout for worker {worker.index}")
            selector.register(worker.process.stdout, selectors.EVENT_READ)
            file_to_worker[worker.process.stdout] = worker
            if stagger_seconds and index < len(worker_specs) - 1:
                time.sleep(stagger_seconds)

        initial_payload = aggregate_status(
            workers=worker_specs,
            started_at_utc=started_at_utc,
            started_perf=started_perf,
            status="running",
        )
        progress_samples: list[tuple[float, int]] = []
        update_progress_samples(
            progress_samples,
            timestamp=time.perf_counter(),
            processed=int(initial_payload["processed"]),
        )
        initial_payload = apply_recent_rate(initial_payload, samples=progress_samples)
        write_json(status_path, initial_payload)
        append_log(log_handle, aggregate_line(initial_payload))

        next_poll_at = time.time() + poll_seconds
        final_exit_code = 0

        while True:
            if STOP_REQUESTED:
                terminate_workers(worker_specs)
                final_payload = aggregate_status(
                    workers=worker_specs,
                    started_at_utc=started_at_utc,
                    started_perf=started_perf,
                    status="stopped",
                )
                update_progress_samples(
                    progress_samples,
                    timestamp=time.perf_counter(),
                    processed=int(final_payload["processed"]),
                )
                final_payload = apply_recent_rate(final_payload, samples=progress_samples)
                final_payload["stopped_at_utc"] = now_utc()
                write_json(status_path, final_payload)
                append_log(log_handle, aggregate_line(final_payload))
                append_log(log_handle, f"[run] stopped {final_payload['stopped_at_utc']}")
                final_exit_code = 1
                break

            timeout = max(0.0, next_poll_at - time.time())
            events = selector.select(timeout=timeout)
            for key, _mask in events:
                worker = file_to_worker[key.fileobj]
                line = key.fileobj.readline()
                if line:
                    append_worker_log(worker.log_path, line)

            if time.time() >= next_poll_at:
                payload = aggregate_status(
                    workers=worker_specs,
                    started_at_utc=started_at_utc,
                    started_perf=started_perf,
                    status="running",
                )
                update_progress_samples(
                    progress_samples,
                    timestamp=time.perf_counter(),
                    processed=int(payload["processed"]),
                )
                payload = apply_recent_rate(payload, samples=progress_samples)
                write_json(status_path, payload)
                append_log(log_handle, aggregate_line(payload))
                next_poll_at = time.time() + poll_seconds

            if all(worker.process and worker.process.poll() is not None for worker in worker_specs):
                for handle, worker in list(file_to_worker.items()):
                    while True:
                        line = handle.readline()
                        if not line:
                            break
                        append_worker_log(worker.log_path, line)
                failed = any((worker.process.returncode or 0) != 0 for worker in worker_specs if worker.process)
                final_payload = aggregate_status(
                    workers=worker_specs,
                    started_at_utc=started_at_utc,
                    started_perf=started_perf,
                    status="failed" if failed else "completed",
                )
                update_progress_samples(
                    progress_samples,
                    timestamp=time.perf_counter(),
                    processed=int(final_payload["processed"]),
                )
                final_payload = apply_recent_rate(final_payload, samples=progress_samples)
                final_payload["finished_at_utc"] = now_utc()
                write_json(status_path, final_payload)
                append_log(log_handle, aggregate_line(final_payload))
                append_log(
                    log_handle,
                    f"[run] finished {final_payload['finished_at_utc']} exit_codes="
                    + ",".join(str(worker.process.returncode if worker.process else None) for worker in worker_specs)
                    + " worker_logs="
                    + ",".join(str(worker.log_path) for worker in worker_specs),
                )
                final_exit_code = 1 if failed else 0
                break

        pid_path.unlink(missing_ok=True)
        raise typer.Exit(final_exit_code)


if __name__ == "__main__":
    app()
