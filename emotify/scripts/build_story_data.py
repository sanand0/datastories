#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "numpy>=1.26",
#   "pandas>=2.2",
# ]
# ///
"""Build compact JSON datasets for the GitHub Pages story."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

EMOTIONS = [
    "amazement",
    "solemnity",
    "tenderness",
    "nostalgia",
    "calmness",
    "power",
    "joy",
    "tension",
    "sadness",
]


@dataclass(frozen=True)
class Example:
    genre: str
    track_id: int
    slug: str
    note: str


EXAMPLES: list[Example] = [
    Example("rock", 156, "rock-156", "Joy, unanimous"),
    Example("electronic", 248, "electronic-248", "Power, unanimous"),
    Example("pop", 354, "pop-354", "Calmness, near-consensus"),
    Example("pop", 370, "pop-370", "Bittersweet: nostalgia + sadness"),
    Example("classical", 27, "classical-27", "Solemnity"),
    Example("classical", 39, "classical-39", "Amazement"),
    Example("rock", 161, "rock-161", "Tension"),
    Example("pop", 376, "pop-376", "Tenderness"),
    Example("rock", 158, "rock-158", "Ambiguous: high disagreement"),
    Example("electronic", 265, "electronic-265", "Ambiguous: high disagreement"),
]


def genre_offsets(ratings: pd.DataFrame) -> dict[str, int]:
    return (
        ratings.groupby("genre")["track_id"].min().astype(int).to_dict()
        if not ratings.empty
        else {}
    )


def track_local_id(genre: str, track_id: int, offsets: dict[str, int]) -> int:
    offset = offsets.get(genre, 1)
    return int(track_id - offset + 1)


def load_ratings(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"track id": "track_id", "joyful_activation": "joy"})
    df["genre"] = df["genre"].astype(str)
    df["track_id"] = df["track_id"].astype(int)
    return df


def compute_track_table(ratings: pd.DataFrame) -> pd.DataFrame:
    grouped = ratings.groupby(["genre", "track_id"], as_index=False)
    counts = grouped[EMOTIONS].sum()
    counts = counts.merge(grouped.size().rename(columns={"size": "n_raters"}), on=["genre", "track_id"])
    for emotion in EMOTIONS:
        counts[f"p_{emotion}"] = counts[emotion] / counts["n_raters"]

    k = counts[EMOTIONS].to_numpy(dtype=float)
    selections = k.sum(axis=1)
    shares = k / np.maximum(selections[:, None], 1e-12)

    entropy = -(shares * np.log(shares + 1e-12)).sum(axis=1)
    counts["entropy"] = entropy
    counts["max_p"] = (k / counts["n_raters"].to_numpy(dtype=float)[:, None]).max(axis=1)
    counts["max_share"] = shares.max(axis=1)
    counts["selections_per_rater"] = selections / counts["n_raters"].to_numpy(dtype=float)
    counts["top_emotion"] = [EMOTIONS[int(np.argmax(row))] for row in shares]

    return counts[[
        "genre",
        "track_id",
        "n_raters",
        "entropy",
        "selections_per_rater",
        "max_p",
        "max_share",
        "top_emotion",
        *[f"p_{e}" for e in EMOTIONS],
    ]]


def pack_story(
    ratings: pd.DataFrame,
    tracks: pd.DataFrame,
    overall_importance: pd.DataFrame,
    by_emotion_importance: pd.DataFrame,
    metrics: pd.DataFrame,
    audio_root: Path,
    out_dir: Path,
) -> dict:
    offsets = genre_offsets(ratings)

    emotion_counts = ratings[EMOTIONS].sum().sort_values(ascending=False)
    emotion_total = int(emotion_counts.sum())
    emotion_bias = [
        {
            "emotion": str(emotion),
            "count": int(emotion_counts[emotion]),
            "share": float(emotion_counts[emotion] / emotion_total),
        }
        for emotion in emotion_counts.index
    ]

    genre_means = []
    for genre, group in tracks.groupby("genre"):
        means = {
            "genre": str(genre),
            "n_tracks": int(len(group)),
            "mean_entropy": float(group["entropy"].mean()),
        }
        for emotion in EMOTIONS:
            means[f"mean_{emotion}"] = float(group[f"p_{emotion}"].mean())
        genre_means.append(means)

    example_rows = []
    for ex in EXAMPLES:
        local_id = track_local_id(ex.genre, ex.track_id, offsets)
        source_path = audio_root / ex.genre / f"{local_id}.opus"
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        target_rel = Path("audio") / f"{ex.slug}.opus"
        target_path = out_dir / target_rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(source_path.read_bytes())

        row = tracks[(tracks["genre"] == ex.genre) & (tracks["track_id"] == ex.track_id)].iloc[0].to_dict()
        example_rows.append(
            {
                "genre": ex.genre,
                "track_id": int(ex.track_id),
                "note": ex.note,
                "audio": str(target_rel).replace("\\", "/"),
                "n_raters": int(row["n_raters"]),
                "entropy": float(row["entropy"]),
                "selections_per_rater": float(row["selections_per_rater"]),
                "max_p": float(row["max_p"]),
                "max_share": float(row["max_share"]),
                "p": {emotion: float(row[f"p_{emotion}"]) for emotion in EMOTIONS},
            }
        )

    top_overall = overall_importance.head(20)
    overall_features = [
        {
            "feature": str(r.feature),
            "importance": float(r.importance_mean),
        }
        for r in top_overall.itertuples(index=False)
    ]

    per_emotion = {}
    for emotion in EMOTIONS:
        subset = by_emotion_importance[by_emotion_importance["emotion"] == emotion].head(12)
        per_emotion[emotion] = [
            {"feature": str(r.feature), "importance": float(r.importance_mean)}
            for r in subset.itertuples(index=False)
        ]

    def extract_macro(split: str) -> dict[str, dict[str, float]]:
        df = metrics[(metrics["split"] == split) & (metrics["emotion"] == "macro")].copy()
        if df.empty:
            return {}
        pivot = df.pivot_table(index="model", columns="metric", values="value", aggfunc="first")
        output: dict[str, dict[str, float]] = {}
        for model, row in pivot.iterrows():
            output[str(model)] = {k: float(v) for k, v in row.dropna().to_dict().items()}
        return output

    def extract_logo() -> dict[str, dict[str, float]]:
        df = metrics[(metrics["split"] == "leave_one_genre_out") & (metrics["emotion"] == "macro")].copy()
        if df.empty:
            return {}
        grouped = df.groupby(["model", "metric"])["value"].mean().unstack("metric")
        output: dict[str, dict[str, float]] = {}
        for model, row in grouped.iterrows():
            output[str(model)] = {k: float(v) for k, v in row.dropna().to_dict().items()}
        return output

    track_rows = []
    for row in tracks.itertuples(index=False):
        track_rows.append(
            {
                "genre": str(row.genre),
                "track_id": int(row.track_id),
                "n_raters": int(row.n_raters),
                "entropy": float(row.entropy),
                "selections_per_rater": float(row.selections_per_rater),
                "max_p": float(row.max_p),
                "max_share": float(row.max_share),
                "top_emotion": str(row.top_emotion),
                "p": {emotion: float(getattr(row, f"p_{emotion}")) for emotion in EMOTIONS},
            }
        )

    return {
        "emotions": EMOTIONS,
        "emotion_bias": emotion_bias,
        "tracks": track_rows,
        "genre_means": genre_means,
        "feature_importance_overall": overall_features,
        "feature_importance_by_emotion": per_emotion,
        "examples": example_rows,
        "model_metrics": {
            "stratified": extract_macro("stratified"),
            "logo_mean": extract_logo(),
        },
        "notes": {
            "n_tracks": int(len(tracks)),
            "n_ratings": int(len(ratings)),
        },
    }


def main(
    ratings_csv: Path = Path("data.csv"),
    importance_overall: Path = Path("artifacts/feature_importance_overall.csv"),
    importance_by_emotion: Path = Path("artifacts/feature_importance_by_emotion.csv"),
    metrics_csv: Path = Path("artifacts/metrics.csv"),
    audio_root: Path = Path("."),
    out_dir: Path = Path("data"),
) -> None:
    ratings = load_ratings(ratings_csv)
    tracks = compute_track_table(ratings)

    overall = pd.read_csv(importance_overall)
    by_emotion = pd.read_csv(importance_by_emotion)
    metrics = pd.read_csv(metrics_csv)

    story = pack_story(ratings, tracks, overall, by_emotion, metrics, audio_root, out_dir)
    (out_dir / "story.json").write_text(json.dumps(story, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
