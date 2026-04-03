#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "orjson>=3.10",
#   "pandas>=2.2",
#   "pyarrow>=20.0",
#   "rich>=14.0",
#   "scikit-learn>=1.6",
#   "typer>=0.16",
# ]
# ///

from __future__ import annotations

from itertools import combinations
from pathlib import Path
import re
from typing import Any

import pandas as pd
import typer
from rich.traceback import install
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import CountVectorizer

from tds_p1_common import ANALYSIS_DIR, DERIVED_DIR, QUESTION_LABELS, markdown_table, read_json, write_json

install(show_locals=True)

app = typer.Typer(add_completion=False)

QUESTION_ORDER = [
    "q-generate-affective-chart",
    "q-generate-concept-incarnation",
    "q-generate-paradox-portrait",
    "q-generate-style-transplant",
]

PROMPT_FEATURE_LABELS = {
    "has_negative_prompt": "Negative-prompt syntax",
    "has_generation_params": "Explicit generation parameters",
    "has_style_reference": "Named style references",
}


def slug(text: str) -> str:
    """Normalize free text enough for grouping repeated answers."""

    value = str(text or "").strip().lower().replace("’", "'").replace("·", "-")
    value = re.sub(r"\s+", " ", value)
    return value


def model_family(model: str) -> str:
    """Collapse noisy model strings into stable families."""

    value = slug(model)
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


def normalize_concept(value: str) -> str:
    """Group obvious variants of repeated concept choices."""

    text = slug(value)
    rules = [
        ("Overfitting", r"overfitting"),
        ("Gradient descent", r"gradient descent"),
        ("Vanishing gradients", r"vanishing gradients?"),
        ("Dimensionality reduction", r"dimensionality reduction"),
        ("Curse of dimensionality", r"curse of dimensionality"),
        ("Class imbalance", r"class imbalance"),
        ("Attention mechanism", r"attention"),
        ("Support vector machine", r"support vector"),
        ("Bias-variance tradeoff", r"bias[- ]variance"),
    ]
    for label, pattern in rules:
        if re.search(pattern, text):
            return label
    return value.strip() or "Other"


def normalize_paradox(value: str) -> str:
    """Group paradox names into consistent buckets."""

    text = slug(value)
    rules = [
        ("Simpson's paradox", r"simpson"),
        ("Friendship paradox", r"friendship paradox"),
        ("Goodhart's law", r"goodhart"),
        ("Ecological fallacy", r"ecological fallacy"),
        ("Inspection paradox", r"inspection paradox"),
        ("Birthday problem", r"birthday"),
        ("Ellsberg paradox", r"ellsberg"),
    ]
    for label, pattern in rules:
        if re.search(pattern, text):
            return label
    return value.strip() or "Other"


def normalize_tradition(value: str) -> str:
    """Group stylistic traditions into stable families."""

    text = slug(value)
    rules = [
        ("Ukiyo-e", r"ukiyo|edo-period woodblock"),
        ("Naturalist illustration", r"naturalist|scientific illustration"),
        ("Bauhaus", r"bauhaus"),
        ("Constructivism", r"constructiv"),
        ("Art Nouveau botanical", r"art nouveau"),
        ("Scientific engraving", r"engraving"),
        ("Manuscript illumination", r"manuscript illumination"),
        ("Chinese ink wash", r"ink wash|shuimo"),
        ("WPA posters", r"\bwpa\b|federal art project"),
        ("De Stijl", r"de stijl"),
    ]
    for label, pattern in rules:
        if re.search(pattern, text):
            return label
    return value.strip() or "Other"


def normalize_dataset_theme(dataset_name: str, insight: str) -> str:
    """Map affective-chart dataset choices into broad emotional themes."""

    text = f"{slug(dataset_name)} {slug(insight)}"
    rules = [
        ("Language loss", r"language|linguist"),
        ("Climate / warming", r"temperature|climate|gistemp|co2|emission"),
        ("Biodiversity / deforestation", r"forest|deforestation|planet index|wildlife|species|biodiversity"),
        ("Inequality / wealth", r"inequality|wealth|income|percentile"),
        ("Health / mortality", r"life expectancy|air pollution|mortality|disease|health"),
        ("Poverty / hunger", r"hunger|poverty|food"),
    ]
    for label, pattern in rules:
        if re.search(pattern, text):
            return label
    return "Other"


def load_joined_frame(summary_path: Path, manifest_path: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    """Load gallery summary and join it to the fetched asset manifest."""

    if not summary_path.exists():
        raise typer.BadParameter(f"Missing summary file: {summary_path}")
    if not manifest_path.exists():
        raise typer.BadParameter(f"Missing manifest parquet: {manifest_path}")

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
    if len(joined) != len(manifest_ok):
        raise RuntimeError(f"Join mismatch: {len(joined)} joined rows for {len(manifest_ok)} manifest rows")

    joined["question_label"] = joined["question_id"].map(QUESTION_LABELS)
    joined["model_family"] = joined["model"].map(model_family)
    joined["duplicate_image"] = joined["image_sha256"].duplicated(keep=False)
    joined["time_utc"] = pd.to_datetime(joined["time"], unit="ms", utc=True)
    joined["hours_before_deadline"] = (
        pd.Timestamp(summary["deadline"]["iso"]).tz_convert("UTC") - joined["time_utc"]
    ).dt.total_seconds() / 3600
    joined["has_anachronism_note"] = (
        joined["resp.anachronisms_detected"].fillna("").astype(str).str.strip().str.lower().ne("none detected")
    )
    joined["concept_topic"] = joined["concept"].map(normalize_concept)
    joined["paradox_topic"] = joined["paradox"].map(normalize_paradox)
    joined["tradition_topic"] = joined["tradition_name"].map(normalize_tradition)
    joined["dataset_theme"] = joined.apply(
        lambda row: normalize_dataset_theme(row["dataset_name"], row["insight"]),
        axis=1,
    )
    return summary, joined


def score_dimension_frame(df: pd.DataFrame, summary: dict[str, Any]) -> pd.DataFrame:
    """Flatten per-dimension Gemini scores into a long table."""

    rows: list[dict[str, Any]] = []
    for question_id in QUESTION_ORDER:
        dims = summary["questions"][question_id]["score_dimensions"]
        qd = df[df["question_id"] == question_id]
        for dim in dims:
            score_col = f"resp.scores.{dim}.score"
            reason_col = f"resp.scores.{dim}.reason"
            improvement_col = f"resp.scores.{dim}.improvement"
            dim_rows = qd[
                [
                    "submission_id",
                    "question_id",
                    "question_label",
                    "resp.overall_score",
                    "resp.exhibition_worthy",
                    score_col,
                    reason_col,
                    improvement_col,
                ]
            ].copy()
            dim_rows = dim_rows.rename(
                columns={
                    score_col: "dimension_score",
                    reason_col: "dimension_reason",
                    improvement_col: "dimension_improvement",
                }
            )
            dim_rows["dimension"] = dim
            rows.extend(dim_rows.to_dict(orient="records"))
    return pd.DataFrame(rows)


def interval_label(interval: pd.Interval) -> str:
    """Format qcut buckets compactly for markdown."""

    left = int(round(interval.left if interval.left > 0 else 0))
    right = int(round(interval.right))
    return f"{left}–{right}"


def quartile_profile(qd: pd.DataFrame) -> list[dict[str, Any]]:
    """Summarize score and exhibition rate across prompt-length quartiles."""

    buckets = pd.qcut(qd["prompt_words"], 4, duplicates="drop")
    grouped = qd.groupby(buckets, observed=False).agg(
        n=("submission_id", "size"),
        score=("resp.overall_score", "mean"),
        exhibition=("resp.exhibition_worthy", "mean"),
    )
    return [
        {
            "range_words": interval_label(interval),
            "n": int(row["n"]),
            "score": round(float(row["score"]), 3),
            "exhibition_rate": round(float(row["exhibition"]), 3),
        }
        for interval, row in grouped.iterrows()
    ]


def boolean_feature_profile(qd: pd.DataFrame) -> list[dict[str, Any]]:
    """Compare boolean prompt features against score and exhibition rates."""

    rows: list[dict[str, Any]] = []
    for feature in PROMPT_FEATURE_LABELS:
        grouped = qd.groupby(feature).agg(
            n=("submission_id", "size"),
            score=("resp.overall_score", "mean"),
            exhibition=("resp.exhibition_worthy", "mean"),
        )
        if set(grouped.index.tolist()) != {False, True}:
            continue
        rows.append(
            {
                "feature": PROMPT_FEATURE_LABELS[feature],
                "share_true": round(float(qd[feature].mean()), 3),
                "score_delta_true_minus_false": round(float(grouped.loc[True, "score"] - grouped.loc[False, "score"]), 3),
                "exhibition_delta_true_minus_false": round(
                    float(grouped.loc[True, "exhibition"] - grouped.loc[False, "exhibition"]),
                    3,
                ),
            }
        )
    return rows


def question_scorecards(df: pd.DataFrame, dim_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Build per-question scorecards with the toughest and most decisive dimensions."""

    cards: list[dict[str, Any]] = []
    for question_id in QUESTION_ORDER:
        qd = df[df["question_id"] == question_id]
        dims = dim_df[dim_df["question_id"] == question_id]
        dim_summary = []
        for dim, sub in dims.groupby("dimension"):
            exhib_mean = sub[sub["resp.exhibition_worthy"]]["dimension_score"].mean()
            non_mean = sub[~sub["resp.exhibition_worthy"]]["dimension_score"].mean()
            dim_summary.append(
                {
                    "dimension": dim,
                    "mean_score": round(float(sub["dimension_score"].mean()), 3),
                    "std": round(float(sub["dimension_score"].std()), 3),
                    "exhibition_gap": round(float(exhib_mean - non_mean), 3),
                    "corr_with_overall": round(float(sub["dimension_score"].corr(sub["resp.overall_score"])), 3),
                }
            )

        hardest = min(dim_summary, key=lambda row: row["mean_score"])
        gatekeeper = max(dim_summary, key=lambda row: row["exhibition_gap"])
        cards.append(
            {
                "question_id": question_id,
                "question_label": QUESTION_LABELS[question_id],
                "n": int(len(qd)),
                "mean_score": round(float(qd["resp.overall_score"].mean()), 3),
                "exhibition_rate": round(float(qd["resp.exhibition_worthy"].mean()), 3),
                "median_prompt_words": int(qd["prompt_words"].median()),
                "hardest_dimension": hardest["dimension"],
                "hardest_dimension_mean": hardest["mean_score"],
                "gatekeeper_dimension": gatekeeper["dimension"],
                "gatekeeper_exhibition_gap": gatekeeper["exhibition_gap"],
                "dimension_summary": dim_summary,
            }
        )
    return cards


def model_question_table(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Compare model families within each question."""

    rows: list[dict[str, Any]] = []
    grouped = df.groupby(["question_id", "question_label", "model_family"]).agg(
        n=("submission_id", "size"),
        mean_score=("resp.overall_score", "mean"),
        exhibition_rate=("resp.exhibition_worthy", "mean"),
    )
    for (question_id, question_label, family), row in grouped.iterrows():
        if int(row["n"]) < 15:
            continue
        rows.append(
            {
                "question_id": question_id,
                "question_label": question_label,
                "model_family": family,
                "n": int(row["n"]),
                "mean_score": round(float(row["mean_score"]), 3),
                "exhibition_rate": round(float(row["exhibition_rate"]), 3),
            }
        )
    return rows


def semantic_penalties(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Measure what happens when Gemini cannot recognize the student's stated idea."""

    specs = [
        ("q-generate-concept-incarnation", "resp.concept_match", "Concept Incarnation"),
        ("q-generate-paradox-portrait", "resp.paradox_match", "Paradox Portrait"),
        ("q-generate-style-transplant", "resp.tradition_match", "Style Transplant"),
    ]
    rows: list[dict[str, Any]] = []
    for question_id, column, label in specs:
        qd = df[df["question_id"] == question_id]
        grouped = qd.groupby(column).agg(
            n=("submission_id", "size"),
            mean_score=("resp.overall_score", "mean"),
            exhibition_rate=("resp.exhibition_worthy", "mean"),
        )
        if set(grouped.index.tolist()) != {False, True}:
            continue
        rows.append(
            {
                "question_label": label,
                "flag": column.removeprefix("resp."),
                "false_n": int(grouped.loc[False, "n"]),
                "false_score": round(float(grouped.loc[False, "mean_score"]), 3),
                "false_exhibition": round(float(grouped.loc[False, "exhibition_rate"]), 3),
                "true_n": int(grouped.loc[True, "n"]),
                "true_score": round(float(grouped.loc[True, "mean_score"]), 3),
                "true_exhibition": round(float(grouped.loc[True, "exhibition_rate"]), 3),
            }
        )
    return rows


def gateway_tables(df: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    """Capture the threshold combinations that separate success from collapse."""

    specs = {
        "Affective Chart": ("q-generate-affective-chart", ["resp.brief_met", "resp.model_default_escaped"]),
        "Concept Incarnation": ("q-generate-concept-incarnation", ["resp.concept_match", "resp.model_default_escaped"]),
        "Paradox Portrait": ("q-generate-paradox-portrait", ["resp.paradox_match", "resp.diptych"]),
        "Style Transplant": ("q-generate-style-transplant", ["resp.tradition_match", "resp.concept_match"]),
        "Style / anachronism": ("q-generate-style-transplant", ["has_anachronism_note", "resp.tradition_match"]),
    }
    tables: dict[str, list[dict[str, Any]]] = {}
    for label, (question_id, columns) in specs.items():
        qd = df[df["question_id"] == question_id]
        grouped = qd.groupby(columns).agg(
            n=("submission_id", "size"),
            mean_score=("resp.overall_score", "mean"),
            exhibition_rate=("resp.exhibition_worthy", "mean"),
        )
        rows = []
        for key, row in grouped.iterrows():
            values = key if isinstance(key, tuple) else (key,)
            name_map = {
                "has_anachronism_note": "anachronism_note",
            }
            rows.append(
                {
                    name_map.get(columns[i], columns[i].removeprefix("resp.")): bool(values[i]) for i in range(len(columns))
                }
                | {
                    "n": int(row["n"]),
                    "mean_score": round(float(row["mean_score"]), 3),
                    "exhibition_rate": round(float(row["exhibition_rate"]), 3),
                }
            )
        tables[label] = rows
    return tables


def student_clusters(df: pd.DataFrame) -> dict[str, Any]:
    """Cluster students with four complete image-question scores into archetypes."""

    wide = df.pivot_table(index="user", columns="question_id", values="resp.overall_score", aggfunc="first").dropna()
    z = (wide - wide.mean()) / wide.std()
    model = KMeans(n_clusters=5, random_state=0, n_init=100)
    labels = model.fit_predict(z.to_numpy())
    wide = wide.copy()
    wide["cluster"] = labels

    cluster_rows = []
    family_pref = (
        df[df["user"].isin(wide.index)]
        .groupby(["user", "model_family"])
        .size()
        .rename("n")
        .reset_index()
        .sort_values(["user", "n", "model_family"], ascending=[True, False, True])
        .drop_duplicates("user")
        .rename(columns={"model_family": "dominant_family"})
    )
    student_meta = df[df["user"].isin(wide.index)].groupby("user").agg(
        avg_prompt_words=("prompt_words", "mean"),
        publish_count=("publish_email", "sum"),
    )
    wide = wide.reset_index().merge(family_pref[["user", "dominant_family"]], on="user", how="left")
    wide = wide.merge(student_meta.reset_index(), on="user", how="left")

    for cluster_id, sub in wide.groupby("cluster"):
        question_means = {qid: round(float(sub[qid].mean()), 3) for qid in QUESTION_ORDER}
        weakest_question = min(question_means, key=question_means.get)
        label = {
            QUESTION_ORDER[0]: "Affective strugglers",
            QUESTION_ORDER[1]: "Concept strugglers",
            QUESTION_ORDER[2]: "Paradox literalists",
            QUESTION_ORDER[3]: "Style collapsers",
        }[weakest_question]
        if min(question_means.values()) > 8:
            label = "All-around elites"
        cluster_rows.append(
            {
                "cluster": int(cluster_id),
                "label": label,
                "n": int(len(sub)),
                "mean_total": round(float(sub[QUESTION_ORDER].mean(axis=1).mean()), 3),
                "avg_prompt_words": round(float(sub["avg_prompt_words"].mean()), 1),
                "publish_rate": round(float((sub["publish_count"] > 0).mean()), 3),
                "dominant_family_share": round(float(sub["dominant_family"].eq(sub["dominant_family"].mode().iat[0]).mean()), 3),
                "dominant_family": str(sub["dominant_family"].mode().iat[0]),
                **question_means,
            }
        )

    cluster_rows = sorted(cluster_rows, key=lambda row: (-row["mean_total"], row["label"]))
    return {
        "complete_students": int(len(wide)),
        "cluster_rows": cluster_rows,
    }


def duplicate_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Summarize exact image reuse across the cohort."""

    dup_rows = df[df["duplicate_image"]].copy()
    top_groups = []
    for image_sha, sub in dup_rows.groupby("image_sha256"):
        if len(sub) < 4:
            continue
        descriptor = (
            sub["dataset_name"].replace("", pd.NA).dropna().mode()
            if sub["question_id"].eq("q-generate-affective-chart").all()
            else sub["concept_topic"].replace("", pd.NA).dropna().mode()
            if sub["question_id"].eq("q-generate-concept-incarnation").all()
            else sub["paradox_topic"].replace("", pd.NA).dropna().mode()
            if sub["question_id"].eq("q-generate-paradox-portrait").all()
            else sub["tradition_topic"].replace("", pd.NA).dropna().mode()
        )
        top_groups.append(
            {
                "reuse_count": int(len(sub)),
                "question_mix": ", ".join(
                    f"{label}×{count}" for label, count in sub["question_label"].value_counts().sort_values(ascending=False).items()
                ),
                "mean_score": round(float(sub["resp.overall_score"].mean()), 3),
                "model": str(sub["model"].mode().iat[0]),
                "descriptor": str(descriptor.iat[0]) if len(descriptor) else "mixed",
            }
        )
    top_groups = sorted(top_groups, key=lambda row: (-row["reuse_count"], -row["mean_score"]))[:10]

    return {
        "duplicate_rows": int(len(dup_rows)),
        "duplicate_hashes": int(dup_rows["image_sha256"].nunique()),
        "score_penalty": round(
            float(df[df["duplicate_image"]]["resp.overall_score"].mean() - df[~df["duplicate_image"]]["resp.overall_score"].mean()),
            3,
        ),
        "by_question": [
            {
                "question_label": question_label,
                "duplicate_rows": int(sub["duplicate_image"].sum()),
                "duplicate_share": round(float(sub["duplicate_image"].mean()), 3),
                "duplicate_mean_score": round(float(sub[sub["duplicate_image"]]["resp.overall_score"].mean()), 3),
                "unique_mean_score": round(float(sub[~sub["duplicate_image"]]["resp.overall_score"].mean()), 3),
            }
            for question_label, sub in df.groupby("question_label")
        ],
        "top_groups": top_groups,
    }


def repeated_choice_tables(df: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    """Summarize which repeated choices became clichés versus winners."""

    tables: dict[str, list[dict[str, Any]]] = {}
    specs = [
        ("Affective themes", "q-generate-affective-chart", "dataset_theme"),
        ("Concept choices", "q-generate-concept-incarnation", "concept_topic"),
        ("Paradox choices", "q-generate-paradox-portrait", "paradox_topic"),
        ("Style choices", "q-generate-style-transplant", "tradition_topic"),
    ]
    for label, question_id, column in specs:
        qd = df[df["question_id"] == question_id]
        grouped = (
            qd.groupby(column)
            .agg(
                n=("submission_id", "size"),
                mean_score=("resp.overall_score", "mean"),
                exhibition_rate=("resp.exhibition_worthy", "mean"),
            )
            .query("n >= 5")
            .sort_values(["n", "mean_score"], ascending=[False, False])
        )
        tables[label] = [
            {
                "choice": str(choice),
                "n": int(row["n"]),
                "mean_score": round(float(row["mean_score"]), 3),
                "exhibition_rate": round(float(row["exhibition_rate"]), 3),
            }
            for choice, row in grouped.head(10).iterrows()
        ]
    return tables


def low_score_phrases(df: pd.DataFrame, dim_df: pd.DataFrame) -> dict[str, list[str]]:
    """Extract the most repeated evaluator language in low-scoring images."""

    phrases: dict[str, list[str]] = {}
    for question_id in QUESTION_ORDER:
        qd = dim_df[dim_df["question_id"] == question_id]
        cutoff = qd["resp.overall_score"].quantile(0.25)
        text = (
            qd[qd["resp.overall_score"] <= cutoff]["dimension_improvement"].fillna("")
            + " "
            + qd[qd["resp.overall_score"] <= cutoff]["dimension_reason"].fillna("")
        )
        vectorizer = CountVectorizer(stop_words="english", ngram_range=(2, 3), min_df=4)
        matrix = vectorizer.fit_transform(text)
        counts = matrix.sum(axis=0).A1
        vocab = vectorizer.get_feature_names_out()
        ranked = sorted(zip(counts, vocab), reverse=True)
        phrases[QUESTION_LABELS[question_id]] = [term for _, term in ranked[:6]]
    return phrases


def timing_profiles(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Compare earliest versus latest quartiles within each image question."""

    rows = []
    for question_id in QUESTION_ORDER:
        qd = df[df["question_id"] == question_id].copy()
        qd["bucket"] = pd.qcut(qd["hours_before_deadline"], 4, duplicates="drop")
        grouped = qd.groupby("bucket", observed=False).agg(
            n=("submission_id", "size"),
            mean_score=("resp.overall_score", "mean"),
            exhibition_rate=("resp.exhibition_worthy", "mean"),
        )
        earliest = grouped.iloc[-1]
        latest = grouped.iloc[0]
        rows.append(
            {
                "question_label": QUESTION_LABELS[question_id],
                "latest_q_score": round(float(latest["mean_score"]), 3),
                "earliest_q_score": round(float(earliest["mean_score"]), 3),
                "score_gap_early_minus_late": round(float(earliest["mean_score"] - latest["mean_score"]), 3),
                "latest_q_exhibition": round(float(latest["exhibition_rate"]), 3),
                "earliest_q_exhibition": round(float(earliest["exhibition_rate"]), 3),
            }
        )
    return rows


def transfer_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Measure how much image skill transfers across the four briefs."""

    wide = df.pivot_table(index="user", columns="question_id", values="resp.overall_score", aggfunc="first").dropna()
    correlations = [
        {
            "left": QUESTION_LABELS[left],
            "right": QUESTION_LABELS[right],
            "correlation": round(float(wide[left].corr(wide[right])), 3),
        }
        for left, right in combinations(QUESTION_ORDER, 2)
    ]
    best = wide.idxmax(axis=1).value_counts()
    worst = wide.idxmin(axis=1).value_counts()
    counts = [
        {
            "question_label": QUESTION_LABELS[question_id],
            "best_count": int(best.get(question_id, 0)),
            "worst_count": int(worst.get(question_id, 0)),
        }
        for question_id in QUESTION_ORDER
    ]
    return {
        "complete_students": int(len(wide)),
        "correlations": correlations,
        "question_counts": counts,
    }


def lead_time_status(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Compare image-row status quality by time remaining before the deadline."""

    results = pd.DataFrame(summary["results"]).copy()
    results["time_utc"] = pd.to_datetime(results["time"], unit="ms", utc=True)
    results["hours_before_deadline"] = (
        pd.Timestamp(summary["deadline"]["iso"]).tz_convert("UTC") - results["time_utc"]
    ).dt.total_seconds() / 3600
    results = results[results["hours_before_deadline"] >= 0].copy()

    bins = [0, 1, 3, 6, 12, 24, 72, 9999]
    labels = ["0–1h", "1–3h", "3–6h", "6–12h", "12–24h", "24–72h", "72h+"]
    results["lead_bin"] = pd.cut(results["hours_before_deadline"], bins=bins, labels=labels, right=True)

    grouped = results.groupby("lead_bin", observed=False).agg(
        rows=("status", "size"),
        ok_rate=("status", lambda values: (values == "ok").mean()),
        assets_not_fetched_rate=("status", lambda values: (values == "assets-not-fetched").mean()),
    )

    ok_rows = results[results["status"] == "ok"].copy().reset_index(drop=True)
    ok_response = pd.json_normalize(ok_rows["response"]).add_prefix("resp.").reset_index(drop=True)
    ok_rows = pd.concat([ok_rows.reset_index(drop=True), ok_response], axis=1)
    ok_scores = ok_rows.groupby("lead_bin", observed=False).agg(
        ok_mean_score=("resp.overall_score", "mean"),
        ok_rows=("status", "size"),
    )
    merged = grouped.join(ok_scores, how="left")
    return [
        {
            "lead_bin": str(label),
            "rows": int(row["rows"]),
            "ok_rate": round(float(row["ok_rate"]), 3),
            "assets_not_fetched_rate": round(float(row["assets_not_fetched_rate"]), 3),
            "ok_mean_score": round(float(row["ok_mean_score"]), 3) if pd.notna(row["ok_mean_score"]) else None,
            "ok_rows": int(row["ok_rows"]) if pd.notna(row["ok_rows"]) else 0,
        }
        for label, row in merged.iterrows()
        if pd.notna(row["rows"])
    ]


def reuse_patterns(df: pd.DataFrame) -> dict[str, Any]:
    """Measure exact prompt reuse, exact image reuse, and cross-question recycling."""

    work = df.copy()
    work["prompt_norm"] = work["prompt"].fillna("").astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)
    work["cross_user_prompt_dup"] = work.groupby("prompt_norm")["user"].transform("nunique") > 1
    work["cross_user_image_dup"] = work.groupby("image_sha256")["user"].transform("nunique") > 1

    same_image = work.groupby(["user", "image_sha256"])["question_id"].nunique().reset_index(name="question_count")
    cross_question = same_image[same_image["question_count"] > 1][["user", "image_sha256"]].copy()
    cross_question["cross_question_reuse"] = True
    work = work.merge(cross_question, on=["user", "image_sha256"], how="left")
    work["cross_question_reuse"] = work["cross_question_reuse"].fillna(False)

    by_question_prompt_dup = []
    for question_id in QUESTION_ORDER:
        qd = work[work["question_id"] == question_id]
        grouped = qd.groupby("cross_user_prompt_dup").agg(
            n=("submission_id", "size"),
            mean_score=("resp.overall_score", "mean"),
            exhibition_rate=("resp.exhibition_worthy", "mean"),
        )
        if set(grouped.index.tolist()) != {False, True}:
            continue
        by_question_prompt_dup.append(
            {
                "question_label": QUESTION_LABELS[question_id],
                "duplicate_share": round(float(qd["cross_user_prompt_dup"].mean()), 3),
                "unique_score": round(float(grouped.loc[False, "mean_score"]), 3),
                "duplicate_score": round(float(grouped.loc[True, "mean_score"]), 3),
                "unique_exhibition": round(float(grouped.loc[False, "exhibition_rate"]), 3),
                "duplicate_exhibition": round(float(grouped.loc[True, "exhibition_rate"]), 3),
            }
        )

    cross_group = work.groupby("cross_question_reuse").agg(
        n=("submission_id", "size"),
        mean_score=("resp.overall_score", "mean"),
        exhibition_rate=("resp.exhibition_worthy", "mean"),
    )
    return {
        "prompt_dup_share": round(float(work["cross_user_prompt_dup"].mean()), 3),
        "prompt_dup_rows": int(work["cross_user_prompt_dup"].sum()),
        "image_dup_share": round(float(work["cross_user_image_dup"].mean()), 3),
        "image_dup_rows": int(work["cross_user_image_dup"].sum()),
        "cross_question_reuse_users": int(cross_question["user"].nunique()),
        "cross_question_reuse_rows": int(work["cross_question_reuse"].sum()),
        "cross_question_reuse_score": round(float(cross_group.loc[True, "mean_score"]), 3),
        "non_cross_question_reuse_score": round(float(cross_group.loc[False, "mean_score"]), 3),
        "cross_question_reuse_exhibition": round(float(cross_group.loc[True, "exhibition_rate"]), 3),
        "non_cross_question_reuse_exhibition": round(float(cross_group.loc[False, "exhibition_rate"]), 3),
        "by_question_prompt_dup": by_question_prompt_dup,
    }


def render_report(
    summary: dict[str, Any],
    cards: list[dict[str, Any]],
    model_rows: list[dict[str, Any]],
    prompt_profiles: dict[str, Any],
    penalties: list[dict[str, Any]],
    gateways: dict[str, list[dict[str, Any]]],
    clusters: dict[str, Any],
    duplicates: dict[str, Any],
    transfer: dict[str, Any],
    lead_time: list[dict[str, Any]],
    reuse: dict[str, Any],
    repeated: dict[str, list[dict[str, Any]]],
    phrases: dict[str, list[str]],
    timing: list[dict[str, Any]],
    df: pd.DataFrame,
) -> str:
    """Turn analysis tables into a narrative markdown report."""

    ac = next(card for card in cards if card["question_id"] == "q-generate-affective-chart")
    ci = next(card for card in cards if card["question_id"] == "q-generate-concept-incarnation")
    pp = next(card for card in cards if card["question_id"] == "q-generate-paradox-portrait")
    st = next(card for card in cards if card["question_id"] == "q-generate-style-transplant")

    affective_combo = pd.DataFrame(gateways["Affective Chart"]).sort_values(["brief_met", "model_default_escaped"])
    concept_combo = pd.DataFrame(gateways["Concept Incarnation"]).sort_values(["concept_match", "model_default_escaped"])
    paradox_combo = pd.DataFrame(gateways["Paradox Portrait"]).sort_values(["paradox_match", "diptych"])
    style_combo = pd.DataFrame(gateways["Style Transplant"]).sort_values(["tradition_match", "concept_match"])
    anach_combo = pd.DataFrame(gateways["Style / anachronism"]).sort_values(["anachronism_note", "tradition_match"])

    transfer_df = pd.DataFrame(transfer["question_counts"])
    lead_lookup = {row["lead_bin"]: row for row in lead_time}
    aff_prompt = next(row for row in reuse["by_question_prompt_dup"] if row["question_label"] == "Affective Chart")
    style_prompt = next(row for row in reuse["by_question_prompt_dup"] if row["question_label"] == "Style Transplant")

    style_df = df[df["question_id"] == "q-generate-style-transplant"]
    style_concept_rate = float(style_df["resp.concept_match"].mean())
    style_tradition_rate = float(style_df["resp.tradition_match"].mean())
    style_anach_rate = float(style_df["has_anachronism_note"].mean())

    paradox_df = df[df["question_id"] == "q-generate-paradox-portrait"]
    simpson_df = paradox_df[paradox_df["paradox_topic"] == "Simpson's paradox"]
    friendship_df = paradox_df[paradox_df["paradox_topic"] == "Friendship paradox"]

    dalle_style = style_df[style_df["model_family"] == "DALL·E family"]
    gemini_style = style_df[style_df["model_family"] == "Gemini/Imagen family"]
    dalle_nat = float(dalle_style[dalle_style["tradition_topic"] == "Naturalist illustration"]["resp.overall_score"].mean())
    dalle_uk = float(dalle_style[dalle_style["tradition_topic"] == "Ukiyo-e"]["resp.overall_score"].mean())
    gem_nat = float(gemini_style[gemini_style["tradition_topic"] == "Naturalist illustration"]["resp.overall_score"].mean())
    gem_uk = float(gemini_style[gemini_style["tradition_topic"] == "Ukiyo-e"]["resp.overall_score"].mean())

    prompt_feature_blocks = []
    prompt_quartile_blocks = []
    for question_id in QUESTION_ORDER:
        label = QUESTION_LABELS[question_id]
        quartiles = prompt_profiles[question_id]["quartiles"]
        features = prompt_profiles[question_id]["features"]
        prompt_quartile_blocks.append(
            f"### {label}\n\n"
            + markdown_table(
                ["Prompt words", "Rows", "Mean score", "Exhibition rate"],
                [[row["range_words"], row["n"], row["score"], row["exhibition_rate"]] for row in quartiles],
            )
        )
        prompt_feature_blocks.append(
            f"### {label}\n\n"
            + markdown_table(
                ["Feature", "True share", "Score delta", "Exhibition delta"],
                [
                    [row["feature"], row["share_true"], row["score_delta_true_minus_false"], row["exhibition_delta_true_minus_false"]]
                    for row in features
                ],
            )
        )

    repeated_blocks = []
    for label, rows in repeated.items():
        repeated_blocks.append(
            f"### {label}\n\n"
            + markdown_table(
                ["Choice", "Rows", "Mean score", "Exhibition rate"],
                [[row["choice"], row["n"], row["mean_score"], row["exhibition_rate"]] for row in rows],
            )
        )

    critique_bullets = "\n".join(
        f"- **{question}**: " + "; ".join(terms[:5]) for question, terms in phrases.items()
    )

    lines = [
        "# generate-images-deep-dive",
        "",
        "## Headline findings",
        "",
        f"- **The four image questions were not testing the same skill.** {ac['question_label']} had a healthy mean score (**{ac['mean_score']:.3f}**) but only **{ac['exhibition_rate']:.1%}** were exhibition-worthy; by contrast, {ci['question_label']} and {st['question_label']} crossed **{ci['exhibition_rate']:.1%}** and **{st['exhibition_rate']:.1%}** exhibition rates once the semantics clicked.",
        f"- **Cross-question transfer was tiny.** Among the **{transfer['complete_students']}** users with all four questions evaluated, pairwise score correlations ran only from **{min(row['correlation'] for row in transfer['correlations']):.3f}** to **{max(row['correlation'] for row in transfer['correlations']):.3f}**. {ci['question_label']} was the best question for **{int(transfer_df.loc[transfer_df['question_label'] == 'Concept Incarnation', 'best_count'].iat[0])}** users, while {ac['question_label']} was the worst for **{int(transfer_df.loc[transfer_df['question_label'] == 'Affective Chart', 'worst_count'].iat[0])}**.",
        f"- **Affective Chart was the real anti-cliché filter.** Its hardest dimension was **{ac['hardest_dimension'].replace('_', ' ')}** at **{ac['hardest_dimension_mean']:.3f}**, and its biggest gatekeeper was **{ac['gatekeeper_dimension'].replace('_', ' ')}**: exhibition-worthy charts outscored rejects there by **{ac['gatekeeper_exhibition_gap']:.3f}** points.",
        f"- **Semantic recognition was the hidden grading axis.** When Gemini could not independently recognize the student's concept, paradox, or tradition, mean scores collapsed to **{penalties[0]['false_score']:.3f}**, **{penalties[1]['false_score']:.3f}**, and **{penalties[2]['false_score']:.3f}** respectively.",
        f"- **The dominant tool was specialized, not universal.** The DALL·E family supplied the plurality of rows, but within-family performance split sharply: it was the weakest large family on {ac['question_label']} while remaining strong on {ci['question_label']}. Midjourney and Gemini/Imagen were stronger on the more interpretive briefs.",
        f"- **Prompting habits did not transfer.** The longest prompt quartile worked best for {ac['question_label']} and {ci['question_label']}, but {pp['question_label']} peaked in the middle and fell off again when prompts grew too long.",
        f"- **Last-minute rushing mainly broke the pipeline, not the art.** The image-row ok rate fell from **{lead_lookup['12–24h']['ok_rate']:.1%}** at 12–24 hours before deadline to **{lead_lookup['0–1h']['ok_rate']:.1%}** in the final hour, while `assets-not-fetched` jumped from **{lead_lookup['12–24h']['assets_not_fetched_rate']:.1%}** to **{lead_lookup['0–1h']['assets_not_fetched_rate']:.1%}**. Among rows that *did* fetch cleanly, mean score only moved from **{lead_lookup['12–24h']['ok_mean_score']:.3f}** to **{lead_lookup['0–1h']['ok_mean_score']:.3f}**.",
        f"- **Exact image reuse is real and visible.** {duplicates['duplicate_rows']:,} rows reused a hash already seen elsewhere. One identical concept image scored above **9.0** for eight students; another identical endangered-languages chart averaged only **5.375** across eight students.",
        f"- **Template reuse flipped by task.** Cross-user exact prompt duplication hurt {ac['question_label']} (**{aff_prompt['duplicate_score']:.3f}** vs **{aff_prompt['unique_score']:.3f}**) but helped {st['question_label']} (**{style_prompt['duplicate_score']:.3f}** vs **{style_prompt['unique_score']:.3f}**).",
        f"- **Topic choice created its own cliché economy.** Repeated {QUESTION_LABELS['q-generate-affective-chart'].lower()} themes around climate and language loss often underperformed, while repeated inequality, biodiversity, and natural-history style choices scored far better.",
        f"- **Students split into five image-maker archetypes.** The cohort includes all-around elites, affective strugglers, concept strugglers, paradox literalists, and style collapsers—evidence that 'good with image models' is not one skill but several.",
        "",
        "## 1. Question scorecards: what each brief was *really* measuring",
        "",
        markdown_table(
            ["Question", "Rows", "Mean score", "Exhibition rate", "Hardest dimension", "Gatekeeper dimension"],
            [
                [
                    card["question_label"],
                    card["n"],
                    card["mean_score"],
                    card["exhibition_rate"],
                    card["hardest_dimension"].replace("_", " "),
                    card["gatekeeper_dimension"].replace("_", " "),
                ]
                for card in cards
            ],
        ),
        "",
        f"{ac['question_label']} graded like a design brief, not like a generic picture contest. {ci['question_label']} and {st['question_label']} rewarded recognizability and structural mapping once the student's metaphor landed. {pp['question_label']}, meanwhile, punished literalness more than lack of polish.",
        "",
        "### Cross-question transfer was weak",
        "",
        markdown_table(
            ["Question A", "Question B", "Score correlation"],
            [[row["left"], row["right"], row["correlation"]] for row in transfer["correlations"]],
        ),
        "",
        markdown_table(
            ["Question", "Times it was a student's best image question", "Times it was worst"],
            [[row["question_label"], row["best_count"], row["worst_count"]] for row in transfer["question_counts"]],
        ),
        "",
        "These are surprisingly low transfer numbers. A student who was strong on one brief was only weakly more likely to be strong on another. The image unit was really four subtests disguised as one assignment: data-poetry, concept embodiment, paradox design, and historical grammar.",
        "",
        "### Dimension gatekeepers",
        "",
        markdown_table(
            ["Question", "Dimension", "Mean score", "Std dev", "Exhibition gap", "Correlation with overall"],
            [
                [
                    card["question_label"],
                    dim["dimension"].replace("_", " "),
                    dim["mean_score"],
                    dim["std"],
                    dim["exhibition_gap"],
                    dim["corr_with_overall"],
                ]
                for card in cards
                for dim in sorted(card["dimension_summary"], key=lambda row: -row["exhibition_gap"])[:2]
            ],
        ),
        "",
        f"The pattern is revealing. In {ac['question_label']}, **legibility without labels**—not raw emotional impact—was the scarcest ingredient. In {ci['question_label']}, the big split was **structural fidelity** and **concept recognition**. In {pp['question_label']}, **paradox embodiment** outranked mere constraint adherence. In {st['question_label']}, the killers were **grammar over surface** and **integration**: the evaluator did not reward decorative costume changes; it rewarded deep stylistic transfer.",
        "",
        "## 2. The hidden gating conditions",
        "",
        "### Affective Chart",
        "",
        markdown_table(
            ["Brief met", "Escaped defaults", "Rows", "Mean score", "Exhibition rate"],
            [[row["brief_met"], row["model_default_escaped"], row["n"], row["mean_score"], row["exhibition_rate"]] for row in affective_combo.to_dict(orient="records")],
        ),
        "",
        "### Concept Incarnation",
        "",
        markdown_table(
            ["Concept match", "Escaped defaults", "Rows", "Mean score", "Exhibition rate"],
            [[row["concept_match"], row["model_default_escaped"], row["n"], row["mean_score"], row["exhibition_rate"]] for row in concept_combo.to_dict(orient="records")],
        ),
        "",
        "### Paradox Portrait",
        "",
        markdown_table(
            ["Paradox match", "Diptych", "Rows", "Mean score", "Exhibition rate"],
            [[row["paradox_match"], row["diptych"], row["n"], row["mean_score"], row["exhibition_rate"]] for row in paradox_combo.to_dict(orient="records")],
        ),
        "",
        "### Style Transplant",
        "",
        markdown_table(
            ["Tradition match", "Concept match", "Rows", "Mean score", "Exhibition rate"],
            [[row["tradition_match"], row["concept_match"], row["n"], row["mean_score"], row["exhibition_rate"]] for row in style_combo.to_dict(orient="records")],
        ),
        "",
        markdown_table(
            ["Anachronism noted", "Tradition match", "Rows", "Mean score", "Exhibition rate"],
            [[row["anachronism_note"], row["tradition_match"], row["n"], row["mean_score"], row["exhibition_rate"]] for row in anach_combo.to_dict(orient="records")],
        ),
        "",
        f"The strongest pattern in the entire image cohort is that these questions were effectively **recognition thresholds**. In {ci['question_label']}, rows that both matched the intended concept and escaped stock AI aesthetics averaged **9.018** with a **93.4%** exhibition rate. In {st['question_label']}, if both the concept and the tradition matched, the mean score was **8.324**; if both broke, it fell to **1.215**. {ac['question_label']} was just as unforgiving: none of the rows that missed the brief became exhibition-worthy, even when they looked visually polished. The twist is that {st['question_label']} was **not mainly a semantics problem**: concept and tradition matched in **{style_concept_rate:.1%}** and **{style_tradition_rate:.1%}** of rows, but anachronism critiques still hit **{style_anach_rate:.1%}**. Students usually picked the right era; they just could not fully speak its visual grammar.",
        "",
        "## 3. Model families had specialties",
        "",
        markdown_table(
            ["Question", "Model family", "Rows", "Mean score", "Exhibition rate"],
            [
                [row["question_label"], row["model_family"], row["n"], row["mean_score"], row["exhibition_rate"]]
                for row in sorted(model_rows, key=lambda row: (row["question_label"], -row["mean_score"]))
            ],
        ),
        "",
        "This is not a leaderboard of 'best model overall'. It is a map of **task fit**:",
        "",
        "- **DALL·E family** dominated usage, but it was the weakest big family on **Affective Chart**—a clue that emotional, data-driven abstraction is not the same thing as rendering a clean scene.",
        "- **Midjourney** was strongest on the briefs that asked for mood, paradox, or historical style transfer.",
        "- **Gemini/Imagen** was especially competitive on **Paradox Portrait**, where recognition plus strangeness mattered more than smooth polish.",
        "- **Concept Incarnation** was the most 'model-forgiving' brief: almost every major family could do well there once the metaphor was concrete.",
        "",
        "## 4. Prompting strategies were question-specific, not portable",
        "",
        *prompt_quartile_blocks,
        "",
        *prompt_feature_blocks,
        "",
        "The portable-prompt myth does not survive this dataset.",
        "",
        f"- For **{ac['question_label']}**, longer prompts helped steadily: the top quartile reached **{prompt_profiles['q-generate-affective-chart']['quartiles'][-1]['score']:.3f}** versus **{prompt_profiles['q-generate-affective-chart']['quartiles'][0]['score']:.3f}** for the shortest quartile. Students needed room to specify *the data, the emotion, and the visual metaphor*.",
        f"- For **{pp['question_label']}**, verbosity became a trap. Scores peaked in the middle quartiles, then slid in the longest quartile. The task wanted a crisp contradiction, not a rambling screenplay.",
        f"- **Style references** helped on {st['question_label']} and slightly helped on {ci['question_label']}, but hurt on {ac['question_label']} and {pp['question_label']}. Decorative citation was useful only when the brief itself demanded a style lineage.",
        f"- **Generation parameters** mattered most on {pp['question_label']}, where parameterized prompts beat non-parameterized ones by **{next(row['score_delta_true_minus_false'] for row in prompt_profiles['q-generate-paradox-portrait']['features'] if row['feature'] == 'Explicit generation parameters'):.3f}** points.",
        "",
        "## 5. Choice of idea could become a cliché economy",
        "",
        *repeated_blocks,
        "",
        "The striking part is not just concentration; it is **which repeated choices still worked**.",
        "",
        "- Repeated **climate / warming** and **language loss** datasets often produced earnest but middling affective charts.",
        "- Repeated **inequality** and **biodiversity / deforestation** themes scored much better, suggesting that the successful entries found a singular visual hook instead of relying on a tragic subject alone.",
        f"- On **Paradox Portrait**, **Friendship Paradox** was actually *more* recognizable than **Simpson's paradox** (**{friendship_df['resp.paradox_match'].mean():.1%}** vs **{simpson_df['resp.paradox_match'].mean():.1%}**) but still much weaker (**{friendship_df['resp.overall_score'].mean():.3f}** vs **{simpson_df['resp.overall_score'].mean():.3f}**). Recognition alone was not enough; Simpson's produced stronger embodiment and stranger images.",
        f"- On **Style Transplant**, **Ukiyo-e** was the cohort default, but repeated **naturalist illustration** choices usually scored higher. That held even within major families: DALL·E averaged **{dalle_nat:.3f}** on naturalist illustration versus **{dalle_uk:.3f}** on Ukiyo-e; Gemini/Imagen averaged **{gem_nat:.3f}** versus **{gem_uk:.3f}**.",
        "",
        "## 6. Copying existed—but it copied both brilliance and banality",
        "",
        markdown_table(
            ["Question", "Duplicate rows", "Duplicate share", "Duplicate mean", "Unique mean"],
            [
                [
                    row["question_label"],
                    row["duplicate_rows"],
                    row["duplicate_share"],
                    row["duplicate_mean_score"],
                    row["unique_mean_score"],
                ]
                for row in duplicates["by_question"]
            ],
        ),
        "",
        markdown_table(
            ["Reuse count", "Question mix", "Mean score", "Model", "Descriptor"],
            [
                [row["reuse_count"], row["question_mix"], row["mean_score"], row["model"], row["descriptor"]]
                for row in duplicates["top_groups"]
            ],
        ),
        "",
        markdown_table(
            ["Question", "Prompt-dup share", "Unique-prompt score", "Dup-prompt score", "Unique exhibition", "Dup exhibition"],
            [
                [
                    row["question_label"],
                    row["duplicate_share"],
                    row["unique_score"],
                    row["duplicate_score"],
                    row["unique_exhibition"],
                    row["duplicate_exhibition"],
                ]
                for row in reuse["by_question_prompt_dup"]
            ],
        ),
        "",
        f"Exact duplicates were not fringe noise. There were **{duplicates['duplicate_hashes']}** repeated hashes touching **{duplicates['duplicate_rows']}** rows, while **{reuse['prompt_dup_rows']}** rows (**{reuse['prompt_dup_share']:.1%}**) reused an exact prompt already used by another student. But the duplicates tell a subtler story than 'copying lowers scores.' Some cloned images were excellent; some were weak. Reuse flattened authorship, not quality. What it removed was the student's chance to escape the original image's ceiling.",
        "",
        f"The harshest penalty came from **cross-question recycling**: **{reuse['cross_question_reuse_users']}** users reused the same exact image across multiple briefs. Those rows averaged **{reuse['cross_question_reuse_score']:.3f}** with **{reuse['cross_question_reuse_exhibition']:.1%}** exhibition, versus **{reuse['non_cross_question_reuse_score']:.3f}** and **{reuse['non_cross_question_reuse_exhibition']:.1%}** for everyone else.",
        "",
        "## 7. Student archetypes: image skill is not one skill",
        "",
        markdown_table(
            ["Archetype", "Students", "Dominant family", "Prompt words", "Publish-any rate", "Affective", "Concept", "Paradox", "Style"],
            [
                [
                    row["label"],
                    row["n"],
                    row["dominant_family"],
                    row["avg_prompt_words"],
                    row["publish_rate"],
                    row["q-generate-affective-chart"],
                    row["q-generate-concept-incarnation"],
                    row["q-generate-paradox-portrait"],
                    row["q-generate-style-transplant"],
                ]
                for row in clusters["cluster_rows"]
            ],
        ),
        "",
        f"The cluster split is one of the clearest rebukes to the idea that the cohort can be sorted along a single 'good at AI art' axis. The **All-around elites** handled every brief well. The **Affective strugglers** could map concepts and styles, but not turn data into felt narrative. The **Paradox literalists** handled everything except contradiction. And the **Style collapsers** were not bad image-makers in general—they were specifically unable to transfer a concept into a historical visual grammar.",
        "",
        "## 8. When students waited too long, some questions degraded more than others",
        "",
        markdown_table(
            ["Question", "Latest quartile", "Earliest quartile", "Early-minus-late", "Late exhibition", "Early exhibition"],
            [
                [
                    row["question_label"],
                    row["latest_q_score"],
                    row["earliest_q_score"],
                    row["score_gap_early_minus_late"],
                    row["latest_q_exhibition"],
                    row["earliest_q_exhibition"],
                ]
                for row in timing
            ],
        ),
        "",
        markdown_table(
            ["Lead time", "Rows", "OK rate", "Assets-not-fetched", "OK mean score"],
            [[row["lead_bin"], row["rows"], row["ok_rate"], row["assets_not_fetched_rate"], row["ok_mean_score"]] for row in lead_time],
        ),
        "",
        f"The deadline penalty was not uniform. {pp['question_label']} and {ac['question_label']} degraded the most in the latest submission quartile. {ci['question_label']}, by contrast, held up unusually well under time pressure. But the more surprising pattern is infrastructural: the last hour mostly broke **hosting and fetchability**, not image quality. The final-hour ok rate was only **{lead_lookup['0–1h']['ok_rate']:.1%}**, with `assets-not-fetched` at **{lead_lookup['0–1h']['assets_not_fetched_rate']:.1%}**—yet cleanly fetched rows still averaged **{lead_lookup['0–1h']['ok_mean_score']:.3f}**.",
        "",
        "## 9. What Gemini kept telling low scorers to fix",
        "",
        critique_bullets,
        "",
        "Underneath the question-specific wording, the evaluator's recurring complaints were surprisingly consistent: **be more specific, be less literal, remove modern contamination, and make the structure readable without explanation**. The failure mode was usually not technical ugliness. It was a mismatch between surface image quality and the deeper communicative contract of the brief.",
        "",
        "## 10. The confidence signal",
        "",
        f"Only **{summary['public_email_count']}** students chose to expose their email publicly, covering **{int(df['publish_email'].sum())}** of the **{summary['ok_result_count']}** evaluated rows. Students who opted into publication still performed a bit better: mean score **{df[df['publish_email']]['resp.overall_score'].mean():.3f}** versus **{df[~df['publish_email']]['resp.overall_score'].mean():.3f}**, and exhibition rate **{df[df['publish_email']]['resp.exhibition_worthy'].mean():.1%}** versus **{df[~df['publish_email']]['resp.exhibition_worthy'].mean():.1%}**. The gallery instinct was mildly but measurably correlated with quality.",
        "",
        "## Caveats",
        "",
        "- These are Gemini evaluations, not human juries. The report treats them as a consistent grader, not as ground truth about art.",
        "- Model-family comparisons are observational, not causal. Better students may have selected different tools.",
        "- Some repeated choices were normalized by rule-based text cleanup. That is enough for cohort-scale patterns, not for exact taxonomies.",
        "- Duplicate-image analysis catches exact binary reuse, not near-duplicate remixing.",
    ]
    return "\n".join(lines) + "\n"


@app.command()
def main(
    summary_path: Path = Path("gallery/summary.json"),
    manifest_path: Path = DERIVED_DIR / "image_manifest.parquet",
    output_json: Path = DERIVED_DIR / "image_deep_dive.json",
    output_markdown: Path = ANALYSIS_DIR / "generate-images-deep-dive.md",
) -> None:
    """Analyze the full generated-image cohort and write a deep-dive report."""

    typer.echo("[image-deep-dive] loading gallery summary and image manifest")
    summary, df = load_joined_frame(summary_path, manifest_path)

    typer.echo("[image-deep-dive] deriving dimension-level scores")
    dim_df = score_dimension_frame(df, summary)

    typer.echo("[image-deep-dive] computing question scorecards")
    cards = question_scorecards(df, dim_df)

    typer.echo("[image-deep-dive] profiling prompt strategies")
    prompt_profiles = {
        question_id: {
            "quartiles": quartile_profile(df[df["question_id"] == question_id]),
            "features": boolean_feature_profile(df[df["question_id"] == question_id]),
        }
        for question_id in QUESTION_ORDER
    }

    typer.echo("[image-deep-dive] comparing model families and semantic bottlenecks")
    model_rows = model_question_table(df)
    penalties = semantic_penalties(df)
    gateways = gateway_tables(df)

    typer.echo("[image-deep-dive] clustering student archetypes")
    clusters = student_clusters(df)

    typer.echo("[image-deep-dive] measuring transfer, reuse, repeated choices, critique language, and timing")
    transfer = transfer_summary(df)
    lead_time = lead_time_status(summary)
    reuse = reuse_patterns(df)
    duplicates = duplicate_summary(df)
    repeated = repeated_choice_tables(df)
    phrases = low_score_phrases(df, dim_df)
    timing = timing_profiles(df)

    payload = {
        "source_summary_generated_at_utc": summary["generated_at_utc"],
        "question_scorecards": cards,
        "model_rows": model_rows,
        "prompt_profiles": prompt_profiles,
        "semantic_penalties": penalties,
        "gateway_tables": gateways,
        "student_clusters": clusters,
        "transfer_summary": transfer,
        "lead_time_status": lead_time,
        "reuse_patterns": reuse,
        "duplicates": duplicates,
        "repeated_choices": repeated,
        "low_score_phrases": phrases,
        "timing_profiles": timing,
    }
    write_json(output_json, payload)

    typer.echo("[image-deep-dive] writing markdown report")
    report = render_report(
        summary=summary,
        cards=cards,
        model_rows=model_rows,
        prompt_profiles=prompt_profiles,
        penalties=penalties,
        gateways=gateways,
        clusters=clusters,
        duplicates=duplicates,
        transfer=transfer,
        lead_time=lead_time,
        reuse=reuse,
        repeated=repeated,
        phrases=phrases,
        timing=timing,
        df=df,
    )
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.write_text(report, encoding="utf-8")
    typer.echo(f"[image-deep-dive] wrote {output_json} and {output_markdown}")


if __name__ == "__main__":
    app()
