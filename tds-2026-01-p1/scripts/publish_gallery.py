#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "typer>=0.16",
# ]
# ///

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json
import os
import selectors
import subprocess
import sys
import time

import typer

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gemini-3.1-pro-preview"
MODEL_SLUG = "gemini-3-1-pro-preview"
ANALYSIS_ROOT = ROOT / "analysis" / "image-evals" / MODEL_SLUG
DEFAULT_LOG_PATH = ANALYSIS_ROOT / "full-gallery-run.log"
DEFAULT_PROGRESS_PATH = ANALYSIS_ROOT / "progress.json"
DEFAULT_PID_PATH = ANALYSIS_ROOT / "full-gallery-run.pid"
DEFAULT_GALLERY_DIR = ROOT / "gallery"

app = typer.Typer(add_completion=False)


def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def append_log(log_handle, message: str) -> None:
    line = message.rstrip("\n")
    print(line)
    log_handle.write(line + "\n")
    log_handle.flush()


def read_summary_counts(summary_path: Path) -> tuple[int | None, int | None]:
    if not summary_path.exists():
        return None, None
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        return int(payload.get("result_count", 0)), int(payload.get("pending_result_count", 0))
    except Exception:  # noqa: BLE001
        return None, None


def build_gallery_args(all_students: bool, emails: list[str], gallery_dir: Path) -> list[str]:
    args = ["uv", "run", "scripts/build_gallery.py", "--gallery-dir", str(gallery_dir)]
    if all_students:
        args.append("--all-students")
    for email in emails:
        args.extend(["--email", email])
    return args


def refresh_gallery(*, all_students: bool, emails: list[str], gallery_dir: Path) -> tuple[int | None, int | None, str]:
    result = subprocess.run(
        build_gallery_args(all_students, emails, gallery_dir),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    summary_path = gallery_dir / "summary.json"
    result_count, pending_count = read_summary_counts(summary_path)
    details = result.stdout.strip() or result.stderr.strip()
    if result.returncode != 0:
        details = f"build_gallery exit={result.returncode} {details}".strip()
    return result_count, pending_count, details


def evaluate_args(*, emails: list[str], progress_every: int, progress_path: Path) -> list[str]:
    args = [
        "uv",
        "run",
        "scripts/evaluate_images.py",
        "--format",
        "text",
        "--progress-every",
        str(progress_every),
        "--run-label",
        "full-gallery",
        "--progress-path",
        str(progress_path),
    ]
    for email in emails:
        args.extend(["--email", email])
    return args


@app.command()
def main(
    all_students: bool = typer.Option(False, "--all-students", help="Publish the full all-students gallery."),
    emails: list[str] | None = typer.Option(None, "--email", help="Restrict the run to one or more student emails."),
    refresh_seconds: int = typer.Option(180, "--refresh-seconds", min=30, help="How often to rebuild gallery/summary.json while evaluations are running."),
    progress_every: int = typer.Option(10, "--progress-every", min=1, help="Emit evaluator status and ETA every N processed rows."),
    gallery_dir: Path = typer.Option(DEFAULT_GALLERY_DIR, "--gallery-dir", help="Gallery output directory."),
    log_path: Path = typer.Option(DEFAULT_LOG_PATH, "--log-path", help="Path to the run log file."),
    progress_path: Path = typer.Option(DEFAULT_PROGRESS_PATH, "--progress-path", help="Path to the live evaluator progress JSON."),
    pid_path: Path = typer.Option(DEFAULT_PID_PATH, "--pid-path", help="Path to the publisher PID file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show the commands that would run without executing them."),
) -> None:
    """Evaluate images and refresh gallery/summary.json until the full run completes."""

    selected_emails = emails or []
    if not all_students and not selected_emails:
        raise typer.BadParameter("Pass --all-students or at least one --email.")

    ensure_dir(log_path.parent)
    ensure_dir(progress_path.parent)
    ensure_dir(pid_path.parent)

    eval_cmd = evaluate_args(emails=selected_emails, progress_every=progress_every, progress_path=progress_path)
    gallery_cmd = build_gallery_args(all_students, selected_emails, gallery_dir)

    if dry_run:
        typer.echo(json.dumps({"evaluate_cmd": eval_cmd, "gallery_cmd": gallery_cmd}, indent=2))
        raise typer.Exit()

    pid_path.write_text(str(os.getpid()), encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    with log_path.open("a", encoding="utf-8") as log_handle:
        append_log(log_handle, f"[run] started {now_utc()} pid={os.getpid()}")
        append_log(log_handle, f"[run] evaluate_cmd={' '.join(eval_cmd)}")
        append_log(log_handle, f"[run] gallery_cmd={' '.join(gallery_cmd)}")

        result_count, pending_count, details = refresh_gallery(
            all_students=all_students,
            emails=selected_emails,
            gallery_dir=gallery_dir,
        )
        append_log(
            log_handle,
            f"[gallery-refresh] {now_utc()} result_count={result_count} pending={pending_count} details={details}",
        )

        proc = subprocess.Popen(
            eval_cmd,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if proc.stdout is None:
            raise RuntimeError("Failed to capture evaluator stdout.")

        selector = selectors.DefaultSelector()
        selector.register(proc.stdout, selectors.EVENT_READ)
        next_refresh_at = time.time() + refresh_seconds

        while True:
            timeout = max(0.0, next_refresh_at - time.time())
            events = selector.select(timeout=timeout)
            if events:
                line = proc.stdout.readline()
                if line:
                    append_log(log_handle, line.rstrip("\n"))

            if time.time() >= next_refresh_at:
                result_count, pending_count, details = refresh_gallery(
                    all_students=all_students,
                    emails=selected_emails,
                    gallery_dir=gallery_dir,
                )
                append_log(
                    log_handle,
                    f"[gallery-refresh] {now_utc()} result_count={result_count} pending={pending_count} details={details}",
                )
                next_refresh_at = time.time() + refresh_seconds

            if proc.poll() is not None:
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    append_log(log_handle, line.rstrip("\n"))
                break

        result_count, pending_count, details = refresh_gallery(
            all_students=all_students,
            emails=selected_emails,
            gallery_dir=gallery_dir,
        )
        append_log(
            log_handle,
            f"[gallery-refresh] {now_utc()} result_count={result_count} pending={pending_count} details={details}",
        )
        append_log(log_handle, f"[run] finished {now_utc()} exit={proc.returncode}")

    raise typer.Exit(proc.returncode or 0)


if __name__ == "__main__":
    app()
