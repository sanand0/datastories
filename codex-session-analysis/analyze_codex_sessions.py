#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer>=0.12"]
# ///

"""Analyze Codex session logs and map feature usage gaps to release notes."""

from __future__ import annotations

import csv
import json
import re
import shlex
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer


MONTH_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$"
)
DATE_RE = re.compile(r"^\s*[•*]\s*(\d{4}-\d{2}-\d{2})\s*$")
BULLET_RE = re.compile(r"^\s*[□•-]\s+(.*\S)\s*$")
IMAGE_TASK_RE = re.compile(
    r"\b(image|screenshot|ui|ux|design|diagram|chart|visuali[sz]ation|photo|logo)\b", re.IGNORECASE
)
BATCH_TASK_RE = re.compile(
    r"\b(all|every|across|for each|bulk|batch|entire repo|entire codebase|whole codebase)\b",
    re.IGNORECASE,
)
SKIP_CONTEXT_MARKERS = ("AGENTS.md instructions", "<environment_context>", "<permissions instructions>")

READ_ONLY_CMDS = {
    "cat",
    "cd",
    "cut",
    "du",
    "env",
    "fd",
    "find",
    "git",
    "grep",
    "head",
    "jaq",
    "jq",
    "ls",
    "pwd",
    "rg",
    "sed",
    "sort",
    "stat",
    "tail",
    "test",
    "ug",
    "uniq",
    "wc",
}
GIT_READ_ONLY_SUBCMDS = {
    "branch",
    "diff",
    "log",
    "show",
    "status",
    "rev-parse",
    "remote",
}
WRITE_PATTERNS = [
    re.compile(r"\bsed\s+-i\b"),
    re.compile(r"\bperl\s+-i\b"),
    re.compile(r"\becho\b.*>>?"),
    re.compile(r"\bprintf\b.*>>?"),
    re.compile(r"\bcat\b.*>>?"),
    re.compile(r"\btee\b"),
    re.compile(r"\btouch\b"),
    re.compile(r"\bmkdir\b"),
    re.compile(r"\brm\b"),
    re.compile(r"\bmv\b"),
    re.compile(r"\bcp\b"),
    re.compile(r"\binstall\b"),
    re.compile(r"\bapply_patch\b"),
    re.compile(r"<<\s*'?(EOF|PATCH)"),
    re.compile(r"\bgit\s+(add|commit|checkout|switch|merge|rebase|reset|restore|revert)\b"),
]
NETWORK_CMDS = {"curl", "wget", "w3m", "lynx"}
SHELL_TOOL_NAMES = {"shell", "shell_command", "exec_command"}
WEB_EVENT_TYPES = {"web_search_call", "search", "open_page", "find_in_page"}
LONG_RUNNING_SECONDS = 60.0
COMPLEX_TOOL_THRESHOLD = 20
MULTI_SEGMENT_RE = re.compile(r"(\&\&|\|\||\||;|\n)")


@dataclass
class ToolCall:
    """Normalized tool call + output metadata for a session."""

    idx: int
    timestamp: str | None
    name: str
    call_id: str | None
    arguments: str | None
    command: str | None
    base_command: str | None
    exit_code: int | None = None
    duration_seconds: float | None = None
    failed: bool = False
    output_snippet: str | None = None


@dataclass
class SessionSummary:
    """Aggregated signals extracted from one session log."""

    path: str
    file_type: str
    session_id: str | None = None
    session_timestamp: str | None = None
    primary_prompt: str = ""
    user_message_count: int = 0
    user_messages: list[str] = field(default_factory=list)
    tools: Counter[str] = field(default_factory=Counter)
    calls: list[ToolCall] = field(default_factory=list)
    event_types: Counter[str] = field(default_factory=Counter)
    web_events: int = 0
    input_images: int = 0
    collaboration_modes: Counter[str] = field(default_factory=Counter)
    models: Counter[str] = field(default_factory=Counter)
    permission_error_count: int = 0
    network_lookup_count: int = 0


@dataclass
class Opportunity:
    """A concrete place where a Codex feature likely would have helped."""

    feature: str
    reason: str
    path: str
    session_timestamp: str | None
    primary_prompt: str
    evidence: str


@dataclass
class ReleaseBullet:
    """One bullet line extracted from the Codex changelog."""

    date: str
    month: str
    title: str
    section: str
    text: str


def parse_timestamp(value: str | None) -> datetime | None:
    """Convert ISO-like timestamps to aware datetime objects."""
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def safe_json_loads(raw: Any) -> Any:
    """Parse JSON strings where possible; otherwise return original value."""
    if isinstance(raw, (dict, list)):
        return raw
    if not isinstance(raw, str):
        return raw
    text = raw.strip()
    if not text:
        return raw
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return raw


def content_to_text(content: Any) -> str:
    """Flatten content blocks from Codex message payloads."""
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        for key in ("text", "message"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
    return "\n".join(parts).strip()


def normalize_shell_command(args_obj: Any) -> tuple[str | None, str | None]:
    """Extract full and base command from shell-like tool args."""
    if not isinstance(args_obj, dict):
        return None, None

    command = args_obj.get("cmd")
    if command is None:
        command = args_obj.get("command")

    command_list: list[str] | None = None
    if isinstance(command, list):
        command_list = [str(part) for part in command]
        full_cmd = " ".join(command_list).strip()
    elif isinstance(command, str):
        full_cmd = command.strip()
    else:
        return None, None

    if not full_cmd:
        return None, None

    # When command is `bash -lc "<script>"`, classify by the first script token.
    if command_list and len(command_list) >= 3 and command_list[0].endswith("bash") and "c" in command_list[1]:
        script = command_list[2]
        return full_cmd, first_script_token(script)

    try:
        tokens = shlex.split(full_cmd, posix=True)
    except ValueError:
        tokens = full_cmd.split()
    if not tokens:
        return full_cmd, None
    return full_cmd, tokens[0]


def first_script_token(script: str) -> str | None:
    """Return the first meaningful token in a shell script snippet."""
    try:
        tokens = shlex.split(script, posix=True)
    except ValueError:
        tokens = script.split()

    skip_literals = {"&&", "||", "|", ";", "then", "do", "done", "fi", "elif", "else", "{", "}"}

    for token in tokens:
        token = token.strip()
        if not token or token in skip_literals:
            continue
        if "=" in token and not token.startswith(("=", "==")):
            left = token.split("=", 1)[0]
            if left.replace("_", "").isalnum():
                continue
        if token.startswith("$("):
            continue
        if token.startswith("-"):
            continue
        return token
    return tokens[0] if tokens else None


def parse_output_blob(output: Any) -> tuple[int | None, float | None, str]:
    """Extract (exit_code, duration_seconds, plain_text_output)."""
    parsed = safe_json_loads(output)
    text = ""
    exit_code: int | None = None
    duration: float | None = None

    if isinstance(parsed, dict):
        metadata = parsed.get("metadata")
        if isinstance(metadata, dict):
            raw_code = metadata.get("exit_code")
            if isinstance(raw_code, int):
                exit_code = raw_code
            elif isinstance(raw_code, str) and raw_code.lstrip("-").isdigit():
                exit_code = int(raw_code)
            raw_duration = metadata.get("duration_seconds")
            if isinstance(raw_duration, (int, float)):
                duration = float(raw_duration)
        inner = parsed.get("output")
        text = inner if isinstance(inner, str) else json.dumps(parsed, ensure_ascii=True)
    elif isinstance(parsed, list):
        text = "\n".join(item if isinstance(item, str) else json.dumps(item, ensure_ascii=True) for item in parsed)
    else:
        text = str(parsed if parsed is not None else "")

    if exit_code is None:
        match = re.search(r"Process exited with code\s+(-?\d+)", text)
        if match:
            exit_code = int(match.group(1))
    if duration is None:
        match = re.search(r"Wall time:\s*([0-9.]+)\s*seconds", text)
        if match:
            duration = float(match.group(1))

    return exit_code, duration, text


def command_contains(call: ToolCall, needle: str) -> bool:
    """Case-insensitive substring check against normalized command text."""
    if not call.command:
        return False
    return needle.lower() in call.command.lower()


def is_write_command(full_cmd: str | None) -> bool:
    """Heuristic: command likely mutates files/worktree."""
    if not full_cmd:
        return False
    lowered = full_cmd.lower()
    return any(pattern.search(lowered) for pattern in WRITE_PATTERNS)


def is_read_only_command(base_cmd: str | None, full_cmd: str | None) -> bool:
    """Heuristic: command is inspection-only."""
    if not base_cmd or not full_cmd:
        return False
    if MULTI_SEGMENT_RE.search(full_cmd):
        return False
    if is_write_command(full_cmd):
        return False
    if base_cmd == "git":
        try:
            tokens = shlex.split(full_cmd, posix=True)
        except ValueError:
            tokens = full_cmd.split()
        if len(tokens) < 2:
            return False
        return tokens[1] in GIT_READ_ONLY_SUBCMDS
    return base_cmd in READ_ONLY_CMDS


def clean_prompt(text: str, limit: int = 220) -> str:
    """Collapse whitespace and trim long prompt text."""
    value = " ".join(text.split())
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def filtered_user_messages(messages: list[str]) -> list[str]:
    """Drop environment/config boilerplate from user-provided text."""
    filtered: list[str] = []
    for message in messages:
        text = message.strip()
        if not text:
            continue
        if any(marker in text for marker in SKIP_CONTEXT_MARKERS):
            continue
        filtered.append(text)
    return filtered


def has_slash_command(text: str, command: str) -> bool:
    """Check whether text includes an explicit slash-command invocation."""
    return re.search(rf"(?<![A-Za-z0-9_])/{re.escape(command)}\b", text) is not None


def prompt_needs_web_lookup(prompt: str) -> bool:
    """Heuristic for prompts that likely need up-to-date web verification."""
    lowered = prompt.lower()
    if "latest version of the code" in lowered:
        return False
    phrase_triggers = (
        "release notes",
        "changelog",
        "who is",
        "who's",
        "today's",
        "current price",
        "latest price",
        "stock price",
        "exchange rate",
        "breaking news",
        "most recent",
    )
    if any(phrase in lowered for phrase in phrase_triggers):
        return True

    if "latest" in lowered:
        context_terms = (
            "release",
            "version",
            "model",
            "api",
            "docs",
            "documentation",
            "pricing",
            "price",
            "rate",
            "news",
            "update",
            "feature",
        )
        if any(term in lowered for term in context_terms):
            return True

    if "current" in lowered:
        context_terms = ("version", "ceo", "president", "price", "rate", "model")
        if any(term in lowered for term in context_terms):
            return True

    return False


def pick_primary_prompt(messages: list[str]) -> str:
    """Pick the user prompt that best represents the task intent."""
    filtered = filtered_user_messages(messages)
    if filtered:
        # In most logs the actual task prompt appears last among context setup messages.
        return clean_prompt(filtered[-1])
    return clean_prompt(messages[-1]) if messages else ""


def parse_record_event(record: dict[str, Any]) -> tuple[str | None, dict[str, Any], str | None]:
    """Return (event_type, event_payload, timestamp)."""
    timestamp = record.get("timestamp")
    rtype = record.get("type")

    if rtype == "response_item" and isinstance(record.get("payload"), dict):
        payload = record["payload"]
        return payload.get("type"), payload, timestamp

    if rtype == "event_msg" and isinstance(record.get("payload"), dict):
        payload = record["payload"]
        return payload.get("type"), payload, timestamp

    if rtype in {"turn_context", "session_meta"} and isinstance(record.get("payload"), dict):
        return rtype, record["payload"], timestamp

    if isinstance(record.get("payload"), dict) and isinstance(record["payload"].get("type"), str):
        payload = record["payload"]
        return payload.get("type"), payload, timestamp

    return rtype, record, timestamp


def register_function_call(
    summary: SessionSummary,
    calls_by_id: dict[str, ToolCall],
    event: dict[str, Any],
    event_ts: str | None,
    idx: int,
) -> None:
    """Create normalized tool call objects from function_call records."""
    name = str(event.get("name") or "unknown")
    call_id = event.get("call_id") or event.get("id")
    arguments_raw = event.get("arguments")
    args_obj = safe_json_loads(arguments_raw)
    command, base_command = (None, None)
    if name in SHELL_TOOL_NAMES:
        command, base_command = normalize_shell_command(args_obj)
        if base_command in NETWORK_CMDS:
            summary.network_lookup_count += 1

    call = ToolCall(
        idx=idx,
        timestamp=event_ts,
        name=name,
        call_id=call_id if isinstance(call_id, str) else None,
        arguments=json.dumps(args_obj, ensure_ascii=True) if isinstance(args_obj, (dict, list)) else str(arguments_raw),
        command=command,
        base_command=base_command,
    )
    summary.calls.append(call)
    summary.tools[name] += 1
    if isinstance(call_id, str):
        calls_by_id[call_id] = call


def register_function_output(summary: SessionSummary, calls_by_id: dict[str, ToolCall], event: dict[str, Any]) -> None:
    """Attach outputs to previously observed calls and classify failures."""
    call_id = event.get("call_id")
    exit_code, duration, text = parse_output_blob(event.get("output"))
    target = calls_by_id.get(call_id) if isinstance(call_id, str) else None

    if target is None:
        target = ToolCall(
            idx=len(summary.calls),
            timestamp=None,
            name="unknown",
            call_id=call_id if isinstance(call_id, str) else None,
            arguments=None,
            command=None,
            base_command=None,
        )
        summary.calls.append(target)

    target.exit_code = exit_code
    target.duration_seconds = duration
    normalized_text = " ".join(text.split())
    target.output_snippet = normalized_text[:280] if normalized_text else ""
    lowered = normalized_text.lower()
    target.failed = bool(
        (exit_code is not None and exit_code != 0)
        or "error" in lowered
        or "failed" in lowered
        or "traceback" in lowered
        or "command not found" in lowered
    )

    if any(token in lowered for token in ("permission denied", "approval", "sandbox", "operation not permitted")):
        summary.permission_error_count += 1


def parse_jsonl_session(path: Path) -> SessionSummary:
    """Parse modern Codex JSONL session logs."""
    summary = SessionSummary(path=str(path), file_type="jsonl")
    calls_by_id: dict[str, ToolCall] = {}

    with path.open("r", encoding="utf-8") as handle:
        for idx, raw in enumerate(handle):
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue

            event_type, event, event_ts = parse_record_event(record)
            if event_type:
                summary.event_types[event_type] += 1

            if event_type == "session_meta":
                summary.session_id = str(event.get("id") or summary.session_id or "")
                summary.session_timestamp = str(event.get("timestamp") or summary.session_timestamp or "")

            if summary.session_timestamp is None:
                ts = record.get("timestamp")
                if isinstance(ts, str):
                    summary.session_timestamp = ts

            if event_type == "turn_context":
                model = event.get("model")
                if isinstance(model, str):
                    summary.models[model] += 1
                mode = event.get("collaboration_mode", {}).get("mode")
                if isinstance(mode, str):
                    summary.collaboration_modes[mode] += 1

            if event_type in WEB_EVENT_TYPES:
                summary.web_events += 1

            if event_type == "input_image":
                summary.input_images += 1

            if event_type == "message":
                role = event.get("role")
                if role == "user":
                    text = content_to_text(event.get("content"))
                    if text:
                        summary.user_messages.append(text)
                continue

            if event_type == "user_message":
                text = event.get("message")
                if isinstance(text, str) and text.strip():
                    summary.user_messages.append(text.strip())
                continue

            if event_type in {"function_call", "custom_tool_call"}:
                register_function_call(summary, calls_by_id, event, event_ts, idx)
                continue

            if event_type in {"function_call_output", "custom_tool_call_output"}:
                register_function_output(summary, calls_by_id, event)
                continue

    summary.user_message_count = len(summary.user_messages)
    summary.primary_prompt = pick_primary_prompt(summary.user_messages)
    return summary


def parse_rollout_json_session(path: Path) -> SessionSummary:
    """Parse legacy rollout JSON files with a top-level items array."""
    summary = SessionSummary(path=str(path), file_type="rollout_json")
    calls_by_id: dict[str, ToolCall] = {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return summary

    session_obj = data.get("session", {})
    if isinstance(session_obj, dict):
        sid = session_obj.get("id")
        sts = session_obj.get("timestamp")
        if isinstance(sid, str):
            summary.session_id = sid
        if isinstance(sts, str):
            summary.session_timestamp = sts

    items = data.get("items")
    if not isinstance(items, list):
        return summary

    for idx, event in enumerate(items):
        if not isinstance(event, dict):
            continue
        event_type = event.get("type")
        if isinstance(event_type, str):
            summary.event_types[event_type] += 1

        if event_type == "message" and event.get("role") == "user":
            text = content_to_text(event.get("content"))
            if text:
                summary.user_messages.append(text)
            continue

        if event_type == "function_call":
            register_function_call(summary, calls_by_id, event, summary.session_timestamp, idx)
            continue

        if event_type == "function_call_output":
            register_function_output(summary, calls_by_id, event)
            continue

    summary.user_message_count = len(summary.user_messages)
    summary.primary_prompt = pick_primary_prompt(summary.user_messages)
    return summary


def parse_changelog_bullets(path: Path) -> list[ReleaseBullet]:
    """Extract dated changelog bullets from the Codex changelog text dump."""
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    bullets: list[ReleaseBullet] = []
    month = ""
    current_date: str | None = None
    title = ""
    section = "general"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if MONTH_RE.match(stripped):
            month = stripped
            current_date = None
            title = ""
            section = "general"
            continue

        date_match = DATE_RE.match(stripped)
        if date_match:
            current_date = date_match.group(1)
            title = ""
            section = "general"
            continue

        if current_date:
            # First non-empty, non-bullet line after date is usually the release title.
            if not title and not BULLET_RE.match(stripped):
                title = stripped
                continue

            lowered = stripped.lower()
            if lowered in {"new features", "bug fixes", "fixes & improvements", "documentation", "chores"}:
                section = lowered
                continue

            bullet_match = BULLET_RE.match(stripped)
            if bullet_match:
                bullets.append(
                    ReleaseBullet(
                        date=current_date,
                        month=month,
                        title=title or "(untitled release)",
                        section=section,
                        text=bullet_match.group(1),
                    )
                )

    return bullets


def find_opportunities(summary: SessionSummary) -> list[Opportunity]:
    """Derive actionable feature opportunities from one session summary."""
    opportunities: list[Opportunity] = []
    tools = summary.tools
    prompt = summary.primary_prompt
    prompt_lower = prompt.lower()

    has_parallel = any(name in tools for name in ("parallel", "multi_tool_use.parallel"))
    has_plan = tools.get("update_plan", 0) > 0 or summary.collaboration_modes.get("plan", 0) > 0
    has_subagents = any(name in tools for name in ("spawn_agent", "spawn_agents_on_csv", "wait", "close_agent", "send_input"))
    has_web = summary.web_events > 0
    has_request_user_input = tools.get("request_user_input", 0) > 0
    has_view_image = tools.get("view_image", 0) > 0 or summary.input_images > 0
    has_apply_patch = tools.get("apply_patch", 0) > 0 or any(
        call.base_command == "apply_patch" or ("apply_patch" in (call.command or "")) for call in summary.calls
    )

    # Parallel read opportunities: multiple read-only shell calls in a row.
    consecutive: list[ToolCall] = []
    sequences: list[list[ToolCall]] = []
    for call in summary.calls:
        if call.name not in SHELL_TOOL_NAMES:
            if len(consecutive) >= 3:
                sequences.append(consecutive.copy())
            consecutive = []
            continue
        if is_read_only_command(call.base_command, call.command):
            consecutive.append(call)
            continue
        if len(consecutive) >= 3:
            sequences.append(consecutive.copy())
        consecutive = []
    if len(consecutive) >= 3:
        sequences.append(consecutive.copy())

    if sequences and not has_parallel:
        sample = sequences[0][:3]
        evidence = " | ".join(call.command or call.base_command or call.name for call in sample)
        opportunities.append(
            Opportunity(
                feature="parallel tool calls",
                reason="Session performs repeated sequential read-only shell calls.",
                path=summary.path,
                session_timestamp=summary.session_timestamp,
                primary_prompt=prompt,
                evidence=evidence,
            )
        )

    long_running = [call for call in summary.calls if (call.duration_seconds or 0.0) >= LONG_RUNNING_SECONDS]
    if long_running and not has_subagents:
        sample = long_running[0]
        opportunities.append(
            Opportunity(
                feature="sub-agents / awaiter",
                reason="Long-running command executed without delegation/awaiter pattern.",
                path=summary.path,
                session_timestamp=summary.session_timestamp,
                primary_prompt=prompt,
                evidence=f"{sample.command or sample.name} ({sample.duration_seconds:.1f}s)",
            )
        )

    if len(summary.calls) >= COMPLEX_TOOL_THRESHOLD and not has_plan:
        opportunities.append(
            Opportunity(
                feature="planning mode / update_plan",
                reason="High tool-call complexity with no explicit plan tracking.",
                path=summary.path,
                session_timestamp=summary.session_timestamp,
                primary_prompt=prompt,
                evidence=f"{len(summary.calls)} tool calls",
            )
        )

    if prompt and prompt_needs_web_lookup(prompt) and not has_web and summary.network_lookup_count == 0:
        opportunities.append(
            Opportunity(
                feature="web search tool",
                reason="Prompt appears time-sensitive but session shows no web lookup.",
                path=summary.path,
                session_timestamp=summary.session_timestamp,
                primary_prompt=prompt,
                evidence=clean_prompt(prompt, limit=180),
            )
        )

    if prompt and IMAGE_TASK_RE.search(prompt) and not has_view_image:
        opportunities.append(
            Opportunity(
                feature="image input/view_image",
                reason="Task appears image/UI-heavy with no image tool usage.",
                path=summary.path,
                session_timestamp=summary.session_timestamp,
                primary_prompt=prompt,
                evidence=clean_prompt(prompt, limit=180),
            )
        )

    if summary.permission_error_count >= 2 and not has_request_user_input:
        opportunities.append(
            Opportunity(
                feature="request_user_input",
                reason="Repeated permission/approval friction without explicit user choice collection.",
                path=summary.path,
                session_timestamp=summary.session_timestamp,
                primary_prompt=prompt,
                evidence=f"{summary.permission_error_count} permission-related errors",
            )
        )

    write_shell_calls = [
        call
        for call in summary.calls
        if call.name in SHELL_TOOL_NAMES and is_write_command(call.command)
    ]
    if len(write_shell_calls) >= 3 and not has_apply_patch:
        sample = write_shell_calls[0]
        opportunities.append(
            Opportunity(
                feature="apply_patch",
                reason="Multiple shell-based file edits where structured patching could reduce risk.",
                path=summary.path,
                session_timestamp=summary.session_timestamp,
                primary_prompt=prompt,
                evidence=sample.command or sample.name,
            )
        )

    if prompt and BATCH_TASK_RE.search(prompt_lower) and len(summary.calls) >= 30 and not has_subagents:
        opportunities.append(
            Opportunity(
                feature="spawn_agents_on_csv / sub-agents",
                reason="Batch-like task with high call volume and no fan-out delegation.",
                path=summary.path,
                session_timestamp=summary.session_timestamp,
                primary_prompt=prompt,
                evidence=f"{len(summary.calls)} tool calls; prompt suggests batch scope",
            )
        )

    return opportunities


def summarize_feature_usage(sessions: list[SessionSummary]) -> list[dict[str, Any]]:
    """Roll up usage statistics for core Codex capabilities."""
    feature_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for summary in sessions:
        tools = summary.tools
        calls = len(summary.calls)
        used = {
            "apply_patch": tools.get("apply_patch", 0) > 0,
            "update_plan": tools.get("update_plan", 0) > 0 or summary.collaboration_modes.get("plan", 0) > 0,
            "sub_agents": any(
                tools.get(name, 0) > 0 for name in ("spawn_agent", "spawn_agents_on_csv", "wait", "close_agent")
            ),
            "request_user_input": tools.get("request_user_input", 0) > 0,
            "view_image": tools.get("view_image", 0) > 0 or summary.input_images > 0,
            "web_search": summary.web_events > 0,
            "parallel": tools.get("parallel", 0) > 0 or tools.get("multi_tool_use.parallel", 0) > 0,
            "skills_signal": any("$skill-" in msg or "SKILL.md" in msg for msg in summary.user_messages),
            "long_running_session": any((call.duration_seconds or 0) >= LONG_RUNNING_SECONDS for call in summary.calls),
            "complex_session": calls >= COMPLEX_TOOL_THRESHOLD,
        }
        for feature, used_value in used.items():
            feature_counts[feature]["sessions_used" if used_value else "sessions_unused"] += 1

    rows: list[dict[str, Any]] = []
    for feature, counts in sorted(feature_counts.items()):
        used_count = counts["sessions_used"]
        unused_count = counts["sessions_unused"]
        total = used_count + unused_count
        adoption = (used_count / total) if total else 0.0
        rows.append(
            {
                "feature": feature,
                "sessions_used": used_count,
                "sessions_unused": unused_count,
                "adoption_rate": round(adoption, 4),
            }
        )
    return rows


def parse_date_only(value: str | None) -> datetime | None:
    """Parse YYYY-MM-DD into UTC datetime for release-window math."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def summarize_recent_feature_coverage(sessions: list[SessionSummary]) -> list[dict[str, Any]]:
    """Track adoption of recent Codex features with post-release windows."""
    specs: list[dict[str, Any]] = [
        {
            "feature": "request_user_input_in_default_mode",
            "release_date": "2026-02-26",
            "detection": "tool:request_user_input",
        },
        {
            "feature": "spawn_agents_on_csv",
            "release_date": "2026-02-25",
            "detection": "tool:spawn_agents_on_csv",
        },
        {
            "feature": "sub_agent_workflows",
            "release_date": "2026-02-25",
            "detection": "tools:spawn_agent/wait/send_input/close_agent",
        },
        {
            "feature": "parallel_tool_orchestration",
            "release_date": "2026-02-04",
            "detection": "tool:parallel",
        },
        {
            "feature": "manual_parallel_shell_patterns",
            "release_date": "2026-02-04",
            "detection": "shell contains '&' or 'xargs -P' or ' parallel '",
        },
        {
            "feature": "web_search_events",
            "release_date": "2026-01-28",
            "detection": "web_search/open_page/find events",
        },
        {
            "feature": "memory_commands_slash",
            "release_date": "2026-02-12",
            "detection": "user text contains /m_update or /m_drop",
        },
        {
            "feature": "statusline_slash_command",
            "release_date": "2026-02-11",
            "detection": "user text contains /statusline",
        },
        {
            "feature": "debug_config_slash_command",
            "release_date": "2026-02-05",
            "detection": "user text contains /debug-config",
        },
        {
            "feature": "clear_copy_slash_commands",
            "release_date": "2026-02-25",
            "detection": "user text contains /clear or /copy",
        },
        {
            "feature": "theme_slash_command",
            "release_date": "2026-02-25",
            "detection": "user text contains /theme",
        },
        {
            "feature": "permissions_slash_command",
            "release_date": "2026-02-17",
            "detection": "user text contains /permissions",
        },
        {
            "feature": "experimental_slash_command",
            "release_date": "2026-02-26",
            "detection": "user text contains /experimental",
        },
        {
            "feature": "agent_slash_command",
            "release_date": "2026-02-25",
            "detection": "user text contains /agent",
        },
        {
            "feature": "resume_slash_command",
            "release_date": "2025-09-15",
            "detection": "user text contains /resume",
        },
        {
            "feature": "voice_transcription_config",
            "release_date": "2026-02-25",
            "detection": "user text or command contains features.voice_transcription",
        },
        {
            "feature": "js_repl_experimental_usage",
            "release_date": "2026-02-26",
            "detection": "tool name includes js_repl or text contains js_repl",
        },
        {
            "feature": "escalated_sandbox_permission_requests",
            "release_date": "2026-02-25",
            "detection": "shell tool args include sandbox_permissions=require_escalated",
        },
        {
            "feature": "gpt_5_3_codex_model_usage",
            "release_date": "2026-02-05",
            "detection": "turn_context model is gpt-5.3-codex",
        },
        {
            "feature": "skills_workflows",
            "release_date": "2025-12-19",
            "detection": "messages mention $skill- or SKILL.md",
        },
        {
            "feature": "plan_mode_or_update_plan",
            "release_date": "2026-02-02",
            "detection": "update_plan tool or plan mode context",
        },
        {
            "feature": "codex_resume_usage",
            "release_date": "2025-09-15",
            "detection": "shell/user text contains 'codex resume'",
        },
        {
            "feature": "model_switching_commands",
            "release_date": "2025-09-15",
            "detection": "shell/user text contains '--model' or '/model'",
        },
    ]

    rows: list[dict[str, Any]] = []
    session_ts_cache: dict[str, datetime | None] = {
        summary.path: parse_timestamp(summary.session_timestamp) for summary in sessions
    }

    for spec in specs:
        feature = spec["feature"]
        release_dt = parse_date_only(spec["release_date"])
        used_total = 0
        used_after_release = 0
        eligible_after_release = 0
        first_seen: datetime | None = None
        last_seen: datetime | None = None

        for summary in sessions:
            ts = session_ts_cache.get(summary.path)
            if release_dt and ts and ts >= release_dt:
                eligible_after_release += 1

            raw_text_blob = "\n".join(summary.user_messages).lower()
            task_text_blob = "\n".join(filtered_user_messages(summary.user_messages)).lower()
            has_feature = False
            if feature == "request_user_input_in_default_mode":
                has_feature = summary.tools.get("request_user_input", 0) > 0
            elif feature == "spawn_agents_on_csv":
                has_feature = summary.tools.get("spawn_agents_on_csv", 0) > 0
            elif feature == "sub_agent_workflows":
                has_feature = any(
                    summary.tools.get(name, 0) > 0
                    for name in ("spawn_agent", "wait", "send_input", "close_agent", "spawn_agents_on_csv")
                )
            elif feature == "parallel_tool_orchestration":
                has_feature = summary.tools.get("parallel", 0) > 0 or summary.tools.get("multi_tool_use.parallel", 0) > 0
            elif feature == "manual_parallel_shell_patterns":
                has_feature = any(
                    call.name in SHELL_TOOL_NAMES
                    and call.command
                    and (
                        " &" in call.command
                        or "xargs -P" in call.command
                        or " parallel " in call.command
                        or call.command.strip().startswith("parallel ")
                    )
                    for call in summary.calls
                )
            elif feature == "web_search_events":
                has_feature = summary.web_events > 0
            elif feature == "memory_commands_slash":
                has_feature = has_slash_command(task_text_blob, "m_update") or has_slash_command(task_text_blob, "m_drop")
            elif feature == "statusline_slash_command":
                has_feature = has_slash_command(task_text_blob, "statusline")
            elif feature == "debug_config_slash_command":
                has_feature = has_slash_command(task_text_blob, "debug-config")
            elif feature == "clear_copy_slash_commands":
                has_feature = has_slash_command(task_text_blob, "clear") or has_slash_command(task_text_blob, "copy")
            elif feature == "theme_slash_command":
                has_feature = has_slash_command(task_text_blob, "theme")
            elif feature == "permissions_slash_command":
                has_feature = has_slash_command(task_text_blob, "permissions")
            elif feature == "experimental_slash_command":
                has_feature = has_slash_command(task_text_blob, "experimental")
            elif feature == "agent_slash_command":
                has_feature = has_slash_command(task_text_blob, "agent")
            elif feature == "resume_slash_command":
                has_feature = has_slash_command(task_text_blob, "resume")
            elif feature == "voice_transcription_config":
                has_feature = "features.voice_transcription" in task_text_blob or any(
                    command_contains(call, "features.voice_transcription") for call in summary.calls
                )
            elif feature == "js_repl_experimental_usage":
                has_feature = any("js_repl" in name for name in summary.tools) or "js_repl" in task_text_blob
            elif feature == "escalated_sandbox_permission_requests":
                has_feature = any(
                    call.name in SHELL_TOOL_NAMES
                    and isinstance((args_obj := safe_json_loads(call.arguments)), dict)
                    and args_obj.get("sandbox_permissions") == "require_escalated"
                    for call in summary.calls
                )
            elif feature == "gpt_5_3_codex_model_usage":
                has_feature = any(model == "gpt-5.3-codex" for model in summary.models)
            elif feature == "skills_workflows":
                has_feature = (
                    "$skill-" in raw_text_blob
                    or "skill.md" in raw_text_blob
                    or any(command_contains(call, "SKILL.md") for call in summary.calls)
                )
            elif feature == "plan_mode_or_update_plan":
                has_feature = summary.tools.get("update_plan", 0) > 0 or summary.collaboration_modes.get("plan", 0) > 0
            elif feature == "codex_resume_usage":
                has_feature = "codex resume" in task_text_blob or any(
                    command_contains(call, "codex resume") for call in summary.calls
                )
            elif feature == "model_switching_commands":
                has_feature = (
                    has_slash_command(task_text_blob, "model")
                    or "--model" in task_text_blob
                    or any(command_contains(call, "--model") for call in summary.calls)
                )

            if not has_feature:
                continue

            used_total += 1
            if release_dt and ts and ts >= release_dt:
                used_after_release += 1

            if ts is not None:
                if first_seen is None or ts < first_seen:
                    first_seen = ts
                if last_seen is None or ts > last_seen:
                    last_seen = ts

        rows.append(
            {
                "feature": feature,
                "release_date": spec["release_date"],
                "detection": spec["detection"],
                "sessions_used_total": used_total,
                "sessions_eligible_after_release": eligible_after_release,
                "sessions_used_after_release": used_after_release,
                "adoption_after_release": round(used_after_release / eligible_after_release, 4)
                if eligible_after_release
                else 0.0,
                "first_seen_session": first_seen.isoformat() if first_seen else "",
                "last_seen_session": last_seen.isoformat() if last_seen else "",
            }
        )

    return rows


def parse_session_file(path: Path) -> SessionSummary:
    """Dispatch parser by extension/content shape."""
    if path.suffix == ".jsonl":
        return parse_jsonl_session(path)
    if path.suffix == ".json":
        return parse_rollout_json_session(path)
    return SessionSummary(path=str(path), file_type=path.suffix.lstrip(".") or "unknown")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    """Write dictionaries to CSV with fixed columns."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def analyze(session_root: Path, changelog_txt: Path, out_dir: Path) -> dict[str, Any]:
    """Run the full analysis pipeline and write machine-readable outputs."""
    files = sorted(p for p in session_root.rglob("*") if p.is_file() and p.suffix in {".jsonl", ".json"})
    sessions = [parse_session_file(path) for path in files]
    sessions = [summary for summary in sessions if summary.user_messages or summary.calls]

    all_tools = Counter()
    all_events = Counter()
    all_commands = Counter()
    all_models = Counter()
    model_sessions = Counter()
    model_first_seen: dict[str, datetime] = {}
    model_last_seen: dict[str, datetime] = {}
    tool_outcomes: dict[str, Counter[str]] = defaultdict(Counter)
    command_outcomes: dict[str, Counter[str]] = defaultdict(Counter)
    for summary in sessions:
        all_tools.update(summary.tools)
        all_events.update(summary.event_types)
        all_models.update(summary.models)
        ts = parse_timestamp(summary.session_timestamp)
        for model in summary.models:
            model_sessions[model] += 1
            if ts is not None:
                if model not in model_first_seen or ts < model_first_seen[model]:
                    model_first_seen[model] = ts
                if model not in model_last_seen or ts > model_last_seen[model]:
                    model_last_seen[model] = ts
        for call in summary.calls:
            if call.base_command:
                all_commands[call.base_command] += 1
            outcome_key = "failed" if call.failed else "succeeded"
            tool_outcomes[call.name][outcome_key] += 1
            if call.base_command:
                command_outcomes[call.base_command][outcome_key] += 1

    timestamps = [parse_timestamp(summary.session_timestamp) for summary in sessions]
    timestamps = [ts for ts in timestamps if ts is not None]
    opportunities = [opp for summary in sessions for opp in find_opportunities(summary)]
    feature_usage_rows = summarize_feature_usage(sessions)
    recent_feature_rows = summarize_recent_feature_coverage(sessions)
    release_bullets = parse_changelog_bullets(changelog_txt)

    by_feature = Counter(opp.feature for opp in opportunities)
    summary_json: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "session_root": str(session_root),
        "session_count": len(sessions),
        "file_count": len(files),
        "date_range": {
            "start": min(timestamps).isoformat() if timestamps else None,
            "end": max(timestamps).isoformat() if timestamps else None,
        },
        "top_tools": all_tools.most_common(30),
        "top_event_types": all_events.most_common(30),
        "top_base_commands": all_commands.most_common(40),
        "models_by_turn_context": all_models.most_common(30),
        "model_session_coverage": [
            {
                "model": model,
                "sessions": count,
                "first_seen": model_first_seen[model].isoformat() if model in model_first_seen else "",
                "last_seen": model_last_seen[model].isoformat() if model in model_last_seen else "",
            }
            for model, count in model_sessions.most_common()
        ],
        "tool_failure_rates": [
            {
                "tool": tool,
                "total": counts["failed"] + counts["succeeded"],
                "failed": counts["failed"],
                "failure_rate": round(
                    counts["failed"] / (counts["failed"] + counts["succeeded"]), 4
                )
                if (counts["failed"] + counts["succeeded"])
                else 0.0,
            }
            for tool, counts in sorted(
                tool_outcomes.items(),
                key=lambda item: item[1]["failed"] + item[1]["succeeded"],
                reverse=True,
            )
        ],
        "command_failure_rates": [
            {
                "base_command": cmd,
                "total": counts["failed"] + counts["succeeded"],
                "failed": counts["failed"],
                "failure_rate": round(
                    counts["failed"] / (counts["failed"] + counts["succeeded"]), 4
                )
                if (counts["failed"] + counts["succeeded"])
                else 0.0,
            }
            for cmd, counts in sorted(
                command_outcomes.items(),
                key=lambda item: item[1]["failed"] + item[1]["succeeded"],
                reverse=True,
            )
        ],
        "feature_usage": feature_usage_rows,
        "recent_feature_coverage": recent_feature_rows,
        "opportunity_counts": by_feature.most_common(),
        "opportunities": [asdict(opp) for opp in opportunities],
        "release_bullets_count": len(release_bullets),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "session_analysis.json").write_text(json.dumps(summary_json, indent=2), encoding="utf-8")

    session_rows = [
        {
            "path": summary.path,
            "file_type": summary.file_type,
            "session_timestamp": summary.session_timestamp or "",
            "primary_prompt": summary.primary_prompt,
            "user_message_count": summary.user_message_count,
            "tool_call_count": len(summary.calls),
            "web_events": summary.web_events,
            "input_images": summary.input_images,
            "permission_errors": summary.permission_error_count,
            "network_lookups": summary.network_lookup_count,
            "top_tools": ", ".join(f"{name}:{count}" for name, count in summary.tools.most_common(6)),
        }
        for summary in sessions
    ]
    write_csv(
        out_dir / "sessions_summary.csv",
        session_rows,
        [
            "path",
            "file_type",
            "session_timestamp",
            "primary_prompt",
            "user_message_count",
            "tool_call_count",
            "web_events",
            "input_images",
            "permission_errors",
            "network_lookups",
            "top_tools",
        ],
    )

    write_csv(
        out_dir / "feature_usage.csv",
        feature_usage_rows,
        ["feature", "sessions_used", "sessions_unused", "adoption_rate"],
    )
    write_csv(
        out_dir / "recent_feature_coverage.csv",
        recent_feature_rows,
        [
            "feature",
            "release_date",
            "detection",
            "sessions_used_total",
            "sessions_eligible_after_release",
            "sessions_used_after_release",
            "adoption_after_release",
            "first_seen_session",
            "last_seen_session",
        ],
    )

    write_csv(
        out_dir / "opportunities.csv",
        [asdict(opp) for opp in opportunities],
        ["feature", "reason", "path", "session_timestamp", "primary_prompt", "evidence"],
    )

    write_csv(
        out_dir / "tool_failure_rates.csv",
        summary_json["tool_failure_rates"],
        ["tool", "total", "failed", "failure_rate"],
    )
    write_csv(
        out_dir / "command_failure_rates.csv",
        summary_json["command_failure_rates"],
        ["base_command", "total", "failed", "failure_rate"],
    )
    write_csv(
        out_dir / "model_session_coverage.csv",
        summary_json["model_session_coverage"],
        ["model", "sessions", "first_seen", "last_seen"],
    )

    release_rows = [asdict(bullet) for bullet in release_bullets]
    write_csv(
        out_dir / "release_bullets.csv",
        release_rows,
        ["date", "month", "title", "section", "text"],
    )

    return summary_json


app = typer.Typer(add_completion=False)


@app.command()
def main(
    session_root: Path = typer.Option(Path("sessions"), help="Root folder containing Codex session logs."),
    changelog_txt: Path = typer.Option(
        Path("analysis_sources/codex-changelog.txt"), help="Text dump of Codex changelog."
    ),
    out_dir: Path = typer.Option(Path("analysis_output"), help="Directory for generated outputs."),
) -> None:
    """Analyze sessions and emit JSON/CSV artifacts for reporting."""
    if not session_root.exists():
        raise typer.Exit(code=1)

    summary = analyze(session_root=session_root, changelog_txt=changelog_txt, out_dir=out_dir)
    typer.echo(f"Sessions analyzed: {summary['session_count']}")
    typer.echo(f"Opportunities detected: {len(summary['opportunities'])}")
    typer.echo(f"Outputs: {out_dir}")


if __name__ == "__main__":
    app()
