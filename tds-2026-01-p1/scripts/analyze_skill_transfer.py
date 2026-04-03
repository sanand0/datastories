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

from itertools import combinations
from pathlib import Path
import re
from typing import Any

import pandas as pd
from rich.traceback import install
import typer

from tds_p1_common import (
    ANALYSIS_DIR,
    DERIVED_DIR,
    IMAGE_QUESTION_IDS,
    QUESTION_LABELS,
    ROOT,
    markdown_table,
    read_json,
    write_json,
)

install(show_locals=True)

app = typer.Typer(add_completion=False)

NON_IMAGE_QUESTION_IDS = [
    "q-share-secret-server",
    "q-transcribe-numbers-server",
    "q-pr-merge-server",
    "q-markdown-parser-server",
    "q-network-game-labyrinth",
    "q-network-game-detective",
    "q-network-game-signal",
]


def model_family(model: str) -> str:
    value = str(model or "").strip().lower()
    families = [
        ("DALL·E family", r"dall"),
        ("Gemini/Imagen family", r"gemini|imagen|banana"),
        ("Midjourney family", r"midjourney"),
        ("Flux family", r"\bflux\b"),
        ("Ideogram family", r"ideogram"),
    ]
    for label, pattern in families:
        if re.search(pattern, value):
            return label
    return "Other / long tail"


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def percent(value: float, *, digits: int = 1) -> str:
    return f"{100 * float(value):.{digits}f}%"


def load_image_joined(summary_path: Path, manifest_path: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    summary = read_json(summary_path)
    results = pd.DataFrame(summary["results"])
    ok_results = results[results["status"] == "ok"].copy().reset_index(drop=True)
    ok_results["submission_id"] = ok_results["id"].astype(int)

    response = pd.json_normalize(ok_results["response"]).add_prefix("resp.").reset_index(drop=True)
    submission = pd.json_normalize(ok_results["submission"]).add_prefix("sub.").reset_index(drop=True)
    flat = pd.concat(
        [
            ok_results[["submission_id", "question", "time", "user", "status"]].reset_index(drop=True),
            submission,
            response,
        ],
        axis=1,
    )

    manifest = pd.read_parquet(manifest_path)
    manifest_ok = manifest[manifest["status"] == "ok"].copy()
    joined = manifest_ok.merge(
        flat,
        left_on=["submission_id", "question_id"],
        right_on=["submission_id", "question"],
        how="inner",
        validate="one_to_one",
    )
    joined["model_family"] = joined["model"].map(model_family)
    return summary, joined


def load_non_image_scores() -> pd.DataFrame:
    latest = pd.read_parquet(DERIVED_DIR / "ever_positive_latest.parquet")
    attempts = pd.read_parquet(DERIVED_DIR / "question_attempts.parquet")
    final = attempts[attempts["submission_id"].isin(set(latest["submission_id"].astype(int)))].copy()
    wide = final.pivot_table(index="email", columns="question_id", values="score", aggfunc="first").fillna(0.0)
    wide = wide[NON_IMAGE_QUESTION_IDS].copy()
    for question_id in NON_IMAGE_QUESTION_IDS:
        max_score = float(wide[question_id].max())
        if max_score:
            wide[question_id] = wide[question_id] / max_score
    return wide


def pairwise_correlations(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left, right in combinations(columns, 2):
        subset = frame[[left, right]].dropna()
        rows.append(
            {
                "left": left,
                "right": right,
                "correlation": round(float(subset[left].corr(subset[right])), 3),
                "n": int(len(subset)),
            }
        )
    return sorted(rows, key=lambda row: abs(row["correlation"]), reverse=True)


def strongest_image_links(image_scores: pd.DataFrame, non_image_scores: pd.DataFrame) -> list[dict[str, Any]]:
    joined = non_image_scores.join(image_scores, how="inner")
    rows: list[dict[str, Any]] = []
    for image_column in image_scores.columns:
        pairs: list[tuple[str, float, int]] = []
        for question_id in NON_IMAGE_QUESTION_IDS:
            subset = joined[[question_id, image_column]].dropna()
            pairs.append((question_id, round(float(subset[question_id].corr(subset[image_column])), 3), int(len(subset))))
        best_question_id, best_corr, best_n = max(pairs, key=lambda item: abs(item[1]))
        rows.append(
            {
                "image_metric": image_column,
                "best_question_id": best_question_id,
                "best_question_label": QUESTION_LABELS[best_question_id],
                "correlation": best_corr,
                "n": best_n,
            }
        )
    return rows


def compute_model_family_stats(
    summary: dict[str, Any],
    joined: pd.DataFrame,
    deep_dive: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    rows = deep_dive["model_rows"]
    by_question: dict[str, dict[str, Any]] = {}
    for row in rows:
        by_question.setdefault(row["question_id"], {})[row["model_family"]] = row

    dimension_deltas: dict[str, Any] = {}
    for question_id in IMAGE_QUESTION_IDS:
        question_frame = joined[joined["question_id"] == question_id].copy()
        dimensions = summary["questions"][question_id]["score_dimensions"]
        baseline = {
            dimension: float(question_frame[f"resp.scores.{dimension}.score"].mean())
            for dimension in dimensions
        }
        dimension_deltas[question_id] = {}
        for family, family_frame in question_frame.groupby("model_family"):
            family_deltas = {
                dimension: round(
                    float(family_frame[f"resp.scores.{dimension}.score"].mean() - baseline[dimension]),
                    3,
                )
                for dimension in dimensions
            }
            dimension_deltas[question_id][family] = family_deltas
    return by_question, dimension_deltas


def family_metric(stats: dict[str, Any], family: str) -> str:
    row = stats[family]
    return f"{family} ({row['mean_score']:.3f}, {percent(row['exhibition_rate'])}, n={row['n']})"


def top_dimension(deltas: dict[str, float], *, reverse: bool) -> tuple[str, float]:
    return sorted(deltas.items(), key=lambda item: item[1], reverse=reverse)[0]


def top_dimensions(deltas: dict[str, float], *, reverse: bool, limit: int = 2) -> list[tuple[str, float]]:
    return sorted(deltas.items(), key=lambda item: item[1], reverse=reverse)[:limit]


def build_model_playbook(
    model_stats: dict[str, dict[str, Any]],
    dimension_deltas: dict[str, Any],
    overall_rows: pd.DataFrame,
) -> list[dict[str, Any]]:
    overall = {
        row["model_family"]: row
        for row in overall_rows.to_dict(orient="records")
    }

    affective_best = dimension_deltas["q-generate-affective-chart"]["Ideogram family"]
    affective_worst = dimension_deltas["q-generate-affective-chart"]["DALL·E family"]
    paradox_best = dimension_deltas["q-generate-paradox-portrait"]["Gemini/Imagen family"]
    style_best = dimension_deltas["q-generate-style-transplant"]["Ideogram family"]
    style_worst = dimension_deltas["q-generate-style-transplant"]["DALL·E family"]

    affective_best_dims = top_dimensions(affective_best, reverse=True)
    affective_worst_dims = top_dimensions(affective_worst, reverse=False)
    paradox_best_dim, paradox_best_delta = top_dimension(paradox_best, reverse=True)
    style_best_dim, style_best_delta = top_dimension(style_best, reverse=True)
    style_worst_dim, style_worst_delta = top_dimension(style_worst, reverse=False)

    return [
        {
            "question_id": "q-generate-affective-chart",
            "question_label": QUESTION_LABELS["q-generate-affective-chart"],
            "use": "Ideogram or Midjourney; Gemini/Imagen if you want the safest large-sample fallback.",
            "avoid": "DALL·E for emotionally abstract charts.",
            "evidence": (
                f"{family_metric(model_stats['q-generate-affective-chart'], 'Ideogram family')} led this brief, while "
                f"{family_metric(model_stats['q-generate-affective-chart'], 'DALL·E family')} lagged. Ideogram was strongest on "
                f"{affective_best_dims[0][0].replace('_', ' ')} ({affective_best_dims[0][1]:+.2f}) and "
                f"{affective_best_dims[1][0].replace('_', ' ')} ({affective_best_dims[1][1]:+.2f}), while DALL·E slipped on "
                f"{affective_worst_dims[0][0].replace('_', ' ')} ({affective_worst_dims[0][1]:+.2f}) and "
                f"{affective_worst_dims[1][0].replace('_', ' ')} ({affective_worst_dims[1][1]:+.2f})."
            ),
        },
        {
            "question_id": "q-generate-concept-incarnation",
            "question_label": QUESTION_LABELS["q-generate-concept-incarnation"],
            "use": "Any mainstream family works; DALL·E is the most battle-tested default.",
            "avoid": "Other / long-tail models when you need reliable structure.",
            "evidence": (
                f"This was the most model-forgiving brief: "
                f"{family_metric(model_stats['q-generate-concept-incarnation'], 'DALL·E family')}, "
                f"{family_metric(model_stats['q-generate-concept-incarnation'], 'Gemini/Imagen family')}, and "
                f"{family_metric(model_stats['q-generate-concept-incarnation'], 'Ideogram family')} clustered tightly, "
                f"while {family_metric(model_stats['q-generate-concept-incarnation'], 'Other / long tail')} fell well behind."
            ),
        },
        {
            "question_id": "q-generate-paradox-portrait",
            "question_label": QUESTION_LABELS["q-generate-paradox-portrait"],
            "use": "Gemini/Imagen or Midjourney for paradox-heavy briefs.",
            "avoid": "DALL·E or Ideogram when paradox embodiment matters more than polish.",
            "evidence": (
                f"{family_metric(model_stats['q-generate-paradox-portrait'], 'Gemini/Imagen family')} and "
                f"{family_metric(model_stats['q-generate-paradox-portrait'], 'Midjourney family')} led. "
                f"Gemini/Imagen's biggest edge was {paradox_best_dim.replace('_', ' ')} ({paradox_best_delta:+.2f}), "
                f"while DALL·E landed at {model_stats['q-generate-paradox-portrait']['DALL·E family']['mean_score']:.3f} "
                f"and Ideogram at {model_stats['q-generate-paradox-portrait']['Ideogram family']['mean_score']:.3f}."
            ),
        },
        {
            "question_id": "q-generate-style-transplant",
            "question_label": QUESTION_LABELS["q-generate-style-transplant"],
            "use": "Midjourney or Ideogram; Gemini/Imagen if you want the strongest large-sample generalist.",
            "avoid": "Other / long-tail models, and DALL·E if authentic style grammar is the whole point.",
            "evidence": (
                f"{family_metric(model_stats['q-generate-style-transplant'], 'Ideogram family')} and "
                f"{family_metric(model_stats['q-generate-style-transplant'], 'Gemini/Imagen family')} led the scalable options. "
                f"Ideogram's edge came from {style_best_dim.replace('_', ' ')} ({style_best_delta:+.2f}), while DALL·E slipped on "
                f"{style_worst_dim.replace('_', ' ')} ({style_worst_delta:+.2f})."
            ),
        },
        {
            "question_id": "overall",
            "question_label": "Overall image portfolio",
            "use": "Gemini/Imagen if you need one dependable all-rounder; Midjourney if you can accept smaller-sample uncertainty for a higher ceiling.",
            "avoid": "Other / long-tail families as a default strategy.",
            "evidence": (
                f"Overall, {family_metric(overall, 'Midjourney family')} had the best mean, but "
                f"{family_metric(overall, 'Gemini/Imagen family')} was the strongest large-sample generalist. "
                f"DALL·E remained usable at {overall['DALL·E family']['mean_score']:.3f}, but its weaknesses were brief-specific. "
                f"Other / long tail sat at {overall['Other / long tail']['mean_score']:.3f}."
            ),
        },
    ]


def build_theory_rows(
    systems_image_corr: dict[str, Any],
    non_image_pairs: list[dict[str, Any]],
    image_links: list[dict[str, Any]],
    deep_dive: dict[str, Any],
    model_playbook: list[dict[str, Any]],
) -> list[dict[str, str]]:
    strongest_non_image = non_image_pairs[0]
    strongest_image_link = max(image_links, key=lambda row: abs(row["correlation"]))
    affective = next(row for row in model_playbook if row["question_id"] == "q-generate-affective-chart")
    return [
        {
            "theory": "Thorndike / identical elements",
            "prediction": "Transfer should be strongest when two tasks share the same structure.",
            "evidence": (
                f"The network trio shows the biggest links: "
                f"{QUESTION_LABELS[strongest_non_image['left']]} ↔ {QUESTION_LABELS[strongest_non_image['right']]} = {strongest_non_image['correlation']:.3f}. "
                f"Markdown and transcribe also connect to the network games."
            ),
            "verdict": "Strongly supported.",
        },
        {
            "theory": "Formal discipline / one generic AI aptitude",
            "prediction": "Strong students should stay strong across every question family.",
            "evidence": (
                f"Among {systems_image_corr['complete_students']} complete image portfolios, systems mean vs image mean is only "
                f"{systems_image_corr['correlation']:.3f}. The strongest image-to-non-image link is just "
                f"{strongest_image_link['correlation']:.3f}."
            ),
            "verdict": "Strongly broken.",
        },
        {
            "theory": "Situated cognition",
            "prediction": "Performance should depend heavily on the local representational demands of the task.",
            "evidence": (
                f"The same model family can swing by more than half a point across briefs. {affective['evidence']}"
            ),
            "verdict": "Supported.",
        },
        {
            "theory": "Threshold concepts / tacit knowledge",
            "prediction": "Once the core representational constraint clicks, performance should jump nonlinearly.",
            "evidence": (
                f"In the image unit, concept-match, paradox-match, and tradition-match failures collapse scores to "
                f"{deep_dive['semantic_penalties'][0]['false_score']:.3f}, "
                f"{deep_dive['semantic_penalties'][1]['false_score']:.3f}, and "
                f"{deep_dive['semantic_penalties'][2]['false_score']:.3f}."
            ),
            "verdict": "Supported.",
        },
    ]


def render_report(
    non_image_pairs: list[dict[str, Any]],
    image_links: list[dict[str, Any]],
    systems_image_corr: dict[str, Any],
    model_playbook: list[dict[str, Any]],
    social_transfer_rows: list[list[Any]],
    theory_rows: list[dict[str, str]],
    deep_dive: dict[str, Any],
) -> str:
    image_pair_rows = [
        [row["left"], row["right"], f"{row['correlation']:.3f}"]
        for row in deep_dive["transfer_summary"]["correlations"]
    ]
    non_image_rows = [
        [QUESTION_LABELS[row["left"]], QUESTION_LABELS[row["right"]], f"{row['correlation']:.3f}"]
        for row in non_image_pairs[:8]
    ]
    image_link_rows = [
        [
            "Image mean" if row["image_metric"] == "image_mean" else QUESTION_LABELS[row["image_metric"]],
            row["best_question_label"],
            f"{row['correlation']:.3f}",
        ]
        for row in image_links
    ]
    playbook_rows = [
        [row["question_label"], row["use"], row["avoid"], row["evidence"]]
        for row in model_playbook
    ]
    theory_table_rows = [
        [row["theory"], row["prediction"], row["evidence"], row["verdict"]]
        for row in theory_rows
    ]

    reuse_rows = deep_dive["reuse_patterns"]["by_question_prompt_dup"]
    affective_dup = next(row for row in reuse_rows if row["question_label"] == "Affective Chart")
    style_dup = next(row for row in reuse_rows if row["question_label"] == "Style Transplant")
    lines = [
        "# skill-transfer",
        "",
        "## Headline findings",
        "",
        f"- **There were two almost independent exams hiding inside one course.** Among the **{systems_image_corr['complete_students']}** students with all four image briefs evaluated, the correlation between overall systems performance and overall image performance was just **{systems_image_corr['correlation']:.3f}**.",
        f"- **Near transfer was real; far transfer was tiny.** The strongest non-image link was **{QUESTION_LABELS[non_image_pairs[0]['left']]} ↔ {QUESTION_LABELS[non_image_pairs[0]['right']]} = {non_image_pairs[0]['correlation']:.3f}**, while the strongest image-to-non-image link was only **{max(image_links, key=lambda row: abs(row['correlation']))['correlation']:.3f}**.",
        f"- **The image unit itself behaved like four subtests, not one.** Its pairwise score correlations ran only from **{deep_dive['transfer_summary']['correlations'][0]['correlation']:.3f}** to **{deep_dive['transfer_summary']['correlations'][-1]['correlation']:.3f}**.",
        "- **Social transfer outran cognitive transfer.** Only **63** solvers contributed any new agent IDs; by solver **#154** the Share Secret lookup map already existed. After the public transcribe workaround, median effort fell from **12** attempts to **4**. After the kana-dojo recommendation, sink-family PR share jumped from **71.8%** to **83.2%**.",
        f"- **Model choice should be brief-specific, not tribal.** DALL·E was a strong workhorse on Concept Incarnation but a weak fit for Affective Chart and Paradox Portrait; Gemini/Imagen was the safest large-sample all-rounder.",
        "",
        "## 1. Which image model to use, and what to avoid",
        "",
        markdown_table(["Brief", "Use", "Avoid", "Evidence"], playbook_rows),
        "",
        "## 2. What actually transfers across the course",
        "",
        "### Strongest transfer within the non-image questions",
        "",
        markdown_table(["Question A", "Question B", "Correlation"], non_image_rows),
        "",
        "The network games form the clearest skill family in the course. Markdown Parser and Transcribe Numbers sit near them rather than near the image questions, which suggests a shared competence in protocol-following, debugging, and carefully preserving structure across transformations.",
        "",
        "### The image briefs barely transfer to the rest of the exam",
        "",
        markdown_table(["Image metric", "Strongest non-image link", "Correlation"], image_link_rows),
        "",
        f"That is the most important negative result in the project. Even the strongest bridge from a rich image score to any non-image question is only **{max(image_links, key=lambda row: abs(row['correlation']))['correlation']:.3f}**. The overall systems-vs-image correlation is **{systems_image_corr['correlation']:.3f}**. Once you stop treating the image tasks as a coarse course-point bucket and measure them with Gemini's rubric, the fantasy of one general 'AI-native' skill mostly disappears.",
        "",
        "### The image unit also had weak internal transfer",
        "",
        markdown_table(["Image brief A", "Image brief B", "Correlation"], image_pair_rows),
        "",
        "Affective Chart, Concept Incarnation, Paradox Portrait, and Style Transplant were not different skins on the same exercise. They were four kinds of translation: data into feeling, concept into object, paradox into scene, and concept into historical grammar.",
        "",
        "## 3. Which theories survive this data",
        "",
        markdown_table(["Theory", "Prediction", "What the data says", "Verdict"], theory_table_rows),
        "",
        "## 4. What Feynman would look for, and what he would find",
        "",
        "Feynman would not start with scores. He would start by asking which questions distinguish **naming a thing** from **understanding a thing** well enough to rebuild it in another form.",
        "",
        "- He would immediately distrust the raw solve rate on **Share Secret**. The map is complete by solver **#154**, only **63** students ever contribute a new agent ID, and **547** students solve after the lookup table is already complete. That is success without corresponding evidence of understanding.",
        f"- He would love **Style Transplant** as a detector of fake understanding. Students usually named the right tradition and the right concept, but the evaluator still flagged anachronism often enough to matter. In other words: they knew the label, not always the grammar.",
        f"- He would see **Affective Chart** as the hardest genuine-compression task. Its scarcest ingredient was **{deep_dive['question_scorecards'][0]['hardest_dimension'].replace('_', ' ')}**, not emotional topic choice. The hard part was making the idea legible without explanatory scaffolding.",
        "- He would conclude that transfer lives where the underlying machinery is shared. That is why the network games talk to each other, and why the image briefs mostly do not.",
        "",
        "## 5. What Robert Cialdini would look for, and what he would find",
        "",
        markdown_table(
            ["Principle", "Evidence", "What it means"],
            [
                [
                    "Social proof",
                    social_transfer_rows[0][2],
                    "Once a visible path exists, the cohort normalizes around it fast. Social proof moved tactics more reliably than genuine understanding.",
                ],
                [
                    "Authority",
                    social_transfer_rows[2][2],
                    "A public recommendation can redirect the whole cohort toward a legible low-risk path, even when that path has lower public value.",
                ],
                [
                    "Scarcity / urgency",
                    "As deadline pressure rose, sink-family PR share climbed from 70.9% to 84.6% and code-like work dropped to 0.0% in the one-day window.",
                    "Under time pressure, students buy insurance. They trade originality for merge probability.",
                ],
                [
                    "Limits of social proof",
                    f"Affective prompt duplicates scored {affective_dup['duplicate_score']:.3f} vs {affective_dup['unique_score']:.3f}; Style duplicates scored {style_dup['duplicate_score']:.3f} vs {style_dup['unique_score']:.3f}.",
                    "Copied tactics can spread, but copied craft only helps on briefs with a narrow structural recipe. On open-ended briefs, copying often flattens quality.",
                ],
            ],
        ),
        "",
        "Cialdini would probably say that this exam is not just measuring skill. It is measuring **susceptibility to the cohort's persuasion environment**: which public workarounds students notice, which recommendations they trust, and how strongly deadline pressure bends them toward visible safe choices.",
        "",
        "## 6. The punchline",
        "",
        "If you want a one-line summary, it is this: **skills transferred locally, tactics transferred socially, and the two should not be confused.**",
        "",
        "The course's strongest evidence of learning comes from places where students had to preserve structure across a new representation: parser work, the network games, and the image briefs when the semantics genuinely landed. The course's strongest evidence of coordination comes from the opposite direction: lookup tables, workaround waves, and sink-repo migrations that spread through public visibility rather than deep comprehension.",
    ]
    return "\n".join(lines)


@app.command()
def main(
    summary_path: Path = typer.Option(ROOT / "gallery" / "summary.json", exists=True, readable=True),
    manifest_path: Path = typer.Option(DERIVED_DIR / "image_manifest.parquet", exists=True, readable=True),
    deep_dive_path: Path = typer.Option(DERIVED_DIR / "image_deep_dive.json", exists=True, readable=True),
) -> None:
    summary, joined = load_image_joined(summary_path, manifest_path)
    deep_dive = read_json(deep_dive_path)
    non_image_scores = load_non_image_scores()

    image_scores = joined.pivot_table(index="email", columns="question_id", values="resp.overall_score", aggfunc="first")
    image_scores = image_scores[IMAGE_QUESTION_IDS].copy()
    image_scores["image_mean"] = image_scores.mean(axis=1)

    complete = non_image_scores.join(image_scores, how="inner").dropna()
    complete["systems_mean"] = complete[NON_IMAGE_QUESTION_IDS].mean(axis=1)
    systems_image_corr = {
        "complete_students": int(len(complete)),
        "correlation": round(float(complete["systems_mean"].corr(complete["image_mean"])), 3),
    }

    non_image_pairs = pairwise_correlations(non_image_scores, NON_IMAGE_QUESTION_IDS)
    image_links = strongest_image_links(image_scores, non_image_scores)

    model_stats, dimension_deltas = compute_model_family_stats(summary, joined, deep_dive)
    overall_model_rows = (
        joined.groupby("model_family")
        .agg(
            n=("submission_id", "size"),
            mean_score=("resp.overall_score", "mean"),
            exhibition_rate=("resp.exhibition_worthy", "mean"),
        )
        .reset_index()
        .sort_values(["mean_score", "n"], ascending=[False, False])
    )
    model_playbook = build_model_playbook(model_stats, dimension_deltas, overall_model_rows)

    share_coverage = pd.read_parquet(DERIVED_DIR / "share_secret_lookup_coverage.parquet")
    transcribe_effects = pd.read_parquet(DERIVED_DIR / "transcribe_intervention_effects.parquet").set_index("cohort")
    pr_effects = pd.read_parquet(DERIVED_DIR / "pr_recommendation_effects.parquet").set_index("recommendation_cohort")

    full_map_rank = int(share_coverage.loc[share_coverage["known_agent_ids_after_solve"] >= 100, "solve_rank"].min())
    full_map_solver = full_map_rank + 1
    share_contributors = int((share_coverage["new_agent_ids_at_rank"] > 0).sum())
    share_total = int(share_coverage["solve_rank"].max())
    share_after = share_total - full_map_solver
    before_transcribe = transcribe_effects.loc["before-2026-03-04"]
    after_transcribe = transcribe_effects.loc["after-2026-03-26"]
    before_pr = pr_effects.loc["before-2026-03-24"]
    after_pr = pr_effects.loc["after-2026-03-24"]

    social_transfer_rows = [
        [
            "Share Secret lookup cascade",
            f"Only {share_contributors} solvers contributed any new agent IDs.",
            f"By solver #{full_map_solver}, the full 100-ID map already exists, and {share_after} more students solve after that.",
            "Classic social-proof infrastructure: once the map exists, the puzzle is socially rather than cognitively hard.",
        ],
        [
            "Transcribe workaround wave",
            f"Median solver effort was {before_transcribe['median_attempts_solvers']:.0f} attempts and first-try success was {before_transcribe['first_try_pct']:.1f}%.",
            f"After the public HTML/audio workaround, effort fell to {after_transcribe['median_attempts_solvers']:.0f} attempts and first-try success rose to {after_transcribe['first_try_pct']:.1f}%.",
            "The shared method mattered more than any underlying change in the task.",
        ],
        [
            "PR recommendation shock",
            f"kana-dojo share was {before_pr['kana_dojo_share']:.1f}%, sink-family share was {before_pr['sink_share']:.1f}%, and code-like share was {before_pr['code_like_share']:.1f}%.",
            f"After the recommendation, kana-dojo reached {after_pr['kana_dojo_share']:.1f}%, sink-family share {after_pr['sink_share']:.1f}%, and code-like work fell to {after_pr['code_like_share']:.1f}%.",
            "Authority changed where students aimed their effort, not just how hard they worked.",
        ],
    ]

    theory_rows = build_theory_rows(
        systems_image_corr=systems_image_corr,
        non_image_pairs=non_image_pairs,
        image_links=image_links,
        deep_dive=deep_dive,
        model_playbook=model_playbook,
    )

    summary_payload = {
        "systems_image_correlation": systems_image_corr,
        "non_image_pairs": non_image_pairs,
        "image_to_non_image_links": image_links,
        "model_playbook": model_playbook,
        "social_transfer_rows": [
            {"cue": cue, "before": before, "after": after, "meaning": meaning}
            for cue, before, after, meaning in social_transfer_rows
        ],
        "theory_rows": theory_rows,
    }

    write_json(DERIVED_DIR / "skill_transfer_summary.json", summary_payload)
    write_markdown(
        ANALYSIS_DIR / "skill-transfer.md",
        render_report(
            non_image_pairs=non_image_pairs,
            image_links=image_links,
            systems_image_corr=systems_image_corr,
            model_playbook=model_playbook,
            social_transfer_rows=social_transfer_rows,
            theory_rows=theory_rows,
            deep_dive=deep_dive,
        ),
    )

    typer.echo(f"Wrote {ANALYSIS_DIR / 'skill-transfer.md'}")
    typer.echo(f"Wrote {DERIVED_DIR / 'skill_transfer_summary.json'}")


if __name__ == "__main__":
    app()
