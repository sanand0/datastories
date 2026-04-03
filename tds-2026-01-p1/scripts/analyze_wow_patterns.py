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

from datetime import UTC, datetime
from typing import Any

import pandas as pd
from rich.traceback import install
import typer

from tds_p1_common import DEADLINE_UTC, DERIVED_DIR, write_json

install(show_locals=True)

app = typer.Typer(add_completion=False)

IST = "Asia/Kolkata"
SINK_FAMILIES = {
    "firstcontributions/first-contributions",
    "lingdojo/kana-dojo",
    "syknapse/contribute-to-this-project",
}
CODE_LIKE_TYPES = {"CODE_CHANGE", "CODE_PLUS_TEST", "MIXED_CODE", "TEST_CHANGE"}
DOCS_LIKE_TYPES = {"TYPO_FIX", "DOCS_UPDATE"}
TRANSCRIBE_PHASES = [
    ("before-2026-03-04", pd.Timestamp("2026-03-04T00:00:00+00:00")),
    ("2026-03-04-to-2026-03-25", pd.Timestamp("2026-03-26T00:00:00+00:00")),
    ("after-2026-03-26", None),
]
PR_RECOMMENDATION_AT = pd.Timestamp("2026-03-24T00:00:00+00:00")


def first_success_lookup() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Measure when q-share-secret turned from exploration into lookup."""

    flat = pd.read_parquet(DERIVED_DIR / "share_secret_first_success_flat.parquet").copy()
    flat["submitted_at_utc"] = pd.to_datetime(flat["submitted_at_utc"], utc=True)
    solvers = (
        flat.groupby(["solver_email", "submission_id"], as_index=False)["submitted_at_utc"]
        .min()
        .sort_values(["submitted_at_utc", "submission_id", "solver_email"])
        .reset_index(drop=True)
    )
    solvers["solve_rank"] = solvers.index + 1

    flat = flat.merge(
        solvers[["solver_email", "submission_id", "solve_rank"]],
        on=["solver_email", "submission_id"],
        how="left",
    ).sort_values(["solve_rank", "agent_id", "solver_email"])
    flat["prior_hits"] = flat.groupby("agent_id").cumcount()

    first_seen_counts = (
        flat.groupby("agent_id")["solve_rank"]
        .min()
        .value_counts()
        .sort_index()
        .rename("new_agent_ids_at_rank")
    )
    coverage = pd.DataFrame({"solve_rank": range(1, len(solvers) + 1)})
    coverage["new_agent_ids_at_rank"] = (
        coverage["solve_rank"].map(first_seen_counts).fillna(0).astype(int)
    )
    coverage["prior_known_agent_ids"] = (
        coverage["new_agent_ids_at_rank"].cumsum().shift(fill_value=0).astype(int)
    )
    coverage["known_agent_ids_after_solve"] = (
        coverage["prior_known_agent_ids"] + coverage["new_agent_ids_at_rank"]
    )

    per_solver = (
        flat.groupby(["solver_email", "submission_id", "submitted_at_utc"], as_index=False)
        .agg(
            solve_rank=("solve_rank", "min"),
            known_targets=("prior_hits", lambda s: int((s > 0).sum())),
            new_targets=("prior_hits", lambda s: int((s == 0).sum())),
        )
        .merge(coverage, on="solve_rank", how="left")
        .sort_values("solve_rank")
        .reset_index(drop=True)
    )
    per_solver["all_targets_previously_known"] = per_solver["known_targets"] == 3
    per_solver["ist_day"] = per_solver["submitted_at_utc"].dt.tz_convert(IST).dt.strftime("%Y-%m-%d")

    daily = (
        per_solver.groupby("ist_day", as_index=False)
        .agg(
            first_successes=("submission_id", "size"),
            ids_known_before_first_solver_that_day=("prior_known_agent_ids", "min"),
            ids_known_before_last_solver_that_day=("prior_known_agent_ids", "max"),
            ids_known_end_of_day=("known_agent_ids_after_solve", "max"),
            lookup_only_students=("all_targets_previously_known", "sum"),
        )
        .sort_values("ist_day")
        .reset_index(drop=True)
    )
    daily["new_agent_ids_that_day"] = (
        daily["ids_known_end_of_day"] - daily["ids_known_before_first_solver_that_day"]
    )
    daily["lookup_only_share"] = daily["lookup_only_students"] / daily["first_successes"]

    full_map_ranks = coverage.loc[coverage["prior_known_agent_ids"] == 100, "solve_rank"]
    first_full_rank = int(full_map_ranks.min()) if not full_map_ranks.empty else 0
    first_full_date = ""
    if first_full_rank:
        first_full_date = (
            per_solver.loc[per_solver["solve_rank"] == first_full_rank, "submitted_at_utc"]
            .iloc[0]
            .tz_convert(IST)
            .strftime("%Y-%m-%d")
        )

    super_spreader = daily.sort_values(
        ["new_agent_ids_that_day", "first_successes", "ist_day"],
        ascending=[False, False, True],
    ).iloc[0]
    early = per_solver.head(100)
    late = per_solver.tail(100)
    summary = {
        "students": int(len(per_solver)),
        "student_discoverers": int((per_solver["new_targets"] > 0).sum()),
        "lookup_only_students": int(per_solver["all_targets_previously_known"].sum()),
        "lookup_only_student_share": round(float(per_solver["all_targets_previously_known"].mean() * 100), 2),
        "first_full_rank": first_full_rank,
        "first_full_date": first_full_date,
        "students_after_full_map": int((per_solver["solve_rank"] > first_full_rank).sum()) if first_full_rank else 0,
        "early_100_all_known_share": round(float(early["all_targets_previously_known"].mean() * 100), 2),
        "late_100_all_known_share": round(float(late["all_targets_previously_known"].mean() * 100), 2),
        "super_spreader_day": str(super_spreader["ist_day"]),
        "super_spreader_new_agent_ids": int(super_spreader["new_agent_ids_that_day"]),
        "super_spreader_first_successes": int(super_spreader["first_successes"]),
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }
    return per_solver, coverage, daily, summary


def transcribe_interventions(attempts: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compare q-transcribe effort before and after public tool-sharing moments."""

    subset = attempts[
        (attempts["question_id"] == "q-transcribe-numbers-server") & attempts["meaningful_attempt"]
    ].copy()
    subset["submitted_at_utc"] = pd.to_datetime(subset["submitted_at_utc"], utc=True)

    first_attempt = subset.groupby("email", as_index=False)["submitted_at_utc"].min().rename(
        columns={"submitted_at_utc": "first_attempt_at"}
    )
    first_success = (
        subset[subset["solved"]]
        .groupby("email", as_index=False)["submitted_at_utc"]
        .min()
        .rename(columns={"submitted_at_utc": "first_success_at"})
    )
    per_student = (
        subset.groupby("email", as_index=False)
        .agg(
            attempts=("submission_id", "size"),
            solved_any=("solved", "max"),
        )
        .merge(first_attempt, on="email", how="left")
        .merge(first_success, on="email", how="left")
    )
    per_student["minutes_to_success"] = (
        (per_student["first_success_at"] - per_student["first_attempt_at"]).dt.total_seconds() / 60
    )

    def phase_label(value: pd.Timestamp) -> str:
        if value < TRANSCRIBE_PHASES[0][1]:
            return TRANSCRIBE_PHASES[0][0]
        if value < TRANSCRIBE_PHASES[1][1]:
            return TRANSCRIBE_PHASES[1][0]
        return TRANSCRIBE_PHASES[2][0]

    per_student["cohort"] = per_student["first_attempt_at"].map(phase_label)
    cohort_order = [label for label, _ in TRANSCRIBE_PHASES]
    per_student["cohort"] = pd.Categorical(per_student["cohort"], categories=cohort_order, ordered=True)

    rows: list[dict[str, Any]] = []
    for cohort, group in per_student.groupby("cohort", observed=True):
        solvers = group[group["solved_any"]].copy()
        rows.append(
            {
                "cohort": str(cohort),
                "students": int(len(group)),
                "solve_pct": round(float(group["solved_any"].mean() * 100), 2),
                "median_attempts_solvers": float(solvers["attempts"].median()) if not solvers.empty else 0.0,
                "first_try_pct": round(float((solvers["attempts"] == 1).mean() * 100), 2) if not solvers.empty else 0.0,
                "median_minutes_to_success": float(solvers["minutes_to_success"].median()) if not solvers.empty else 0.0,
            }
        )
    effects = pd.DataFrame.from_records(rows)
    baseline = effects[effects["cohort"] == "before-2026-03-04"].iloc[0]
    after_tool = effects[effects["cohort"] == "after-2026-03-26"].iloc[0]
    summary = {
        "attempts_drop_after_tool_share": round(
            float(baseline["median_attempts_solvers"] - after_tool["median_attempts_solvers"]),
            2,
        ),
        "first_try_multiplier_after_tool_share": round(
            float(after_tool["first_try_pct"] / baseline["first_try_pct"]),
            2,
        )
        if baseline["first_try_pct"]
        else 0.0,
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }
    return effects, summary


def pr_strategy() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Measure how public repo advice changed PR strategy and quality."""

    pr = pd.read_parquet(DERIVED_DIR / "pr_enriched.parquet").copy()
    pr = pr[(pr["api_status"] == "ok") & pr["created_at"].notna()].copy()
    pr["created_at"] = pd.to_datetime(pr["created_at"], utc=True)
    pr["repo_mode"] = pr["repo_family"].isin(SINK_FAMILIES).map({True: "sink", False: "long-tail"})
    pr["code_like"] = pr["pr_type"].isin(CODE_LIKE_TYPES)
    pr["docs_like"] = pr["pr_type"].isin(DOCS_LIKE_TYPES)
    pr["kana_dojo"] = pr["repo_family"].eq("lingdojo/kana-dojo")
    pr["days_before_deadline"] = (pd.Timestamp(DEADLINE_UTC) - pr["created_at"]).dt.days
    pr["recommendation_cohort"] = pr["created_at"].lt(PR_RECOMMENDATION_AT).map(
        {True: "before-2026-03-24", False: "after-2026-03-24"}
    )

    recommendation = (
        pr.groupby("recommendation_cohort", as_index=False)
        .agg(
            prs=("pr_url", "size"),
            kana_dojo_share=("kana_dojo", "mean"),
            sink_share=("repo_mode", lambda s: float((s == "sink").mean())),
            code_like_share=("code_like", "mean"),
            median_merge_hours=("merge_latency_hours", "median"),
        )
        .sort_values("recommendation_cohort")
        .reset_index(drop=True)
    )
    recommendation[["kana_dojo_share", "sink_share", "code_like_share"]] *= 100

    def deadline_window(days: int) -> str:
        if days >= 21:
            return ">=21d"
        if days >= 7:
            return "7-20d"
        if days >= 2:
            return "2-6d"
        if days >= 1:
            return "1d"
        return "<24h"

    pr["deadline_window"] = pr["days_before_deadline"].map(deadline_window)
    window_order = [">=21d", "7-20d", "2-6d", "1d", "<24h"]
    deadline_windows = (
        pr.groupby("deadline_window", as_index=False)
        .agg(
            prs=("pr_url", "size"),
            sink_share=("repo_mode", lambda s: float((s == "sink").mean())),
            code_like_share=("code_like", "mean"),
            median_merge_hours=("merge_latency_hours", "median"),
        )
        .assign(deadline_window=lambda frame: pd.Categorical(frame["deadline_window"], categories=window_order, ordered=True))
        .sort_values("deadline_window")
        .reset_index(drop=True)
    )
    deadline_windows[["sink_share", "code_like_share"]] *= 100

    mode_comparison = (
        pr.groupby("repo_mode", as_index=False)
        .agg(
            prs=("pr_url", "size"),
            human_review_pct=("manual_reviewed", lambda s: float(s.mean() * 100)),
            required_edits_pct=("required_edits", lambda s: float(s.mean() * 100)),
            code_like_pct=("code_like", lambda s: float(s.mean() * 100)),
            docs_like_pct=("docs_like", lambda s: float(s.mean() * 100)),
            avg_value_score=("value_score", "mean"),
            median_merge_hours=("merge_latency_hours", "median"),
        )
        .sort_values("repo_mode")
        .reset_index(drop=True)
    )
    mode_comparison["avg_value_score"] = mode_comparison["avg_value_score"].round(2)

    before = recommendation[recommendation["recommendation_cohort"] == "before-2026-03-24"].iloc[0]
    after = recommendation[recommendation["recommendation_cohort"] == "after-2026-03-24"].iloc[0]
    summary = {
        "kana_dojo_share_before_pct": round(float(before["kana_dojo_share"]), 2),
        "kana_dojo_share_after_pct": round(float(after["kana_dojo_share"]), 2),
        "sink_share_before_pct": round(float(before["sink_share"]), 2),
        "sink_share_after_pct": round(float(after["sink_share"]), 2),
        "code_like_before_pct": round(float(before["code_like_share"]), 2),
        "code_like_after_pct": round(float(after["code_like_share"]), 2),
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }
    return recommendation, deadline_windows, mode_comparison, summary


def student_archetypes(attempts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Build endgame behavior archetypes from student sequences."""

    deadline = pd.Timestamp(DEADLINE_UTC)
    last_24h = deadline - pd.Timedelta(hours=24)
    last_6h = deadline - pd.Timedelta(hours=6)

    meaningful = attempts[attempts["meaningful_attempt"]].copy()
    meaningful["submitted_at_utc"] = pd.to_datetime(meaningful["submitted_at_utc"], utc=True)

    first_success = (
        meaningful[meaningful["solved"]]
        .groupby(["email", "question_id"], as_index=False)["submitted_at_utc"]
        .min()
        .rename(columns={"submitted_at_utc": "first_success_at"})
    )
    per_question = (
        meaningful.groupby(["email", "question_id"], as_index=False)
        .agg(
            attempts=("submission_id", "size"),
            solved_any=("solved", "max"),
        )
        .merge(first_success, on=["email", "question_id"], how="left")
    )

    per_student = (
        per_question.groupby("email", as_index=False)
        .agg(
            solved_questions=("solved_any", "sum"),
            total_meaningful_attempts=("attempts", "sum"),
            questions_first_solved_last24h=("first_success_at", lambda s: int(s.ge(last_24h).fillna(False).sum())),
            questions_first_solved_last6h=("first_success_at", lambda s: int(s.ge(last_6h).fillna(False).sum())),
        )
    )

    history = pd.read_parquet(DERIVED_DIR / "submission_history.parquet").copy()
    history["submitted_at_utc"] = pd.to_datetime(history["submitted_at_utc"], utc=True)
    history["in_last24h"] = history["submitted_at_utc"] >= last_24h
    history["in_last6h"] = history["submitted_at_utc"] >= last_6h
    history["negative_last24h"] = history["is_negative"] & history["in_last24h"]
    history["negative_last6h"] = history["is_negative"] & history["in_last6h"]
    submission_rollup = (
        history.groupby("email", as_index=False)
        .agg(
            saves=("submission_id", "size"),
            negatives=("is_negative", "sum"),
            saves_last24h=("in_last24h", "sum"),
            saves_last6h=("in_last6h", "sum"),
            negatives_last24h=("negative_last24h", "sum"),
            negatives_last6h=("negative_last6h", "sum"),
        )
    )

    latest_any = pd.read_parquet(DERIVED_DIR / "latest_any.parquet")[["email", "total", "is_negative"]].rename(
        columns={"total": "latest_total", "is_negative": "latest_invalid"}
    )
    students = (
        per_student.merge(submission_rollup, on="email", how="left")
        .merge(latest_any, on="email", how="left")
        .fillna(
            {
                "saves": 0,
                "negatives": 0,
                "saves_last24h": 0,
                "saves_last6h": 0,
                "negatives_last24h": 0,
                "negatives_last6h": 0,
                "latest_total": -1,
                "latest_invalid": True,
            }
        )
    )

    def classify(row: pd.Series) -> str:
        if bool(row["latest_invalid"]) and row["solved_questions"] >= 8:
            return "ghost-finishers"
        if row["saves_last24h"] >= 10 and row["negatives_last24h"] >= 3 and row["solved_questions"] >= 8:
            return "panic-patchers"
        if row["questions_first_solved_last24h"] >= 4 and not bool(row["latest_invalid"]):
            return "deadline-sprinters"
        if row["solved_questions"] >= 8 and row["negatives"] == 0 and row["questions_first_solved_last24h"] <= 1:
            return "steady-finishers"
        if row["solved_questions"] <= 4 and row["total_meaningful_attempts"] >= 30:
            return "long-grinders"
        return "other"

    students["archetype"] = students.apply(classify, axis=1)
    summary = (
        students.groupby("archetype", as_index=False)
        .agg(
            students=("email", "size"),
            latest_invalid_pct=("latest_invalid", lambda s: float(s.mean() * 100)),
            median_latest_total=("latest_total", "median"),
            median_solved_questions=("solved_questions", "median"),
            median_attempts=("total_meaningful_attempts", "median"),
            avg_saves_last24h=("saves_last24h", "mean"),
            avg_negatives_last24h=("negatives_last24h", "mean"),
        )
    )
    summary[["latest_invalid_pct", "avg_saves_last24h", "avg_negatives_last24h"]] = summary[
        ["latest_invalid_pct", "avg_saves_last24h", "avg_negatives_last24h"]
    ].round(2)

    latest_invalid_total = int(students["latest_invalid"].sum())
    ghost_count = int((students["archetype"] == "ghost-finishers").sum())
    panic_count = int((students["archetype"] == "panic-patchers").sum())
    summary_json = {
        "students": int(len(students)),
        "latest_invalid_students": latest_invalid_total,
        "ghost_finishers": ghost_count,
        "ghost_share_of_latest_invalid_pct": round(100 * ghost_count / latest_invalid_total, 2) if latest_invalid_total else 0.0,
        "panic_patchers": panic_count,
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }
    return students, summary, summary_json


@app.command()
def main() -> None:
    """Build additional derived tables for phase transitions, PR strategy, and endgame archetypes."""

    attempts = pd.read_parquet(DERIVED_DIR / "question_attempts.parquet").copy()
    attempts["submitted_at_utc"] = pd.to_datetime(attempts["submitted_at_utc"], utc=True)

    lookup_students, lookup_coverage, lookup_daily, lookup_summary = first_success_lookup()
    lookup_students.to_parquet(DERIVED_DIR / "share_secret_lookup_students.parquet", index=False)
    lookup_coverage.to_parquet(DERIVED_DIR / "share_secret_lookup_coverage.parquet", index=False)
    lookup_daily.to_parquet(DERIVED_DIR / "share_secret_lookup_daily.parquet", index=False)
    write_json(DERIVED_DIR / "share_secret_lookup_summary.json", lookup_summary)

    transcribe_effects, transcribe_summary = transcribe_interventions(attempts)
    transcribe_effects.to_parquet(DERIVED_DIR / "transcribe_intervention_effects.parquet", index=False)
    write_json(DERIVED_DIR / "transcribe_intervention_summary.json", transcribe_summary)

    pr_recommendation, pr_windows, pr_modes, pr_summary = pr_strategy()
    pr_recommendation.to_parquet(DERIVED_DIR / "pr_recommendation_effects.parquet", index=False)
    pr_windows.to_parquet(DERIVED_DIR / "pr_deadline_windows.parquet", index=False)
    pr_modes.to_parquet(DERIVED_DIR / "pr_mode_comparison.parquet", index=False)
    write_json(DERIVED_DIR / "pr_strategy_summary.json", pr_summary)

    archetype_students, archetype_summary, archetype_summary_json = student_archetypes(attempts)
    archetype_students.to_parquet(DERIVED_DIR / "student_archetypes.parquet", index=False)
    archetype_summary.to_parquet(DERIVED_DIR / "student_archetype_summary.parquet", index=False)
    write_json(DERIVED_DIR / "student_archetype_summary.json", archetype_summary_json)

    write_json(
        DERIVED_DIR / "wow_patterns_summary.json",
        {
            "share_secret_lookup": lookup_summary,
            "transcribe_interventions": transcribe_summary,
            "pr_strategy": pr_summary,
            "student_archetypes": archetype_summary_json,
        },
    )
    typer.echo(
        "[wow] done: "
        + str(
            {
                "lookup_only_students": lookup_summary["lookup_only_students"],
                "first_full_rank": lookup_summary["first_full_rank"],
                "pr_after_recommendation_sink_share_pct": pr_summary["sink_share_after_pct"],
                "ghost_finishers": archetype_summary_json["ghost_finishers"],
                "panic_patchers": archetype_summary_json["panic_patchers"],
            }
        )
    )


if __name__ == "__main__":
    app()
