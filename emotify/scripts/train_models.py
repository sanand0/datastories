#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "numpy>=1.26",
#   "pandas>=2.2",
#   "scipy>=1.10",
#   "scikit-learn>=1.4",
#   "xgboost>=2.0",
#   "typer>=0.12",
# ]
# ///
"""Train and evaluate multiple models on Emotify features."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import typer
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.multioutput import MultiOutputRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

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
class Dataset:
    features: pd.DataFrame
    targets: pd.DataFrame
    x: np.ndarray
    y: np.ndarray
    genres: np.ndarray
    ids: pd.DataFrame


def load_dataset(features_path: Path, targets_path: Path) -> Dataset:
    """Load features and target proportions."""
    features = pd.read_csv(features_path)
    targets = pd.read_csv(targets_path)

    merged = features.merge(targets, on=["genre", "track_id"], how="inner")
    if merged.empty:
        raise ValueError("No rows after merging features and targets.")

    x = merged.drop(columns=["genre", "track_id", "path"] + [f"p_{e}" for e in EMOTIONS])
    y = merged[[f"p_{e}" for e in EMOTIONS]].to_numpy(dtype=float)
    return Dataset(
        features=features,
        targets=targets,
        x=x.to_numpy(dtype=float),
        y=y,
        genres=merged["genre"].to_numpy(),
        ids=merged[["genre", "track_id", "path"]],
    )


def topk_overlap(y_true: np.ndarray, y_pred: np.ndarray, k: int = 3) -> float:
    """Compute average top-k overlap between prediction and ground truth."""
    overlaps = []
    for true_row, pred_row in zip(y_true, y_pred, strict=True):
        true_top = set(np.argsort(-true_row)[:k])
        pred_top = set(np.argsort(-pred_row)[:k])
        overlaps.append(len(true_top & pred_top) / k)
    return float(np.mean(overlaps))


def calibration_ece(y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10) -> np.ndarray:
    """Compute per-emotion expected calibration error (ECE)."""
    y_pred = np.clip(y_pred, 0, 1)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    eces = []
    for idx in range(y_true.shape[1]):
        pred = y_pred[:, idx]
        true = y_true[:, idx]
        bin_ids = np.digitize(pred, bins) - 1
        ece = 0.0
        for bin_id in range(n_bins):
            mask = bin_ids == bin_id
            if not np.any(mask):
                continue
            weight = np.mean(mask)
            ece += weight * abs(np.mean(pred[mask]) - np.mean(true[mask]))
        eces.append(ece)
    return np.array(eces)


def correlation(
    y_true: np.ndarray, y_pred: np.ndarray, method: str
) -> np.ndarray:
    """Compute per-emotion correlation, handling constant arrays."""
    values = []
    for idx in range(y_true.shape[1]):
        true = y_true[:, idx]
        pred = y_pred[:, idx]
        if np.std(true) < 1e-8 or np.std(pred) < 1e-8:
            values.append(np.nan)
            continue
        if method == "pearson":
            values.append(stats.pearsonr(true, pred)[0])
        elif method == "spearman":
            values.append(stats.spearmanr(true, pred).correlation)
        else:
            raise ValueError(f"Unknown method: {method}")
    return np.array(values, dtype=float)


def evaluate_metrics(
    y_true: np.ndarray, y_pred: np.ndarray
) -> list[dict[str, float | str]]:
    """Compute metrics per emotion and macro averages."""
    y_pred = np.clip(y_pred, 0, 1)
    mae = np.mean(np.abs(y_true - y_pred), axis=0)
    pearson = correlation(y_true, y_pred, method="pearson")
    spearman = correlation(y_true, y_pred, method="spearman")
    ece = calibration_ece(y_true, y_pred)
    topk = topk_overlap(y_true, y_pred)

    def safe_nanmean(values: np.ndarray) -> float:
        if np.all(np.isnan(values)):
            return float("nan")
        return float(np.nanmean(values))

    rows: list[dict[str, float | str]] = []
    for idx, emotion in enumerate(EMOTIONS):
        rows.append({"metric": "mae", "emotion": emotion, "value": float(mae[idx])})
        rows.append(
            {
                "metric": "pearson",
                "emotion": emotion,
                "value": float(pearson[idx]),
            }
        )
        rows.append(
            {
                "metric": "spearman",
                "emotion": emotion,
                "value": float(spearman[idx]),
            }
        )
        rows.append(
            {
                "metric": "ece",
                "emotion": emotion,
                "value": float(ece[idx]),
            }
        )

    rows.append({"metric": "mae", "emotion": "macro", "value": safe_nanmean(mae)})
    rows.append(
        {
            "metric": "pearson",
            "emotion": "macro",
            "value": safe_nanmean(pearson),
        }
    )
    rows.append(
        {
            "metric": "spearman",
            "emotion": "macro",
            "value": safe_nanmean(spearman),
        }
    )
    rows.append({"metric": "ece", "emotion": "macro", "value": safe_nanmean(ece)})
    rows.append({"metric": "topk_overlap", "emotion": "macro", "value": float(topk)})

    return rows


def model_builders() -> dict[str, tuple[object, bool]]:
    """Return model constructors and whether scaling is required."""
    return {
        "Ridge": (MultiOutputRegressor(Ridge(alpha=1.0)), True),
        "RandomForest": (
            RandomForestRegressor(
                n_estimators=400,
                random_state=42,
                n_jobs=-1,
            ),
            False,
        ),
        "XGBoost": (
            MultiOutputRegressor(
                XGBRegressor(
                    objective="reg:squarederror",
                    n_estimators=300,
                    max_depth=5,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_lambda=1.0,
                    random_state=42,
                    n_jobs=-1,
                )
            ),
            False,
        ),
        "MLP": (
            MultiOutputRegressor(
                MLPRegressor(
                    hidden_layer_sizes=(128, 64),
                    random_state=42,
                    max_iter=800,
                    early_stopping=True,
                )
            ),
            True,
        ),
    }


def fit_predict(
    model: object,
    use_scaler: bool,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
) -> np.ndarray:
    """Fit a model and return predictions."""
    if use_scaler:
        pipeline = Pipeline([("scaler", StandardScaler()), ("model", model)])
        pipeline.fit(x_train, y_train)
        return pipeline.predict(x_test)

    model.fit(x_train, y_train)
    return model.predict(x_test)


def evaluate_split(
    name: str,
    genre_label: str | None,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
) -> list[dict[str, float | str]]:
    """Evaluate all models for a given split."""
    rows: list[dict[str, float | str]] = []

    baseline_pred = np.tile(np.mean(y_train, axis=0), (y_test.shape[0], 1))
    for row in evaluate_metrics(y_test, baseline_pred):
        row.update({"split": name, "model": "BaselineMean"})
        if genre_label is not None:
            row["genre"] = genre_label
        rows.append(row)

    for model_name, (model, use_scaler) in model_builders().items():
        preds = fit_predict(model, use_scaler, x_train, y_train, x_test)
        for row in evaluate_metrics(y_test, preds):
            row.update({"split": name, "model": model_name})
            if genre_label is not None:
                row["genre"] = genre_label
            rows.append(row)

    return rows


def stratified_split(dataset: Dataset, test_size: float = 0.2) -> tuple[np.ndarray, np.ndarray]:
    """Create a stratified train/test split by genre."""
    splitter = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=42)
    train_idx, test_idx = next(splitter.split(dataset.x, dataset.genres))
    return train_idx, test_idx


def leave_one_genre_out(dataset: Dataset) -> Iterable[tuple[str, np.ndarray, np.ndarray]]:
    """Generate train/test indices leaving one genre out."""
    for genre in np.unique(dataset.genres):
        test_idx = np.where(dataset.genres == genre)[0]
        train_idx = np.where(dataset.genres != genre)[0]
        yield str(genre), train_idx, test_idx


def run_evaluation(features_path: Path, targets_path: Path, output_dir: Path) -> None:
    """Run all evaluations and save metrics."""
    dataset = load_dataset(features_path, targets_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics_rows: list[dict[str, float | str]] = []

    train_idx, test_idx = stratified_split(dataset)
    metrics_rows.extend(
        evaluate_split(
            "stratified",
            None,
            dataset.x[train_idx],
            dataset.y[train_idx],
            dataset.x[test_idx],
            dataset.y[test_idx],
        )
    )

    for genre, train_idx, test_idx in leave_one_genre_out(dataset):
        metrics_rows.extend(
            evaluate_split(
                "leave_one_genre_out",
                genre,
                dataset.x[train_idx],
                dataset.y[train_idx],
                dataset.x[test_idx],
                dataset.y[test_idx],
            )
        )

    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df.to_csv(output_dir / "metrics.csv", index=False)

    typer.echo(f"Saved metrics to {output_dir / 'metrics.csv'}")


def main(
    features_path: Path = typer.Option(Path("artifacts/features.csv")),
    targets_path: Path = typer.Option(Path("artifacts/targets.csv")),
    output_dir: Path = typer.Option(Path("artifacts")),
) -> None:
    """CLI entrypoint."""
    run_evaluation(features_path, targets_path, output_dir)


if __name__ == "__main__":
    typer.run(main)
