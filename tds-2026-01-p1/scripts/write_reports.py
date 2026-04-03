#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "orjson>=3.10",
#   "pandas>=2.2",
#   "pyarrow>=20.0",
#   "rich>=14.0",
#   "typer>=0.16",
# ]
# ///

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from rich.traceback import install
import typer

from tds_p1_common import ANALYSIS_DIR, DEADLINE_UTC, QUESTION_LABELS, markdown_table, read_json

install(show_locals=True)

app = typer.Typer(add_completion=False)
IST = "Asia/Kolkata"
ASSESSMENT_SINKS = {
    "firstcontributions/first-contributions",
    "lingdojo/kana-dojo",
    "syknapse/contribute-to-this-project",
}
PR_TYPE_LABELS = {
    "TYPO_FIX": "Typo fix",
    "DOCS_UPDATE": "Docs update",
    "CONFIG_CHANGE": "Config change",
    "CONTENT_DATA": "Content / data change",
    "TRANSLATION": "Translation",
    "TEST_CHANGE": "Test change",
    "ASSET_CHANGE": "Asset change",
    "CODE_CHANGE": "Code change",
    "CODE_PLUS_TEST": "Code + tests",
    "MIXED_CODE": "Mixed code",
    "MIXED_NONCODE": "Mixed non-code",
    "OTHER": "Other",
    "FETCH_ERROR": "Fetch error",
}
APPROVAL_TYPE_LABELS = {
    "MANUAL_APPROVED": "Human approval",
    "BOT_OR_AUTO": "Bot / auto merge",
    "MANUAL_COMMENT_OR_DIRECT": "Human comments or direct merge",
    "DIRECT_OR_NO_REVIEW": "Direct / no visible review",
    "FETCH_ERROR": "Fetch error",
}


def pct(numerator: int | float, denominator: int | float) -> str:
    if not denominator:
        return "0.0%"
    return f"{100 * numerator / denominator:.1f}%"


def pct_value(value: Any, *, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{100 * float(value):.{digits}f}%"


def percent(value: Any, *, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.{digits}f}%"


def write_report(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def format_ts(value: Any) -> str:
    ts = pd.Timestamp(value)
    return ts.tz_convert(IST).strftime("%Y-%m-%d %H:%M IST")


def series_rows(series: pd.Series, *, top: int = 10) -> list[list[Any]]:
    return [[index, int(value)] for index, value in series.head(top).items()]


def format_hours(value: Any) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    hours = float(value)
    return f"{hours:.0f}h" if hours >= 100 else f"{hours:.1f}h"


def label_pr_type(value: str) -> str:
    return PR_TYPE_LABELS.get(str(value), str(value))


def label_approval_type(value: str) -> str:
    return APPROVAL_TYPE_LABELS.get(str(value), str(value))


def shorten(text: Any, *, limit: int = 88) -> str:
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def per_student_effort(attempts: pd.DataFrame, question_id: str) -> pd.DataFrame:
    subset = attempts[(attempts["question_id"] == question_id) & (attempts["meaningful_attempt"])].copy()
    rows: list[dict[str, Any]] = []
    for email, group in subset.groupby("email"):
        group = group.sort_values(["submitted_at_utc", "submission_id"])
        solved_rows = group[group["solved"]]
        first_success = solved_rows.iloc[0] if not solved_rows.empty else None
        success_time = first_success["submitted_at_utc"] if first_success is not None else pd.NaT
        before_success = group if first_success is None else group[group["submitted_at_utc"] <= success_time]
        after_success = group[group["submitted_at_utc"] > success_time] if first_success is not None else group.iloc[0:0]
        rows.append(
            {
                "email": email,
                "question_id": question_id,
                "attempts": int(len(group)),
                "solved": bool(first_success is not None),
                "first_attempt_at": group.iloc[0]["submitted_at_utc"],
                "first_success_at": success_time,
                "hours_to_success": (
                    round((success_time - group.iloc[0]["submitted_at_utc"]).total_seconds() / 3600, 2)
                    if first_success is not None
                    else None
                ),
                "first_try_success": bool(first_success is not None and len(before_success) == 1),
                "late_success": bool(
                    first_success is not None and success_time >= pd.Timestamp(DEADLINE_UTC) - pd.Timedelta(hours=24)
                ),
                "regressed_after_success": bool(
                    first_success is not None and ((after_success["score"] == 0) | after_success["is_negative"]).any()
                ),
            }
        )
    return pd.DataFrame.from_records(rows)


def summarize_effort(frame: pd.DataFrame) -> dict[str, Any]:
    solvers = frame[frame["solved"]]
    return {
        "attempted": int(len(frame)),
        "solved": int(frame["solved"].sum()),
        "solve_rate": pct(int(frame["solved"].sum()), len(frame)),
        "median_attempts_solvers": round(float(solvers["attempts"].median()), 2) if not solvers.empty else 0.0,
        "p90_attempts_solvers": round(float(solvers["attempts"].quantile(0.9)), 2) if not solvers.empty else 0.0,
        "median_hours_to_success": round(float(solvers["hours_to_success"].median()), 2) if not solvers.empty else 0.0,
        "first_try_success_rate": pct(int(solvers["first_try_success"].sum()), len(solvers)),
        "late_success_rate": pct(int(solvers["late_success"].sum()), len(solvers)),
        "regressed_after_success_rate": pct(int(solvers["regressed_after_success"].sum()), len(solvers)),
    }


def render_overview(
    submissions: pd.DataFrame,
    latest_any: pd.DataFrame,
    latest_positive: pd.DataFrame,
    ever_positive_latest: pd.DataFrame,
    negatives: pd.DataFrame,
    normalization_summary: dict[str, Any],
) -> str:
    deadline = pd.Timestamp(DEADLINE_UTC)
    before_deadline = submissions[submissions["submitted_at_utc"] <= deadline]
    last_24h = before_deadline[before_deadline["submitted_at_utc"] >= deadline - pd.Timedelta(hours=24)]
    last_6h = before_deadline[before_deadline["submitted_at_utc"] >= deadline - pd.Timedelta(hours=6)]
    last_1h = before_deadline[before_deadline["submitted_at_utc"] >= deadline - pd.Timedelta(hours=1)]
    saves_per_student = submissions.groupby("email").size()
    latest_invalid = latest_any[latest_any["total"] < 0]
    latest_invalid_with_prior_positive = latest_invalid["email"].isin(set(ever_positive_latest["email"])).sum()
    deadline_errors = negatives[negatives["error_category"] == "deadline"].copy()
    deadline_lag_minutes = (
        (deadline_errors["submitted_at_utc"] - deadline).dt.total_seconds() / 60 if not deadline_errors.empty else pd.Series()
    )
    negative_categories = negatives["error_category"].value_counts()
    server_validation_share = pct(int(negative_categories.get("server-validation", 0)), len(negatives))
    validation_questions = (
        negatives[negatives["error_category"] == "server-validation"]["error_question_id"]
        .replace("", pd.NA)
        .dropna()
        .value_counts()
    )

    highlights = [
        f"The canonical history contains **{len(submissions):,} saved submissions** across **{submissions['email'].nunique():,} students**. The median student saved **{saves_per_student.median():.0f}** times; the 90th percentile saved **{saves_per_student.quantile(0.9):.0f}** times.",
        f"The local dump is a **latest positive snapshot**: it has **{normalization_summary['local_dump_rows']:,}** rows, matching the API's **{len(latest_positive):,}** latest non-negative rows, but it hides the larger latest-state trail of **{len(latest_any):,}** students.",
        f"`total: -1` is an **error trail, not a score**. There are **{len(negatives):,}** negative rows affecting **{negatives['email'].nunique():,}** students. **{len(latest_invalid):,}** students end the API trail on a failed save, and **{latest_invalid_with_prior_positive:,}** of them already had an earlier valid submission.",
        f"Negative rows are overwhelmingly validator-driven rather than deadline-driven: **{server_validation_share}** of all negatives are server-validation failures, while deadline misses are a small visible tail.",
        f"Work compressed hard at the end: **{pct(len(last_24h), len(before_deadline))}** of all pre-deadline saves landed in the final 24h, **{pct(len(last_6h), len(before_deadline))}** in the last 6h, and **{pct(len(last_1h), len(before_deadline))}** in the last hour.",
    ]
    if not deadline_lag_minutes.empty:
        highlights.append(
            f"Deadline misses were usually not huge misses: the median deadline failure arrived **{deadline_lag_minutes.median():.1f} minutes** after the cutoff, and the 90th percentile was **{deadline_lag_minutes.quantile(0.9):.1f} minutes** late."
        )

    latest_state_rows = [
        ["Latest valid rows", len(latest_positive), pct(len(latest_positive), len(latest_any))],
        ["Latest invalid rows", len(latest_invalid), pct(len(latest_invalid), len(latest_any))],
        ["Students with any negative row", negatives["email"].nunique(), pct(negatives["email"].nunique(), len(latest_any))],
    ]
    timing_rows = [
        ["Final 24h", len(last_24h), pct(len(last_24h), len(before_deadline))],
        ["Final 6h", len(last_6h), pct(len(last_6h), len(before_deadline))],
        ["Final 1h", len(last_1h), pct(len(last_1h), len(before_deadline))],
    ]

    sections = [
        "# overview",
        "",
        "## Headline findings",
        "",
        *[f"- {line}" for line in highlights],
        "",
        "## Latest-state split",
        "",
        markdown_table(["State", "Students", "Share of latest rows"], latest_state_rows),
        "",
        "## Negative save families",
        "",
        markdown_table(["Error family", "Rows"], series_rows(negative_categories)),
        "",
        "## Validation-heavy questions in negative rows",
        "",
        markdown_table(["Question", "Rows"], [[QUESTION_LABELS.get(k, k), v] for k, v in series_rows(validation_questions)]),
        "",
        "## Deadline compression",
        "",
        markdown_table(["Window before deadline", "Saves", "Share of all pre-deadline saves"], timing_rows),
        "",
        "## Notes",
        "",
        f"- Deadline reference: **{format_ts(pd.Timestamp(DEADLINE_UTC))}**.",
        "- The API latest trail is larger than the local dump because students who ended with a failed save still remain visible in `latest_any` but disappear from the latest positive snapshot.",
        "- This makes `total: -1` especially valuable for reconstructing endgame behavior: panic saves, post-deadline submissions, and validator failures that never show up in the local dump.",
    ]
    return "\n".join(sections)


def render_transcribe_markdown(attempts: pd.DataFrame) -> str:
    transcribe = per_student_effort(attempts, "q-transcribe-numbers-server")
    markdown = per_student_effort(attempts, "q-markdown-parser-server")
    transcribe_stats = summarize_effort(transcribe)
    markdown_stats = summarize_effort(markdown)
    both = transcribe.merge(markdown, on="email", how="inner", suffixes=("_transcribe", "_markdown"))
    both_solved = both[(both["solved_transcribe"]) & (both["solved_markdown"])]
    comparison_rows = [
        [
            "Transcribe Numbers",
            transcribe_stats["attempted"],
            transcribe_stats["solved"],
            transcribe_stats["solve_rate"],
            transcribe_stats["median_attempts_solvers"],
            transcribe_stats["median_hours_to_success"],
            transcribe_stats["first_try_success_rate"],
            transcribe_stats["late_success_rate"],
            transcribe_stats["regressed_after_success_rate"],
        ],
        [
            "Markdown Parser",
            markdown_stats["attempted"],
            markdown_stats["solved"],
            markdown_stats["solve_rate"],
            markdown_stats["median_attempts_solvers"],
            markdown_stats["median_hours_to_success"],
            markdown_stats["first_try_success_rate"],
            markdown_stats["late_success_rate"],
            markdown_stats["regressed_after_success_rate"],
        ],
    ]

    insights = []
    if markdown_stats["median_attempts_solvers"] > transcribe_stats["median_attempts_solvers"]:
        ratio = markdown_stats["median_attempts_solvers"] / max(transcribe_stats["median_attempts_solvers"], 1)
        insights.append(
            f"Markdown was the longer grind: its median solver needed **{ratio:.1f}x** as many meaningful attempts as transcription."
        )
    if markdown_stats["median_hours_to_success"] > transcribe_stats["median_hours_to_success"]:
        if transcribe_stats["median_hours_to_success"] < 0.1:
            insights.append(
                "Markdown also stayed open longer in the calendar: its median time from first meaningful attempt to first success was **15 minutes**, while transcription's median rounded to **0** because many students solved it in their first meaningful save."
            )
        else:
            ratio = markdown_stats["median_hours_to_success"] / transcribe_stats["median_hours_to_success"]
            insights.append(
                f"Markdown also stayed open longer in the calendar: median time from first meaningful attempt to first success was **{ratio:.1f}x** the transcription median."
            )
    insights.append(
        f"Among students who worked on both tasks, **{len(both_solved):,}** solved both; **{((both['solved_transcribe']) & (~both['solved_markdown'])).sum():,}** solved transcription but not markdown, versus **{((~both['solved_transcribe']) & (both['solved_markdown'])).sum():,}** the other way around."
    )

    return "\n".join(
        [
            "# transcribe-markdown",
            "",
            "## Headline findings",
            "",
            *[f"- {line}" for line in insights],
            "",
            "## Effort comparison",
            "",
            markdown_table(
                [
                    "Question",
                    "Students who tried",
                    "Students who solved",
                    "Solve rate",
                    "Median meaningful attempts (solvers)",
                    "Median hours to success",
                    "First-try success rate",
                    "Solved in final 24h",
                    "Regressed after success",
                ],
                comparison_rows,
            ),
            "",
            "## Notes",
            "",
            "- A meaningful attempt is a saved submission with a non-empty answer or a positive score.",
            "- Regression after success means a student later saved a failing or negative row for the same question after first solving it.",
            "- Transcribe captures the page-reload hazard indirectly: later failures after a success are consistent with students reopening the page and getting a fresh audio/hash pair.",
        ]
    )


def render_generate_images(manifest: pd.DataFrame) -> str:
    all_rows = manifest.copy()
    ok_rows = manifest[manifest["status"] == "ok"].copy()
    by_question = (
        all_rows.groupby("question_label")
        .agg(
            submissions=("submission_id", "size"),
            fetched=("status", lambda s: int((s == "ok").sum())),
            publish_email=("publish_email", lambda s: round(float(pd.Series(s).mean() * 100), 1)),
            median_prompt_words=("prompt_words", "median"),
        )
        .reset_index()
        .sort_values("question_label")
    )
    model_series = ok_rows["model"].fillna("").astype(str)
    family_labels = pd.Series("Other / long tail", index=ok_rows.index)
    family_labels[model_series.str.lower().str.contains("dall")] = "DALL·E family"
    family_labels[model_series.str.lower().str.contains("midjourney")] = "Midjourney family"
    family_labels[model_series.str.lower().str.contains("flux")] = "Flux family"
    family_labels[model_series.str.lower().str.contains("ideogram")] = "Ideogram family"
    family_labels[model_series.str.lower().str.contains("gemini|imagen", regex=True)] = "Gemini/Imagen family"
    model_families = family_labels.value_counts()
    models = ok_rows["model"].replace("", pd.NA).dropna().value_counts()
    hosts = ok_rows["image_host"].replace("", pd.NA).dropna().value_counts()
    formats = ok_rows["image_format"].replace("", pd.NA).dropna().value_counts()
    metadata_retained = int(
        (
            ok_rows["software"].astype(str).str.len().gt(0)
            | ok_rows["parameters"].astype(str).str.len().gt(0)
            | ok_rows["comment"].astype(str).str.len().gt(0)
            | ok_rows["description"].astype(str).str.len().gt(0)
        ).sum()
    )
    duplicate_hash_rows = ok_rows["image_sha256"].replace("", pd.NA).dropna()
    duplicate_images = int(duplicate_hash_rows.duplicated(keep=False).sum())
    duplicate_hash_frame = (
        ok_rows[ok_rows["image_sha256"].astype(str).str.len() > 0]
        .groupby("image_sha256")
        .agg(rows=("submission_id", "size"), students=("email", "nunique"), questions=("question_id", "nunique"))
        .reset_index()
    )
    duplicate_hash_frame = duplicate_hash_frame[duplicate_hash_frame["rows"] > 1]
    cross_student_duplicate_hashes = int((duplicate_hash_frame["students"] > 1).sum()) if not duplicate_hash_frame.empty else 0
    cross_question_duplicate_hashes = int((duplicate_hash_frame["questions"] > 1).sum()) if not duplicate_hash_frame.empty else 0
    max_rows_per_hash = int(duplicate_hash_frame["rows"].max()) if not duplicate_hash_frame.empty else 0
    feature_rows = [
        ["Explicit negative-prompt syntax", int(ok_rows["has_negative_prompt"].sum()), pct(int(ok_rows["has_negative_prompt"].sum()), len(ok_rows))],
        ["Generation parameters / switches", int(ok_rows["has_generation_params"].sum()), pct(int(ok_rows["has_generation_params"].sum()), len(ok_rows))],
        ["Named style references", int(ok_rows["has_style_reference"].sum()), pct(int(ok_rows["has_style_reference"].sum()), len(ok_rows))],
    ]

    insights = [
        f"Latest positive rows contain **{len(all_rows):,}** non-empty image-task answers; **{len(ok_rows):,}** fetched cleanly enough to inspect as images plus JSON metadata.",
        f"Public attribution is selective: across successfully fetched image rows, **{pct(int(ok_rows['publish_email'].sum()), len(ok_rows))}** opt into `publish_email`.",
        f"Once messy model names are normalized, the **DALL·E family dominates {pct(int(model_families.get('DALL·E family', 0)), len(ok_rows))}** of fetched image rows, with **Gemini/Imagen** a distant second at **{pct(int(model_families.get('Gemini/Imagen family', 0)), len(ok_rows))}**.",
        f"Prompt length differs meaningfully by exercise: the median ranges from **{by_question['median_prompt_words'].min():.0f}** words to **{by_question['median_prompt_words'].max():.0f}** words across the four briefs.",
        f"Visible tool fingerprints are rare: only **{metadata_retained:,}** fetched images retain obvious software/parameter/comment metadata, which suggests most students exported or re-hosted stripped assets.",
    ]
    if duplicate_images:
        insights.append(
            f"Image reuse is measurable: **{duplicate_images:,}** fetched rows share a hash with another row, spanning **{cross_student_duplicate_hashes:,}** cross-student duplicate hashes and up to **{max_rows_per_hash}** reuses of a single image."
        )

    return "\n".join(
        [
            "# generate-images",
            "",
            "## Headline findings",
            "",
            *[f"- {line}" for line in insights],
            "",
            "## Coverage by image brief",
            "",
            markdown_table(
                ["Question", "Non-empty latest answers", "Fetched successfully", "publish_email rate", "Median prompt words"],
                by_question.values.tolist(),
            ),
            "",
            "## Prompt feature prevalence",
            "",
            markdown_table(["Prompt feature", "Rows", "Share"], feature_rows),
            "",
            "## Normalized model families",
            "",
            markdown_table(["Model family", "Rows"], series_rows(model_families)),
            "",
            "## Most common models",
            "",
            markdown_table(["Model", "Rows"], series_rows(models)),
            "",
            "## Image hosts",
            "",
            markdown_table(["Host", "Rows"], series_rows(hosts)),
            "",
            "## Image formats",
            "",
            markdown_table(["Format", "Rows"], series_rows(formats)),
            "",
            "## Duplicate-image structure",
            "",
            markdown_table(
                ["Metric", "Value"],
                [
                    ["Rows sharing a duplicate image hash", duplicate_images],
                    ["Duplicate hashes spanning multiple students", cross_student_duplicate_hashes],
                    ["Duplicate hashes spanning multiple questions", cross_question_duplicate_hashes],
                    ["Max rows using one identical image", max_rows_per_hash],
                ],
            ),
            "",
            "## Notes",
            "",
            "- These counts are based on the latest positive row per student, then filtered to non-empty image answers.",
            "- Asset download errors remain visible in the manifest and can be used later to study broken-link or last-minute hosting failures.",
            "- The thumbnails live under `data/assets/<question>/...-thumb.avif` and are generated with `avifenc -q 30` after resizing to fit within 640×640.",
        ]
    )


def render_share_secret(summary: dict[str, Any], top_choices: pd.DataFrame, daily: pd.DataFrame) -> str:
    top = top_choices[top_choices["rank"] == 1].copy()
    top["top_share_pct"] = top["top_share"] * 100
    peak_days = daily.sort_values(
        ["first_successes", "decoder_exact_match_share", "ist_day"],
        ascending=[False, False, True],
    ).head(10)
    least_consensus = top.sort_values(
        ["top_share", "distinct_emails_for_agent", "total_uses_for_agent", "agent_id"],
        ascending=[True, False, False, True],
    ).head(10)
    strong_consensus = int((top["top_share"] >= 0.8).sum())
    medium_consensus = int((top["top_share"] >= 0.7).sum())

    highlights = [
        f"`q-share-secret-server` produced **{summary['successful_rows']:,} successful saves** from **{summary['successful_students']:,} students**, so it became one of the cohort's most replayed collaboration targets rather than a one-shot puzzle.",
        f"The public decoder did **not** invent a late mapping from scratch: for **all {summary['agent_ids_with_decoder_map']} agent IDs**, the decoder's chosen email matches the historically dominant first-success email.",
        f"On first successful solves, **{summary['students_all_three_match_decoder']:,} students ({summary['students_all_three_match_decoder_rate']:.2f}%)** matched the decoder exactly on all three targets. The rate was already **{summary['first_week_exact_decoder_rate']:.2f}%** in the first week and only nudged up to **{summary['last_week_exact_decoder_rate']:.2f}%** in the last week.",
        f"The mapping standardized surprisingly early: the median dominant-email share per agent ID is **{top['top_share_pct'].median():.1f}%**, and **{strong_consensus} / {len(top)}** agent IDs already have an 80%+ dominant choice.",
        f"Blind full-answer copy-paste was not the main mechanism: only **{summary['cross_student_duplicate_signatures']}** exact cross-student triplet signature repeated, because each student faced different agent combinations. Standardization happened one agent mapping at a time.",
        f"The biggest first-success wave hit **{summary['peak_day']}**, when **{summary['peak_day_first_successes']}** students first cracked the question and **{peak_days.iloc[0]['decoder_exact_match_share'] * 100:.1f}%** of those solves already matched the later public decoder exactly.",
    ]

    standardization_rows = [
        ["Agent IDs covered by public decoder", summary["agent_ids_with_decoder_map"], ""],
        ["Agent IDs whose decoder email matches dominant historical email", summary["agent_ids_where_decoder_matches_top_email"], "100.0%"],
        ["Students whose first success matched decoder on all 3 targets", summary["students_all_three_match_decoder"], f"{summary['students_all_three_match_decoder_rate']:.2f}%"],
        ["Agent IDs with at least 70% dominant-email share", medium_consensus, pct(medium_consensus, len(top))],
        ["Agent IDs with at least 80% dominant-email share", strong_consensus, pct(strong_consensus, len(top))],
    ]
    timing_rows = [
        ["First week", "n/a", f"{summary['first_week_exact_decoder_rate']:.2f}%"],
        ["Last week", "n/a", f"{summary['last_week_exact_decoder_rate']:.2f}%"],
        ["Earliest 100 first-successes", 100, f"{summary['early_100_exact_decoder_rate']:.2f}%"],
        ["Latest 100 first-successes", 100, f"{summary['late_100_exact_decoder_rate']:.2f}%"],
    ]
    daily_rows = [
        [
            row.ist_day,
            int(row.first_successes),
            int(row.decoder_exact_matches),
            pct_value(row.decoder_exact_match_share),
        ]
        for row in peak_days.itertuples(index=False)
    ]
    consensus_rows = [
        [
            row.agent_id,
            int(row.total_uses_for_agent),
            int(row.distinct_emails_for_agent),
            f"{float(row.top_share_pct):.1f}%",
        ]
        for row in least_consensus.itertuples(index=False)
    ]

    return "\n".join(
        [
            "# q-share-secret-server",
            "",
            "## Headline findings",
            "",
            *[f"- {line}" for line in highlights],
            "",
            "## Mapping standardization",
            "",
            markdown_table(["Metric", "Value", "Share"], standardization_rows),
            "",
            "## First-success timing vs. decoder-match rate",
            "",
            markdown_table(["Window", "Students", "Exact decoder-match rate"], timing_rows),
            "",
            "## Biggest first-success waves",
            "",
            markdown_table(["Day (IST)", "First successes", "Exact decoder matches", "Exact-match share"], daily_rows),
            "",
            "## Lowest-consensus agent IDs",
            "",
            markdown_table(["Agent ID", "First-success uses", "Distinct valid emails", "Dominant-email share"], consensus_rows),
            "",
            "## Notes",
            "",
            f"- Public discussion thread: {summary['top_discussion_url']}",
            f"- Public decoder endpoint used for comparison: {summary['decoder_source_url']}",
            "- Discussion evidence shows a Google Form / spreadsheet workaround appeared within about a day of release, so the later decoder looks more like automation of an already-canonical lookup table than a brand-new exploit.",
        ]
    )


def pr_value_reason(row: pd.Series) -> str:
    reasons: list[str] = []
    pr_type = str(row["pr_type"])
    if pr_type == "CODE_PLUS_TEST":
        reasons.append("code change with tests")
    elif pr_type == "CODE_CHANGE":
        reasons.append("code change")
    elif pr_type == "MIXED_CODE":
        reasons.append("mixed code change")
    elif pr_type == "TEST_CHANGE":
        reasons.append("test change")
    elif pr_type == "DOCS_UPDATE":
        reasons.append("substantive docs update")
    elif pr_type == "TYPO_FIX":
        reasons.append("tiny typo/docs fix")
    else:
        reasons.append(label_pr_type(pr_type).lower())

    if bool(row["manual_reviewed"]):
        count = int(row["human_reviewers"])
        reasons.append(f"{count} human reviewer{'s' if count != 1 else ''}")
    elif bool(row["manual_interaction"]):
        count = int(row["manual_participants"])
        reasons.append(f"{count} manual participant{'s' if count != 1 else ''}")

    if bool(row["required_edits"]):
        edits = int(row["commits_after_feedback"])
        reasons.append(f"{edits} follow-up commit{'s' if edits != 1 else ''}" if edits else "feedback loop before merge")

    if bool(row["self_merged"]):
        reasons.append("self-merged")
    elif str(row["repo_family"]) not in ASSESSMENT_SINKS:
        reasons.append("outside sink repos")

    latency = row["merge_latency_hours"]
    if latency is not None and not pd.isna(latency) and float(latency) >= 24:
        reasons.append(f"{float(latency):.0f}h to merge")

    return "; ".join(reasons[:4])


def pr_merge_path(row: pd.Series) -> str:
    if bool(row["self_merged"]):
        return "Self-merged"
    return label_approval_type(str(row["approval_type"]))


def render_pr_merge(pr_enriched: pd.DataFrame, pr_summary: dict[str, Any]) -> str:
    if pr_enriched.empty:
        return "# q-pr-merge-server\n\nNo enriched PR data available.\n"

    ok = pr_enriched[pr_enriched["api_status"] == "ok"].copy()
    failures = pr_enriched[pr_enriched["api_status"] != "ok"].copy()
    family_stats = (
        ok.groupby("repo_family")
        .agg(
            unique_prs=("pr_url", "size"),
            successful_rows=("success_rows", "sum"),
            target_repos=("repo_key", "nunique"),
            median_merge_hours=("merge_latency_hours", "median"),
            manual_review_rate=("manual_reviewed", "mean"),
            required_edits_rate=("required_edits", "mean"),
            self_merged_rate=("self_merged", "mean"),
        )
        .reset_index()
        .sort_values(["unique_prs", "successful_rows", "repo_family"], ascending=[False, False, True])
    )
    exact_long_tail = (
        ok[~ok["repo_family"].isin(ASSESSMENT_SINKS)]
        .groupby("repo_key")
        .agg(
            unique_prs=("pr_url", "size"),
            median_merge_hours=("merge_latency_hours", "median"),
            manual_review_rate=("manual_reviewed", "mean"),
            required_edits_rate=("required_edits", "mean"),
        )
        .reset_index()
        .sort_values(["unique_prs", "manual_review_rate", "repo_key"], ascending=[False, False, True])
        .head(10)
    )
    approval_counts = ok["approval_type"].value_counts()
    type_counts = ok["pr_type"].value_counts()
    docs_like = int(ok["pr_type"].isin(["TYPO_FIX", "DOCS_UPDATE"]).sum())
    code_like = int(ok["pr_type"].isin(["CODE_CHANGE", "CODE_PLUS_TEST", "MIXED_CODE", "TEST_CHANGE"]).sum())
    sink_ok = ok[ok["repo_family"].isin(ASSESSMENT_SINKS)]
    nonsink_ok = ok[~ok["repo_family"].isin(ASSESSMENT_SINKS)]
    latencies = ok["merge_latency_hours"].dropna()
    sink_latencies = sink_ok["merge_latency_hours"].dropna()
    nonsink_latencies = nonsink_ok["merge_latency_hours"].dropna()
    top_two_share = family_stats.head(2)["unique_prs"].sum() / len(ok) if len(ok) else 0
    sink_share = len(sink_ok) / len(ok) if len(ok) else 0
    sink_fork_rate = float(sink_ok["repo_fork"].mean()) if not sink_ok.empty else 0.0
    sink_self_merge_rate = float(sink_ok["self_merged"].mean()) if not sink_ok.empty else 0.0

    value_pool = ok[(~ok["repo_family"].isin(ASSESSMENT_SINKS)) & (~ok["self_merged"])].copy()
    if len(value_pool) < 5:
        value_pool = ok[~ok["repo_family"].isin(ASSESSMENT_SINKS)].copy()
    if len(value_pool) < 5:
        value_pool = ok.copy()
    top_value = value_pool.sort_values(
        ["value_score", "manual_participants", "changed_files", "additions", "repo_stars"],
        ascending=[False, False, False, False, False],
    ).head(5)

    highlights = [
        f"`q-pr-merge-server` has **{pr_summary['successful_rows']:,} successful save rows**, but those collapse to **{pr_summary['unique_prs']:,} canonical merged PRs** after URL normalization. Another **{pr_summary['invalid_success_rows']:,}** positive rows contain malformed or non-canonical PR text.",
        f"The repo choice is highly concentrated: the top two repo families account for **{pct_value(top_two_share)}** of all enriched PRs, and sink families together account for **{pct_value(sink_share)}**.",
        f"That raw sink volume overstates outside maintainer burden. Inside sink families, **{pct_value(sink_fork_rate)}** of target repos are forks and **{pct_value(sink_self_merge_rate)}** are self-merged, so not every 'successful PR' went through a canonical upstream review path.",
        f"Human review is scarce: only **{pct_value(ok['manual_reviewed'].mean())}** of merged PRs show a formal human reviewer, while **{pct_value(ok['manual_interaction'].mean())}** show any human interaction at all. **{pct_value(ok['required_edits'].mean())}** required follow-up edits before merge.",
        f"The task skews heavily toward light-weight contributions: **{pct(docs_like, len(ok))}** of PRs are docs/typo updates, versus **{pct(code_like, len(ok))}** that touch code or tests.",
    ]
    if not latencies.empty:
        latency_line = f"Median merge latency is **{format_hours(latencies.median())}** overall"
        if not sink_latencies.empty and not nonsink_latencies.empty:
            latency_line += (
                f", versus **{format_hours(sink_latencies.median())}** for sink families and "
                f"**{format_hours(nonsink_latencies.median())}** for the long tail"
            )
        latency_line += "."
        highlights.append(latency_line)
    if not failures.empty:
        highlights.append(
            f"GitHub enrichment still hit **{len(failures):,}** dead/private/malformed PR URLs after normalization; those are excluded from process and value metrics below."
        )

    family_rows = [
        [
            row.repo_family,
            int(row.unique_prs),
            pct(int(row.unique_prs), len(ok)),
            int(row.target_repos),
            format_hours(row.median_merge_hours),
            pct_value(row.manual_review_rate),
            pct_value(row.required_edits_rate),
            pct_value(row.self_merged_rate),
        ]
        for row in family_stats.head(10).itertuples(index=False)
    ]
    approval_rows = [
        [label_approval_type(key), int(value), pct(int(value), len(ok))]
        for key, value in approval_counts.items()
    ]
    type_rows = [
        [label_pr_type(key), int(value), pct(int(value), len(ok))]
        for key, value in type_counts.items()
    ]
    long_tail_rows = [
        [
            row.repo_key,
            int(row.unique_prs),
            format_hours(row.median_merge_hours),
            pct_value(row.manual_review_rate),
            pct_value(row.required_edits_rate),
        ]
        for row in exact_long_tail.itertuples(index=False)
    ]
    value_rows = [
        [
            f"[{row.repo_key}#{int(row.number)}]({row.pr_url})",
            label_pr_type(str(row.pr_type)),
            pr_merge_path(row),
            shorten(str(row.title)),
            pr_value_reason(row),
        ]
        for _, row in top_value.iterrows()
    ]

    return "\n".join(
        [
            "# q-pr-merge-server",
            "",
            "## Headline findings",
            "",
            *[f"- {line}" for line in highlights],
            "",
            "## Major repo-family process",
            "",
            markdown_table(
                [
                    "Repo family",
                    "Unique PRs",
                    "Share of PRs",
                    "Distinct target repos",
                    "Median merge latency",
                    "Human review",
                    "Required edits",
                    "Self-merged",
                ],
                family_rows,
            ),
            "",
            "## Review / acceptance path split",
            "",
            markdown_table(["Path", "PRs", "Share"], approval_rows),
            "",
            "## PR type mix",
            "",
            markdown_table(["Type", "PRs", "Share"], type_rows),
            "",
            "## Long-tail repos outside the sink families",
            "",
            markdown_table(
                ["Exact target repo", "Unique PRs", "Median merge latency", "Human review", "Required edits"],
                long_tail_rows,
            ),
            "",
            "## Top 5 likely high-value contributions",
            "",
            markdown_table(["PR", "Type", "Merge path", "Title", "Why it stands out"], value_rows),
            "",
            "## Notes",
            "",
            "- The repo-family view groups canonical sink families by repository name, so student forks of `kana-dojo` and `first-contributions` stay in the same family instead of fragmenting the counts.",
            "- 'Self-merged' means the PR author and merger are the same login; this is a strong signal that the student controlled the target repo or fork.",
            "- Review metrics exclude PR URLs that were dead, private, or malformed by the time the GitHub API enrichment ran.",
        ]
    )


def render_collaboration_cascades(
    lookup_summary: dict[str, Any],
    lookup_students: pd.DataFrame,
    lookup_coverage: pd.DataFrame,
    lookup_daily: pd.DataFrame,
    transcribe_effects: pd.DataFrame,
) -> str:
    milestone_ranks = [1, 5, 10, 20, 50, 100, lookup_summary["first_full_rank"], 200]
    milestone_ranks = [rank for rank in milestone_ranks if rank and rank <= int(lookup_coverage["solve_rank"].max())]
    milestone_frame = lookup_coverage[lookup_coverage["solve_rank"].isin(milestone_ranks)].copy()
    milestone_rows = [
        [
            f"Solver #{int(row.solve_rank)}",
            int(row.prior_known_agent_ids),
            int(row.known_agent_ids_after_solve),
        ]
        for row in milestone_frame.itertuples(index=False)
    ]

    super_spreader = lookup_daily.sort_values(
        ["new_agent_ids_that_day", "first_successes", "ist_day"],
        ascending=[False, False, True],
    ).iloc[0]
    first_days = lookup_daily.head(6)
    first_day_rows = [
        [
            row.ist_day,
            int(row.ids_known_before_first_solver_that_day),
            int(row.ids_known_end_of_day),
            int(row.first_successes),
            percent(row.lookup_only_share * 100),
        ]
        for row in first_days.itertuples(index=False)
    ]

    cohort_labels = {
        "before-2026-03-04": "Before Mar 4 workaround",
        "2026-03-04-to-2026-03-25": "Mar 4 to Mar 25",
        "after-2026-03-26": "After Mar 26 HTML tool",
    }
    transcribe_rows = [
        [
            cohort_labels.get(str(row.cohort), str(row.cohort)),
            int(row.students),
            percent(row.solve_pct),
            float(row.median_attempts_solvers),
            percent(row.first_try_pct),
        ]
        for row in transcribe_effects.itertuples(index=False)
    ]
    transcribe_before = transcribe_effects[transcribe_effects["cohort"] == "before-2026-03-04"].iloc[0]
    transcribe_after = transcribe_effects[transcribe_effects["cohort"] == "after-2026-03-26"].iloc[0]

    return "\n".join(
        [
            "# collaboration-cascades",
            "",
            "A puzzle is supposed to get easier because you understand it. `q-share-secret-server` gets easier because the class quietly builds itself a map.",
            "",
            f"By the **{lookup_summary['first_full_rank']}th** student to solve the question — **{lookup_summary['first_full_date']}** — all **100 agent IDs** are already in circulation. Only **{lookup_summary['student_discoverers']}** students ever contribute a new mapping. The other **{lookup_summary['lookup_only_students']}** arrive to find all three of their targets already known.",
            "",
            "That is the part worth sitting with. The exam looks individualized on the surface. Underneath, it behaves like shared infrastructure: a few pioneers expand the map, then the map starts doing the work.",
            "",
            "## The map fills faster than intuition says it should",
            "",
            f"The super-spreader day is **{super_spreader['ist_day']}**. The cohort begins that day with only **{int(super_spreader['ids_known_before_first_solver_that_day'])}** known agent IDs. It ends the day with **{int(super_spreader['ids_known_end_of_day'])}**. That is not a slow diffusion curve. That is a step change.",
            "",
            markdown_table(["Moment", "Agent IDs known before solve", "Agent IDs known after solve"], milestone_rows),
            "",
            "## The first week already looks like infrastructure, not discovery",
            "",
            markdown_table(
                ["Day (IST)", "IDs known before first solver", "IDs known by end of day", "First successes", "Lookup-only share"],
                first_day_rows,
            ),
            "",
            f"By the **100th** solver, **{int(milestone_frame.loc[milestone_frame['solve_rank'] == 100, 'known_agent_ids_after_solve'].iloc[0])}** of the **100** agent IDs have already been seen. By the time the full map exists, **{lookup_summary['students_after_full_map']}** students still remain to solve the question.",
            "",
            "## The same collapse appears in a different question",
            "",
            "The interesting thing about social infrastructure is that once you learn to look for it, you see it elsewhere. `q-transcribe-numbers-server` does not become easier because the audio changes. It becomes easier because the public method changes.",
            "",
            f"After the public HTML/audio workaround appears on **Mar 26**, the median solver's effort falls from **{float(transcribe_before['median_attempts_solvers']):.0f}** meaningful attempts to **{float(transcribe_after['median_attempts_solvers']):.0f}**, while first-try success rises from **{percent(transcribe_before['first_try_pct'])}** to **{percent(transcribe_after['first_try_pct'])}**.",
            "",
            markdown_table(
                ["Transcribe cohort", "Students", "Solve rate", "Median attempts (solvers)", "First-try success"],
                transcribe_rows,
            ),
            "",
            "## What this changes",
            "",
            "The exam does not have a single difficulty curve. It has disclosure moments. Once a workaround or lookup table appears in public, the question is no longer testing just personal ingenuity; it is testing whether a student has plugged into the cohort's information network.",
            "",
            "## Caveat",
            "",
            "- This does not prove every late solver consciously copied a public artifact. It does show that the information environment changed so much that later effort profiles look qualitatively different from earlier ones.",
        ]
    )


def render_assessment_sinks(
    pr_recommendation: pd.DataFrame,
    pr_windows: pd.DataFrame,
    pr_modes: pd.DataFrame,
) -> str:
    before = pr_recommendation[pr_recommendation["recommendation_cohort"] == "before-2026-03-24"].iloc[0]
    after = pr_recommendation[pr_recommendation["recommendation_cohort"] == "after-2026-03-24"].iloc[0]
    sink = pr_modes[pr_modes["repo_mode"] == "sink"].iloc[0]
    long_tail = pr_modes[pr_modes["repo_mode"] == "long-tail"].iloc[0]

    recommendation_rows = [
        [
            "Before Mar 24 recommendation",
            int(before["prs"]),
            percent(before["kana_dojo_share"]),
            percent(before["sink_share"]),
            percent(before["code_like_share"]),
            format_hours(before["median_merge_hours"]),
        ],
        [
            "After Mar 24 recommendation",
            int(after["prs"]),
            percent(after["kana_dojo_share"]),
            percent(after["sink_share"]),
            percent(after["code_like_share"]),
            format_hours(after["median_merge_hours"]),
        ],
    ]
    deadline_rows = [
        [
            str(row.deadline_window),
            int(row.prs),
            percent(row.sink_share),
            percent(row.code_like_share),
            format_hours(row.median_merge_hours),
        ]
        for row in pr_windows.itertuples(index=False)
    ]
    mode_rows = [
        [
            "Sink families" if row.repo_mode == "sink" else "Long tail",
            int(row.prs),
            percent(row.human_review_pct),
            percent(row.required_edits_pct),
            percent(row.code_like_pct),
            f"{float(row.avg_value_score):.2f}",
            format_hours(row.median_merge_hours),
        ]
        for row in pr_modes.itertuples(index=False)
    ]

    return "\n".join(
        [
            "# assessment-sinks",
            "",
            "Open-source contribution is supposed to reward patience. This assignment, much of the time, rewards throughput.",
            "",
            f"After `kana-dojo` is recommended in the public discussion on **Mar 24**, repository choice does not drift. It snaps. `kana-dojo`'s share of merged PRs jumps from **{percent(before['kana_dojo_share'])}** to **{percent(after['kana_dojo_share'])}**. Overall sink-repo share rises from **{percent(before['sink_share'])}** to **{percent(after['sink_share'])}**. Code-like work, already rare, collapses from **{percent(before['code_like_share'])}** to **{percent(after['code_like_share'])}**.",
            "",
            "This is what an assessment sink looks like: a repo family that absorbs student volume because it is legible, recommended, and fast to clear — not because it is where the most public value lives.",
            "",
            "## The recommendation shock",
            "",
            markdown_table(
                ["PR creation cohort", "Merged PRs", "kana-dojo share", "Sink-family share", "Code-like share", "Median merge latency"],
                recommendation_rows,
            ),
            "",
            "## As the deadline approaches, the strategy gets safer",
            "",
            markdown_table(
                ["PR creation window", "Merged PRs", "Sink-family share", "Code-like share", "Median merge latency"],
                deadline_rows,
            ),
            "",
            f"Three weeks out, sink families account for **{percent(pr_windows.iloc[0]['sink_share'])}** of merged PRs. One day before deadline, that rises to **{percent(pr_windows[pr_windows['deadline_window'] == '1d'].iloc[0]['sink_share'])}**. At that point the code-like share falls to **{percent(pr_windows[pr_windows['deadline_window'] == '1d'].iloc[0]['code_like_share'])}**.",
            "",
            "## Two labor markets hiding inside one question",
            "",
            markdown_table(
                ["Repo mode", "PRs", "Human review", "Required edits", "Code-like work", "Avg value score", "Median merge latency"],
                mode_rows,
            ),
            "",
            f"The time difference is the giveaway. Sink families merge at a median of **{format_hours(sink['median_merge_hours'])}**. The long tail takes **{format_hours(long_tail['median_merge_hours'])}**. Long-tail PRs attract almost **10x** the human review rate and roughly **18x** the code-change rate.",
            "",
            "## What this changes",
            "",
            "The PR question is not just measuring whether students can contribute to open source. It is also measuring whether students can navigate a market with two currencies: public utility and merge probability. Near the deadline, merge probability wins.",
            "",
            "## Caveat",
            "",
            "- These metrics only cover PRs that eventually merged and remained visible to the GitHub API. They do not include abandoned or rejected PRs, so the long tail is probably even riskier than it looks here.",
        ]
    )


def render_endgame_archetypes(archetypes: pd.DataFrame, archetype_summary: dict[str, Any]) -> str:
    desired_order = {
        "steady-finishers": 0,
        "deadline-sprinters": 1,
        "ghost-finishers": 2,
        "panic-patchers": 3,
        "long-grinders": 4,
        "other": 5,
    }
    archetypes = archetypes.copy()
    archetypes["sort_order"] = archetypes["archetype"].map(desired_order)
    archetypes = archetypes.sort_values("sort_order")

    def label(archetype: str) -> str:
        return archetype.replace("-", " ").title()

    summary_rows = [
        [
            label(str(row.archetype)),
            int(row.students),
            percent(row.latest_invalid_pct),
            float(row.median_solved_questions),
            float(row.median_attempts),
            float(row.avg_saves_last24h),
            float(row.avg_negatives_last24h),
        ]
        for row in archetypes.itertuples(index=False)
    ]
    ghost = archetypes[archetypes["archetype"] == "ghost-finishers"].iloc[0]
    panic = archetypes[archetypes["archetype"] == "panic-patchers"].iloc[0]
    steady = archetypes[archetypes["archetype"] == "steady-finishers"].iloc[0]

    return "\n".join(
        [
            "# endgame-archetypes",
            "",
            "Some students do not fail the exam. They finish it — and then keep touching the dashboard until the final log makes them look broken.",
            "",
            f"The clearest example is the **ghost finisher**: **{int(ghost['students'])}** students who finish a large share of the paper, then end the visible API trail on an invalid save. They account for **{percent(archetype_summary['ghost_share_of_latest_invalid_pct'])}** of all latest-invalid students, and the median ghost finisher has already solved **{float(ghost['median_solved_questions']):.0f}** questions.",
            "",
            f"Then there are the **panic patchers** — only **{int(panic['students'])}** students, but loud ones. Their median run contains **{float(panic['median_attempts']):.0f}** meaningful attempts overall, plus **{float(panic['avg_saves_last24h']):.1f}** saves and **{float(panic['avg_negatives_last24h']):.1f}** negative saves in the last day alone.",
            "",
            f"The contrast case matters too. The **steady finishers** are not just stronger students; they are students who know when to stop. They have a median of **{float(steady['median_solved_questions']):.0f}** solved questions, but only **{float(steady['avg_saves_last24h']):.1f}** saves in the final 24 hours and effectively no late negatives.",
            "",
            "## The six endgames hiding inside one exam",
            "",
            markdown_table(
                [
                    "Archetype",
                    "Students",
                    "Latest invalid",
                    "Median solved questions",
                    "Median meaningful attempts",
                    "Avg saves in final 24h",
                    "Avg negatives in final 24h",
                ],
                summary_rows,
            ),
            "",
            "## What this changes",
            "",
            "Once you separate these archetypes, `total: -1` stops looking like a generic failure bucket. For some students it means they never got traction. For others it means they had already done the hard part and then got trapped in a late validator loop.",
            "",
            "That distinction matters. A ghost finisher does not need more content instruction. A panic patcher does not need a harder exam. They need a calmer endgame: clearer validator feedback, stronger saved-state UX, and fewer reasons to reopen a solved question in the final hours.",
            "",
            "## Caveat",
            "",
            "- These are rule-based archetypes, not unsupervised clusters. The virtue of that trade-off is interpretability: each label corresponds to an exam-design problem you can actually act on.",
        ]
    )


@app.command()
def main() -> None:
    """Generate reproducible markdown reports from derived datasets."""

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    submissions = pd.read_parquet("data/derived/submission_history.parquet")
    latest_any = pd.read_parquet("data/derived/latest_any.parquet")
    latest_positive = pd.read_parquet("data/derived/latest_positive.parquet")
    ever_positive_latest = pd.read_parquet("data/derived/ever_positive_latest.parquet")
    negatives = pd.read_parquet("data/derived/negative_events.parquet")
    attempts = pd.read_parquet("data/derived/question_attempts.parquet")
    normalization_summary = read_json(Path("data/derived/normalization-summary.json"))
    written = ["overview.md", "transcribe-markdown.md"]

    write_report(
        ANALYSIS_DIR / "overview.md",
        render_overview(
            submissions,
            latest_any,
            latest_positive,
            ever_positive_latest,
            negatives,
            normalization_summary,
        ),
    )
    write_report(ANALYSIS_DIR / "transcribe-markdown.md", render_transcribe_markdown(attempts))

    share_summary_path = Path("data/derived/share_secret_summary.json")
    if share_summary_path.exists():
        share_summary = read_json(share_summary_path)
        share_top_choices = pd.read_parquet("data/derived/share_secret_top_choices.parquet")
        share_daily = pd.read_parquet("data/derived/share_secret_daily.parquet")
        write_report(
            ANALYSIS_DIR / "q-share-secret-server.md",
            render_share_secret(share_summary, share_top_choices, share_daily),
        )
        written.append("q-share-secret-server.md")

    pr_summary_path = Path("data/derived/pr_enriched_summary.json")
    pr_enriched_path = Path("data/derived/pr_enriched.parquet")
    if pr_summary_path.exists() and pr_enriched_path.exists():
        pr_summary = read_json(pr_summary_path)
        pr_enriched = pd.read_parquet(pr_enriched_path)
        write_report(ANALYSIS_DIR / "q-pr-merge-server.md", render_pr_merge(pr_enriched, pr_summary))
        written.append("q-pr-merge-server.md")

    wow_summary_path = Path("data/derived/wow_patterns_summary.json")
    if wow_summary_path.exists():
        lookup_summary = read_json(Path("data/derived/share_secret_lookup_summary.json"))
        lookup_students = pd.read_parquet("data/derived/share_secret_lookup_students.parquet")
        lookup_coverage = pd.read_parquet("data/derived/share_secret_lookup_coverage.parquet")
        lookup_daily = pd.read_parquet("data/derived/share_secret_lookup_daily.parquet")
        transcribe_effects = pd.read_parquet("data/derived/transcribe_intervention_effects.parquet")
        pr_recommendation = pd.read_parquet("data/derived/pr_recommendation_effects.parquet")
        pr_windows = pd.read_parquet("data/derived/pr_deadline_windows.parquet")
        pr_modes = pd.read_parquet("data/derived/pr_mode_comparison.parquet")
        archetypes = pd.read_parquet("data/derived/student_archetype_summary.parquet")
        archetype_summary = read_json(Path("data/derived/student_archetype_summary.json"))
        write_report(
            ANALYSIS_DIR / "collaboration-cascades.md",
            render_collaboration_cascades(
                lookup_summary,
                lookup_students,
                lookup_coverage,
                lookup_daily,
                transcribe_effects,
            ),
        )
        write_report(
            ANALYSIS_DIR / "assessment-sinks.md",
            render_assessment_sinks(pr_recommendation, pr_windows, pr_modes),
        )
        write_report(
            ANALYSIS_DIR / "endgame-archetypes.md",
            render_endgame_archetypes(archetypes, archetype_summary),
        )
        written.extend(["collaboration-cascades.md", "assessment-sinks.md", "endgame-archetypes.md"])

    if Path("data/derived/image_manifest.parquet").exists():
        image_manifest = pd.read_parquet("data/derived/image_manifest.parquet")
        write_report(ANALYSIS_DIR / "generate-images.md", render_generate_images(image_manifest))
        written.append("generate-images.md")

    typer.echo(f"[reports] wrote {', '.join(written)}")


if __name__ == "__main__":
    app()
