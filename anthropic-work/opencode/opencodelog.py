#!/usr/bin/env python3
"""Convert OpenCode logs to Markdown format."""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sys


def load_json(filepath):
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}", file=sys.stderr)
        return None


def format_timestamp(timestamp_ms):
    """Convert timestamp in milliseconds to readable format."""
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')


def escape_markdown(text):
    """Escape markdown special characters in text."""
    if not text:
        return ""
    # Don't escape text that's already in code blocks
    return text


def format_tool_call(part):
    """Format a tool call part into Markdown."""
    state = part.get('state', {})
    tool_name = part.get('tool', 'unknown')
    status = state.get('status', 'unknown')
    input_data = state.get('input', {})
    output = state.get('output', '')

    md = f"**Tool: {tool_name}** (Status: {status})\n\n"

    # Add input details
    if input_data:
        md += "**Input:**\n```json\n"
        md += json.dumps(input_data, indent=2)
        md += "\n```\n\n"

    # Add output if available
    if output:
        md += "**Output:**\n```\n"
        md += output.strip()
        md += "\n```\n"

    return md


def format_reasoning(part):
    """Format a reasoning part into Markdown."""
    text = part.get('text', '')
    return f"**Reasoning:** {escape_markdown(text)}\n\n"


def format_text(part):
    """Format a text part into Markdown."""
    text = part.get('text', '')
    return f"{escape_markdown(text)}\n\n"


def format_part(part):
    """Format a single part based on its type."""
    part_type = part.get('type', 'unknown')

    if part_type == 'text':
        return format_text(part)
    elif part_type == 'reasoning':
        return format_reasoning(part)
    elif part_type == 'tool':
        return format_tool_call(part)
    elif part_type == 'step-start':
        return ""  # Skip step-start markers
    else:
        return f"*[{part_type}]*\n\n"


def get_message_parts(storage_path, message_id):
    """Get all parts for a message, sorted by filename."""
    parts_dir = storage_path / 'part' / message_id
    if not parts_dir.exists():
        return []

    parts = []
    for part_file in sorted(parts_dir.glob('*.json')):
        part_data = load_json(part_file)
        if part_data:
            parts.append(part_data)

    return parts


def summarize_message(message, parts):
    """Create a summary for a message based on its parts."""
    role = message.get('role', 'unknown')

    if role == 'user':
        # For user messages, just get the first text part
        for part in parts:
            if part.get('type') == 'text':
                text = part.get('text', '')
                # Truncate long messages
                if len(text) > 100:
                    return text[:100] + "..."
                return text
        return "User message"
    else:
        # For assistant messages, count tools used
        tool_count = sum(1 for p in parts if p.get('type') == 'tool')
        reasoning_count = sum(1 for p in parts if p.get('type') == 'reasoning')

        summary_parts = []
        if reasoning_count > 0:
            summary_parts.append(f"{reasoning_count} reasoning step(s)")
        if tool_count > 0:
            summary_parts.append(f"{tool_count} tool call(s)")

        if summary_parts:
            return ", ".join(summary_parts)
        return "Assistant response"


def format_message(storage_path, message):
    """Format a single message into Markdown."""
    role = message.get('role', 'unknown')
    message_id = message.get('id', '')

    # Get all parts for this message
    parts = get_message_parts(storage_path, message_id)

    if role == 'user':
        md = "## User Message\n\n"
        for part in parts:
            if part.get('type') == 'text':
                md += format_text(part)
        return md

    elif role == 'assistant':
        md = "## Agent Message\n\n"

        # Get message metadata
        model_id = message.get('modelID', 'unknown')
        tokens = message.get('tokens', {})

        # Create summary
        summary = summarize_message(message, parts)

        # Start collapsible section
        md += f"<details><summary><strong>{summary}</strong></summary>\n\n"

        # Add metadata
        md += f"**Model:** {model_id}\n\n"
        if tokens:
            md += f"**Tokens:** Input: {tokens.get('input', 0)}, Output: {tokens.get('output', 0)}"
            if tokens.get('reasoning'):
                md += f", Reasoning: {tokens.get('reasoning', 0)}"
            cache = tokens.get('cache', {})
            if cache:
                md += f", Cache Read: {cache.get('read', 0)}, Cache Write: {cache.get('write', 0)}"
            md += "\n\n"

        md += "---\n\n"

        # Add all parts
        for part in parts:
            part_md = format_part(part)
            if part_md:
                md += part_md

        md += "</details>\n\n"
        return md

    return ""


def process_session(storage_path, session_file):
    """Process a single session and generate Markdown."""
    session = load_json(session_file)
    if not session:
        return ""

    session_id = session.get('id', '')
    title = session.get('title', 'Untitled Session')
    created = format_timestamp(session.get('time', {}).get('created', 0))
    directory = session.get('directory', '')

    md = f"# Session: {title}\n\n"
    md += f"**ID:** `{session_id}`\n\n"
    md += f"**Created:** {created}\n\n"
    md += f"**Directory:** `{directory}`\n\n"
    md += "---\n\n"

    # Get all messages for this session
    message_dir = storage_path / 'message' / session_id
    if not message_dir.exists():
        md += "*No messages found for this session.*\n\n"
        return md

    # Load and sort messages by creation time
    messages = []
    for msg_file in message_dir.glob('*.json'):
        msg = load_json(msg_file)
        if msg:
            messages.append(msg)

    messages.sort(key=lambda m: m.get('time', {}).get('created', 0))

    # Format each message
    for message in messages:
        md += format_message(storage_path, message)

    return md


def main():
    """Main function to convert OpenCode logs to Markdown."""
    storage_path = Path(__file__).parent

    # Get all sessions
    session_dir = storage_path / 'session' / 'global'
    if not session_dir.exists():
        print("No sessions found!", file=sys.stderr)
        return

    session_files = sorted(session_dir.glob('*.json'))

    if not session_files:
        print("No session files found!", file=sys.stderr)
        return

    # Load sessions and sort by creation time
    sessions = []
    for session_file in session_files:
        session = load_json(session_file)
        if session:
            sessions.append((session_file, session))

    sessions.sort(key=lambda x: x[1].get('time', {}).get('created', 0))

    # Generate markdown for all sessions
    output_md = "# OpenCode Session Logs\n\n"
    output_md += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    output_md += f"Total sessions: {len(sessions)}\n\n"
    output_md += "---\n\n"

    for session_file, session in sessions:
        output_md += process_session(storage_path, session_file)
        output_md += "\n\n"

    # Write output
    output_file = storage_path / 'session_logs.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_md)

    print(f"✓ Generated Markdown log: {output_file}")
    print(f"✓ Processed {len(sessions)} sessions")


if __name__ == '__main__':
    main()
