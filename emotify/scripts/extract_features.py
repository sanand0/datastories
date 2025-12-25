#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "librosa>=0.10.1",
#   "numpy>=1.26",
#   "pandas>=2.2",
#   "soundfile>=0.12",
#   "typer>=0.12",
#   "tqdm>=4.66",
# ]
# ///
"""Extract audio features and target proportions for Emotify tracks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import librosa
import numpy as np
import pandas as pd
import typer
from tqdm import tqdm

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
class TrackInfo:
    genre: str
    track_id: int
    path: Path


def load_annotations(csv_path: Path) -> pd.DataFrame:
    """Load annotations and compute per-track emotion proportions."""
    df = pd.read_csv(csv_path)
    df.columns = [col.strip() for col in df.columns]
    df = df.rename(columns={"joyful_activation": "joy", "track id": "track_id"})

    missing = [emotion for emotion in EMOTIONS if emotion not in df.columns]
    if missing:
        raise ValueError(f"Missing emotion columns: {missing}")

    grouped = df.groupby(["genre", "track_id"], as_index=False)
    counts = grouped[EMOTIONS].sum()
    sizes = grouped.size().rename(columns={"size": "n_raters"})
    counts = counts.merge(sizes, on=["genre", "track_id"], how="left")
    for emotion in EMOTIONS:
        counts[f"p_{emotion}"] = counts[emotion] / counts["n_raters"]

    return counts[["genre", "track_id", "n_raters"] + [f"p_{e}" for e in EMOTIONS]]


def resolve_tracks(root: Path, targets: pd.DataFrame) -> list[TrackInfo]:
    """Resolve audio paths for each (genre, track_id)."""
    genre_offsets = (
        targets.groupby("genre")["track_id"].min().to_dict()
        if not targets.empty
        else {}
    )
    tracks: list[TrackInfo] = []
    for row in targets.itertuples(index=False):
        genre = str(row.genre)
        track_id = int(row.track_id)
        offset = genre_offsets.get(genre, 1)
        local_id = track_id - offset + 1
        path = root / genre / f"{local_id}.opus"
        if not path.exists():
            raise FileNotFoundError(f"Missing audio file: {path}")
        tracks.append(TrackInfo(genre=genre, track_id=track_id, path=path))
    return tracks


def aggregate_stats(values: np.ndarray, name: str) -> dict[str, float]:
    """Aggregate statistics for a 1D array."""
    return {
        f"{name}_mean": float(np.mean(values)),
        f"{name}_std": float(np.std(values)),
        f"{name}_p25": float(np.percentile(values, 25)),
        f"{name}_p75": float(np.percentile(values, 75)),
    }


def aggregate_matrix(values: np.ndarray, name: str) -> dict[str, float]:
    """Aggregate statistics for a 2D array with shape (features, frames)."""
    output: dict[str, float] = {}
    for idx, row in enumerate(values):
        output.update(aggregate_stats(row, f"{name}_{idx}"))
    return output


def extract_features(path: Path, sr: int = 22_050) -> dict[str, float]:
    """Extract frame-based audio features and aggregate them."""
    y, sr = librosa.load(path, sr=sr, mono=True)
    if y.size == 0:
        raise ValueError(f"Empty audio file: {path}")

    n_fft = 2048
    hop_length = 512

    rms = librosa.feature.rms(y=y, frame_length=n_fft, hop_length=hop_length)[0]
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=n_fft, hop_length=hop_length)[0]
    centroid = librosa.feature.spectral_centroid(
        y=y, sr=sr, n_fft=n_fft, hop_length=hop_length
    )[0]
    bandwidth = librosa.feature.spectral_bandwidth(
        y=y, sr=sr, n_fft=n_fft, hop_length=hop_length
    )[0]
    rolloff = librosa.feature.spectral_rolloff(
        y=y, sr=sr, n_fft=n_fft, hop_length=hop_length
    )[0]
    flatness = librosa.feature.spectral_flatness(y=y, n_fft=n_fft, hop_length=hop_length)[0]
    contrast = librosa.feature.spectral_contrast(
        y=y, sr=sr, n_fft=n_fft, hop_length=hop_length
    )
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=n_fft, hop_length=hop_length)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    tempo = float(
        librosa.feature.rhythm.tempo(
            onset_envelope=onset_env, sr=sr, hop_length=hop_length
        )[0]
    )

    energy_diff = np.diff(rms, prepend=rms[:1])
    attack_rate = float(np.mean(energy_diff > 0))
    attack_strength = float(np.mean(np.clip(energy_diff, 0, None)))

    features: dict[str, float] = {
        "tempo": tempo,
        "energy_variance": float(np.var(rms)),
        "attack_rate": attack_rate,
        "attack_strength": attack_strength,
    }

    features.update(aggregate_stats(rms, "rms"))
    features.update(aggregate_stats(zcr, "zcr"))
    features.update(aggregate_stats(centroid, "spectral_centroid"))
    features.update(aggregate_stats(bandwidth, "spectral_bandwidth"))
    features.update(aggregate_stats(rolloff, "spectral_rolloff"))
    features.update(aggregate_stats(flatness, "spectral_flatness"))
    features.update(aggregate_stats(onset_env, "onset_strength"))
    features.update(aggregate_matrix(contrast, "spectral_contrast"))
    features.update(aggregate_matrix(chroma, "chroma"))
    features.update(aggregate_matrix(mfcc, "mfcc"))

    return features


def build_feature_table(tracks: Iterable[TrackInfo]) -> pd.DataFrame:
    """Extract features for all tracks."""
    rows = []
    for track in tqdm(list(tracks), desc="Extracting features"):
        row = {
            "genre": track.genre,
            "track_id": track.track_id,
            "path": str(track.path),
        }
        row.update(extract_features(track.path))
        rows.append(row)
    return pd.DataFrame(rows)


def main(
    audio_root: Path = typer.Option(Path("."), help="Root directory with genre folders"),
    annotations: Path = typer.Option(Path("data.csv"), help="Annotations CSV"),
    output_dir: Path = typer.Option(Path("artifacts"), help="Output directory"),
    force: bool = typer.Option(False, help="Recompute even if outputs exist"),
) -> None:
    """Extract features and save to artifacts directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    features_path = output_dir / "features.csv"
    targets_path = output_dir / "targets.csv"

    if not force and features_path.exists() and targets_path.exists():
        typer.echo("Features already exist. Use --force to recompute.")
        raise typer.Exit(code=0)

    targets = load_annotations(annotations)
    tracks = resolve_tracks(audio_root, targets)

    features = build_feature_table(tracks)
    features.to_csv(features_path, index=False)
    targets.to_csv(targets_path, index=False)

    typer.echo(f"Saved features to {features_path}")
    typer.echo(f"Saved targets to {targets_path}")


if __name__ == "__main__":
    typer.run(main)
