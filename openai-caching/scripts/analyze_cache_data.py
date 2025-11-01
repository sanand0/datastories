#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer>=0.12",
#     "orjson>=3.9",
#     "tabulate>=0.9",
# ]
# ///

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import orjson
import typer
from tabulate import tabulate


app = typer.Typer(help="Summarise cache experiment JSONL logs.")


def load_rows(path: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    with path.open("rb") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(orjson.loads(line))
    return rows


@app.command()
def summarize(
    log_path: Path = typer.Argument(..., exists=True, readable=True),
    output_path: Path = typer.Option(None, help="Optional markdown output path."),
) -> None:
    rows = load_rows(log_path)
    grouped: Dict[tuple[str, str], List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(row["strategy"], row["length_label"])].append(row)

    tables: List[str] = []
    for (strategy, length_label), items in sorted(grouped.items()):
        display_rows = []
        for item in sorted(items, key=lambda r: r["stage"]):
            usage = item["response"].get("body_json", {}).get("usage") or {}
            details = usage.get("prompt_tokens_details") or {}
            display_rows.append(
                [
                    item["stage"],
                    usage.get("prompt_tokens"),
                    details.get("cached_tokens"),
                    f"{item['elapsed_ms']:.0f} ms",
                    item.get("message_count"),
                    item.get("local_prompt_token_estimate"),
                ],
            )
        header = f"{strategy} / {length_label}"
        tables.append(
            header + "\n" + tabulate(
                display_rows,
                headers=["stage", "prompt_tokens", "cached_tokens", "elapsed", "messages", "local_estimate"],
                tablefmt="github",
            ),
        )

    output = "\n\n".join(tables)
    typer.echo(output)
    if output_path:
        output_path.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    app()
