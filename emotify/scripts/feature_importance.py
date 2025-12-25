#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "numpy>=1.26",
#   "pandas>=2.2",
#   "scikit-learn>=1.4",
#   "typer>=0.12",
# ]
# ///
"""Analyze feature importance using permutation importance."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import typer
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedShuffleSplit

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


def load_dataset(features_path: Path, targets_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = pd.read_csv(features_path)
    targets = pd.read_csv(targets_path)
    merged = features.merge(targets, on=["genre", "track_id"], how="inner")
    if merged.empty:
        raise ValueError("No rows after merging features and targets.")
    x = merged.drop(columns=["genre", "track_id", "path"] + [f"p_{e}" for e in EMOTIONS])
    y = merged[[f"p_{e}" for e in EMOTIONS]]
    return x, y.join(merged["genre"])


def stratified_split(genres: pd.Series, test_size: float = 0.2) -> tuple[np.ndarray, np.ndarray]:
    splitter = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=42)
    train_idx, test_idx = next(splitter.split(np.zeros(len(genres)), genres))
    return train_idx, test_idx


def compute_overall_importance(
    x_train: pd.DataFrame,
    y_train: pd.DataFrame,
    x_test: pd.DataFrame,
    y_test: pd.DataFrame,
) -> pd.DataFrame:
    model = RandomForestRegressor(
        n_estimators=400,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train, y_train)

    result = permutation_importance(
        model,
        x_test,
        y_test,
        n_repeats=10,
        random_state=42,
        scoring="neg_mean_absolute_error",
    )

    return pd.DataFrame(
        {
            "feature": x_train.columns,
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)


def compute_emotion_importance(
    x_train: pd.DataFrame,
    y_train: pd.DataFrame,
    x_test: pd.DataFrame,
    y_test: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for emotion in EMOTIONS:
        model = RandomForestRegressor(
            n_estimators=400,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(x_train, y_train[emotion])
        result = permutation_importance(
            model,
            x_test,
            y_test[emotion],
            n_repeats=10,
            random_state=42,
            scoring="neg_mean_absolute_error",
        )
        for feature, mean, std in zip(
            x_train.columns,
            result.importances_mean,
            result.importances_std,
            strict=True,
        ):
            rows.append(
                {
                    "emotion": emotion,
                    "feature": feature,
                    "importance_mean": mean,
                    "importance_std": std,
                }
            )

    return pd.DataFrame(rows).sort_values(
        ["emotion", "importance_mean"], ascending=[True, False]
    )


def main(
    features_path: Path = typer.Option(Path("artifacts/features.csv")),
    targets_path: Path = typer.Option(Path("artifacts/targets.csv")),
    output_dir: Path = typer.Option(Path("artifacts")),
) -> None:
    x, y = load_dataset(features_path, targets_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_idx, test_idx = stratified_split(y["genre"])
    x_train = x.iloc[train_idx]
    x_test = x.iloc[test_idx]
    y_train = y.iloc[train_idx].drop(columns=["genre"]).rename(columns=lambda c: c.replace("p_", ""))
    y_test = y.iloc[test_idx].drop(columns=["genre"]).rename(columns=lambda c: c.replace("p_", ""))

    overall = compute_overall_importance(x_train, y_train, x_test, y_test)
    overall.to_csv(output_dir / "feature_importance_overall.csv", index=False)

    by_emotion = compute_emotion_importance(x_train, y_train, x_test, y_test)
    by_emotion.to_csv(output_dir / "feature_importance_by_emotion.csv", index=False)

    typer.echo(f"Saved overall importance to {output_dir / 'feature_importance_overall.csv'}")
    typer.echo(
        f"Saved per-emotion importance to {output_dir / 'feature_importance_by_emotion.csv'}"
    )


if __name__ == "__main__":
    typer.run(main)
