#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "matplotlib>=3.8",
#   "numpy>=2.0",
#   "pandas>=2.2",
#   "scikit-learn>=1.5",
#   "scipy>=1.13",
# ]
# ///

"""Run analyses on cached Libraries.io data and save results to files."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import lognorm, pareto, pearsonr, spearmanr
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LinearRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

CACHE_ROOT = Path(".cache/libraries-io")
OUTPUT_ROOT = Path("analysis_results")
OUTPUT_ROOT.mkdir(exist_ok=True)

NUMERIC_COLUMNS = [
    "dependent_repos_count",
    "dependents_count",
    "forks",
    "stars",
    "rank",
    "contributions_count",
]

DOMAIN_KEYWORDS = {
    "web": [
        "http",
        "web",
        "browser",
        "html",
        "css",
        "react",
        "vue",
        "angular",
        "express",
        "fastapi",
        "flask",
        "django",
        "nextjs",
        "nuxt",
        "server",
        "client",
        "api",
        "graphql",
    ],
    "ml": [
        "ml",
        "ai",
        "machine learning",
        "deep learning",
        "neural",
        "nlp",
        "vision",
        "pytorch",
        "tensorflow",
        "transformer",
        "llm",
    ],
    "data": [
        "data",
        "pandas",
        "numpy",
        "etl",
        "analytics",
        "sql",
        "database",
        "parquet",
        "spark",
        "arrow",
        "csv",
    ],
    "infra": [
        "cloud",
        "aws",
        "gcp",
        "azure",
        "docker",
        "kubernetes",
        "k8s",
        "infra",
        "terraform",
        "devops",
        "serverless",
    ],
    "devtools": [
        "build",
        "lint",
        "format",
        "cli",
        "tooling",
        "compiler",
        "bundler",
        "webpack",
        "vite",
        "rollup",
        "babel",
        "eslint",
    ],
    "testing": [
        "test",
        "pytest",
        "jest",
        "mocha",
        "chai",
        "coverage",
        "mock",
    ],
    "security": [
        "security",
        "auth",
        "oauth",
        "jwt",
        "crypto",
        "encryption",
        "vulnerability",
    ],
    "docs": [
        "docs",
        "documentation",
        "markdown",
        "sphinx",
        "mkdocs",
    ],
}


@dataclass
class FitResult:
    distribution: str
    aic: float
    log_likelihood: float
    params: tuple[float, float, float]


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def log10p1(series: pd.Series) -> pd.Series:
    return np.log10(series.astype(float) + 1.0)


def zscore(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0 or np.isnan(std):
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.mean()) / std


def parse_license(row: pd.Series) -> str:
    license_value = row.get("license_normalized")
    if isinstance(license_value, str) and license_value.strip():
        return license_value.strip()
    for key in ("normalized_licenses", "licenses"):
        value = row.get(key)
        if isinstance(value, list) and value:
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
    return "Unknown"


def normalize_keywords(value: object) -> list[str]:
    if isinstance(value, list):
        keywords = value
    elif isinstance(value, str):
        keywords = re.split(r"[,;/]", value)
    else:
        return []
    cleaned = []
    for keyword in keywords:
        if not isinstance(keyword, str):
            continue
        token = keyword.strip().lower()
        if token:
            cleaned.append(token)
    return cleaned


def parse_repo(url: object) -> tuple[str | None, str | None]:
    if not isinstance(url, str) or not url.strip():
        return None, None
    try:
        parsed = urlparse(url)
    except ValueError:
        return None, None
    host = parsed.netloc.lower() if parsed.netloc else None
    path = parsed.path.strip("/") if parsed.path else ""
    org = None
    if host and path:
        parts = path.split("/")
        if host in {"github.com", "gitlab.com", "bitbucket.org"} and len(parts) >= 1:
            org = parts[0].lower()
    return host, org


def parse_iso_date(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def compute_release_stats(
    versions: object,
) -> tuple[pd.Timestamp | None, pd.Timestamp | None, int, int, float | None]:
    if not isinstance(versions, list) or not versions:
        return None, None, 0, 0, None
    earliest = None
    latest = None
    min_year = None
    max_year = None
    count = 0
    for entry in versions:
        if not isinstance(entry, dict):
            continue
        published = entry.get("published_at")
        if isinstance(published, str) and published:
            count += 1
            if earliest is None or published < earliest:
                earliest = published
            if latest is None or published > latest:
                latest = published
            year_part = published[:4]
            if year_part.isdigit():
                year = int(year_part)
                min_year = year if min_year is None else min(min_year, year)
                max_year = year if max_year is None else max(max_year, year)
    if count == 0:
        return None, None, 0, 0, None
    first_dt = parse_iso_date(earliest) if earliest else None
    last_dt = parse_iso_date(latest) if latest else None
    if min_year is not None and max_year is not None:
        years = max(1, max_year - min_year + 1)
    elif first_dt and last_dt:
        years = max(1, last_dt.year - first_dt.year + 1)
    else:
        years = 1
    return (
        pd.Timestamp(first_dt) if first_dt else None,
        pd.Timestamp(last_dt) if last_dt else None,
        count,
        years,
        count / years,
    )


def assign_domain(text: str) -> str:
    if not text:
        return "other"
    lowered = text.lower()
    scores: dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        scores[domain] = sum(1 for kw in keywords if kw in lowered)
    best_domain = max(scores, key=scores.get)
    if scores[best_domain] == 0:
        return "other"
    ties = [domain for domain, score in scores.items() if score == scores[best_domain]]
    if len(ties) > 1:
        return "multi"
    return best_domain


def load_platform(platform: str) -> pd.DataFrame:
    cache_dir = CACHE_ROOT / platform.lower()
    if not cache_dir.exists():
        raise FileNotFoundError(f"Missing cache directory: {cache_dir}")
    files = sorted(cache_dir.glob("page-*.json"), key=lambda p: int(re.findall(r"\d+", p.stem)[0]))
    items: list[dict[str, object]] = []
    for file_path in files:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            items.extend(data)
    frame = pd.DataFrame(items)
    frame["platform"] = platform
    frame = frame.drop_duplicates(subset=["name"], keep="first")
    return frame


def prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    for column in NUMERIC_COLUMNS:
        frame[column] = numeric(frame.get(column))
    frame["stars_forks"] = frame["stars"] + frame["forks"]
    frame["license"] = frame.apply(parse_license, axis=1)
    frame["keywords_list"] = frame.get("keywords", pd.Series([[]] * len(frame))).apply(normalize_keywords)
    frame["keywords_text"] = frame["keywords_list"].apply(lambda values: " ".join(values))
    frame["description"] = frame.get("description", "").fillna("")
    frame["domain_text"] = (frame["keywords_text"] + " " + frame["description"]).str.strip()
    frame["domain"] = frame["domain_text"].apply(assign_domain)

    release_stats = frame.get("versions", pd.Series([[]] * len(frame))).apply(compute_release_stats)
    frame[[
        "first_release_date",
        "last_release_date",
        "release_count",
        "release_years",
        "releases_per_year",
    ]] = pd.DataFrame(release_stats.tolist(), index=frame.index)

    frame["latest_release_date"] = pd.to_datetime(
        frame.get("latest_release_published_at"), errors="coerce", utc=True
    )
    frame["latest_release_date"] = frame["latest_release_date"].fillna(frame["last_release_date"])
    now = pd.Timestamp.utcnow()
    frame["staleness_days"] = (now - frame["latest_release_date"]).dt.days
    frame["staleness_days"] = frame["staleness_days"].clip(lower=0)
    frame["staleness_years"] = frame["staleness_days"] / 365.25
    frame["first_release_year"] = frame["first_release_date"].dt.year
    frame["last_release_year"] = frame["last_release_date"].dt.year

    frame["log_dependents"] = log10p1(frame["dependents_count"])
    frame["log_repos"] = log10p1(frame["dependent_repos_count"])
    frame["log_stars_forks"] = log10p1(frame["stars_forks"])
    frame["log_contrib"] = log10p1(frame["contributions_count"])
    frame["gap"] = frame["log_dependents"] - frame["log_repos"]
    frame["reverse_gap"] = frame["log_repos"] - frame["log_dependents"]

    frame["hidden_score"] = (
        zscore(frame["log_dependents"]) - zscore(frame["log_repos"]) - zscore(frame["log_stars_forks"])
    )
    frame["critical_fragile"] = (
        zscore(frame["log_dependents"])
        - zscore(frame["log_stars_forks"])
        - zscore(frame["log_contrib"])
        + zscore(frame["staleness_years"].fillna(0))
    )

    repo_info = frame.get("repository_url", pd.Series([None] * len(frame))).apply(parse_repo)
    frame[["repo_host", "repo_org"]] = pd.DataFrame(repo_info.tolist(), index=frame.index)

    return frame


def save_table(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False)


def concentration(values: pd.Series, pct: float) -> float:
    values = values[values > 0].sort_values(ascending=False)
    if values.empty:
        return 0.0
    top_n = max(1, int(len(values) * pct))
    return float(values.iloc[:top_n].sum() / values.sum())


def fit_distribution(values: pd.Series) -> tuple[FitResult, FitResult]:
    values = values[values > 0].astype(float)
    if len(values) < 20:
        raise ValueError("Not enough data to fit distribution")
    lognorm_params = lognorm.fit(values, floc=0)
    pareto_params = pareto.fit(values, floc=0)

    lognorm_ll = float(np.sum(lognorm.logpdf(values, *lognorm_params)))
    pareto_ll = float(np.sum(pareto.logpdf(values, *pareto_params)))

    lognorm_aic = 2 * 3 - 2 * lognorm_ll
    pareto_aic = 2 * 3 - 2 * pareto_ll

    return (
        FitResult("lognormal", lognorm_aic, lognorm_ll, lognorm_params),
        FitResult("pareto", pareto_aic, pareto_ll, pareto_params),
    )


def regression_residuals(x: pd.Series, y: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    mask = (~x.isna()) & (~y.isna())
    if mask.sum() < 2:
        return np.array([]), np.array([])
    coeffs = np.polyfit(x[mask], y[mask], 1)
    predicted = coeffs[0] * x + coeffs[1]
    residuals = y - predicted
    return predicted.to_numpy(), residuals.to_numpy()


def safe_corr(x: pd.Series, y: pd.Series) -> tuple[float | None, float | None, int]:
    data = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(data) < 3:
        return None, None, len(data)
    corr, pval = pearsonr(data["x"], data["y"])
    return float(corr), float(pval), int(len(data))


def outlier_set(
    frame: pd.DataFrame, quantile: float = 0.99, min_repos: int | None = None
) -> tuple[set[str], float | None]:
    subset = frame
    if min_repos is not None:
        subset = subset[subset["dependent_repos_count"] >= min_repos]
    if subset.empty:
        return set(), None
    threshold = subset["gap"].quantile(quantile)
    return set(subset[subset["gap"] >= threshold]["name"]), float(threshold)


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def standardized_regression(
    frame: pd.DataFrame, features: list[str], target: str
) -> tuple[dict[str, float], float, int]:
    data = frame[features + [target]].dropna()
    if len(data) < 5:
        return {}, float("nan"), len(data)
    X = data[features].to_numpy(dtype=float)
    y = data[target].to_numpy(dtype=float)
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_std[X_std == 0] = 1.0
    y_mean = y.mean()
    y_std = y.std() or 1.0
    X_scaled = (X - X_mean) / X_std
    y_scaled = (y - y_mean) / y_std
    model = LinearRegression()
    model.fit(X_scaled, y_scaled)
    coefs = {feature: float(coef) for feature, coef in zip(features, model.coef_)}
    r2 = float(model.score(X_scaled, y_scaled))
    return coefs, r2, len(data)


def top_terms_for_cluster(
    vectorizer: TfidfVectorizer,
    tfidf_matrix,
    labels: np.ndarray,
    cluster_id: int,
    top_n: int = 10,
) -> str:
    feature_names = np.array(vectorizer.get_feature_names_out())
    cluster_rows = tfidf_matrix[labels == cluster_id]
    if cluster_rows.shape[0] == 0:
        return ""
    mean_tfidf = np.asarray(cluster_rows.mean(axis=0)).ravel()
    top_idx = mean_tfidf.argsort()[::-1][:top_n]
    return ", ".join(feature_names[top_idx])


def keyword_surprises(hidden: pd.DataFrame, mainstream: pd.DataFrame) -> pd.DataFrame:
    hidden_counts = Counter()
    mainstream_counts = Counter()

    for keywords in hidden["keywords_list"]:
        hidden_counts.update(set(keywords))
    for keywords in mainstream["keywords_list"]:
        mainstream_counts.update(set(keywords))

    total_hidden = sum(hidden_counts.values()) or 1
    total_mainstream = sum(mainstream_counts.values()) or 1

    rows = []
    all_keywords = set(hidden_counts) | set(mainstream_counts)
    for keyword in all_keywords:
        hidden_count = hidden_counts.get(keyword, 0)
        main_count = mainstream_counts.get(keyword, 0)
        if hidden_count < 3 and main_count < 3:
            continue
        hidden_ratio = hidden_count / total_hidden
        main_ratio = main_count / total_mainstream
        lift = (hidden_ratio / main_ratio) if main_ratio > 0 else float("inf")
        rows.append(
            {
                "keyword": keyword,
                "hidden_count": hidden_count,
                "mainstream_count": main_count,
                "hidden_ratio": hidden_ratio,
                "mainstream_ratio": main_ratio,
                "lift": lift,
            }
        )

    result = pd.DataFrame(rows)
    return result.sort_values("lift", ascending=False)


def build_clusters(frame: pd.DataFrame, platform: str) -> tuple[pd.DataFrame, pd.Series]:
    text_series = frame["domain_text"].fillna("")
    vectorizer = TfidfVectorizer(max_features=5000, min_df=5, stop_words="english")
    tfidf = vectorizer.fit_transform(text_series)

    numeric_features = frame[["gap", "log_dependents", "log_repos", "staleness_years"]].fillna(0).to_numpy()
    scaler = StandardScaler()
    scaled_numeric = scaler.fit_transform(numeric_features)

    svd = TruncatedSVD(n_components=100, random_state=42)
    reduced_text = svd.fit_transform(tfidf)
    combined = np.hstack([reduced_text, scaled_numeric])
    k = 8
    model = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = model.fit_predict(combined)

    cluster_rows = []
    for cluster_id in range(k):
        cluster_frame = frame[labels == cluster_id]
        cluster_rows.append(
            {
                "cluster": cluster_id,
                "count": len(cluster_frame),
                "top_terms": top_terms_for_cluster(vectorizer, tfidf, labels, cluster_id),
                "avg_gap": cluster_frame["gap"].mean(),
                "avg_dependents": cluster_frame["dependents_count"].mean(),
                "avg_dependent_repos": cluster_frame["dependent_repos_count"].mean(),
                "avg_staleness_years": cluster_frame["staleness_years"].mean(),
            }
        )

    cluster_summary = pd.DataFrame(cluster_rows).sort_values("count", ascending=False)
    save_table(cluster_summary, OUTPUT_ROOT / f"{platform}_clusters.csv")
    return cluster_summary, pd.Series(labels, index=frame.index)


def analysis_for_platform(
    frame: pd.DataFrame,
    platform: str,
    distribution_rows: list[dict[str, object]],
    concentration_rows: list[dict[str, object]],
) -> dict[str, object]:
    results: dict[str, object] = {}

    outlier_threshold = frame["gap"].quantile(0.99)
    gap_outliers = frame[frame["gap"] >= outlier_threshold].sort_values("gap", ascending=False)
    save_table(
        gap_outliers[[
            "name",
            "dependents_count",
            "dependent_repos_count",
            "gap",
            "stars",
            "forks",
            "contributions_count",
            "staleness_years",
            "license",
            "repo_host",
        ]],
        OUTPUT_ROOT / f"{platform}_gap_outliers.csv",
    )

    hidden_candidates = frame.copy()
    hidden_candidates["stars_forks"] = hidden_candidates["stars"] + hidden_candidates["forks"]
    hidden_threshold = hidden_candidates["dependents_count"].quantile(0.9)
    hidden = hidden_candidates[
        (hidden_candidates["dependents_count"] >= hidden_threshold)
        & (hidden_candidates["dependent_repos_count"] <= hidden_candidates["dependent_repos_count"].median())
        & (hidden_candidates["stars_forks"] <= hidden_candidates["stars_forks"].median())
    ].sort_values("hidden_score", ascending=False)
    save_table(
        hidden[[
            "name",
            "dependents_count",
            "dependent_repos_count",
            "stars",
            "forks",
            "hidden_score",
            "gap",
            "license",
            "domain",
        ]].head(200),
        OUTPUT_ROOT / f"{platform}_hidden_champions.csv",
    )

    reverse = frame.sort_values("reverse_gap", ascending=False)
    save_table(
        reverse[[
            "name",
            "dependent_repos_count",
            "dependents_count",
            "reverse_gap",
            "stars",
            "forks",
            "license",
            "domain",
        ]].head(200),
        OUTPUT_ROOT / f"{platform}_reverse_gap.csv",
    )

    predicted, residuals = regression_residuals(frame["log_dependents"], frame["log_repos"])
    if residuals.size:
        frame = frame.copy()
        frame["loglog_residual"] = residuals
        save_table(
            frame.sort_values("loglog_residual", ascending=False)[
                ["name", "log_dependents", "log_repos", "loglog_residual", "gap"]
            ].head(200),
            OUTPUT_ROOT / f"{platform}_loglog_residuals_high.csv",
        )
        save_table(
            frame.sort_values("loglog_residual", ascending=True)[
                ["name", "log_dependents", "log_repos", "loglog_residual", "gap"]
            ].head(200),
            OUTPUT_ROOT / f"{platform}_loglog_residuals_low.csv",
        )

        plt.figure(figsize=(6, 4))
        plt.scatter(frame["log_dependents"], frame["log_repos"], alpha=0.2, s=12)
        plt.plot(frame["log_dependents"], predicted, color="red", linewidth=1)
        plt.xlabel("log10(dependents_count + 1)")
        plt.ylabel("log10(dependent_repos_count + 1)")
        plt.title(f"{platform} log-log relationship")
        plt.tight_layout()
        plt.savefig(OUTPUT_ROOT / f"{platform}_loglog_scatter.png", dpi=160)
        plt.close()

    for metric in ["dependents_count", "dependent_repos_count"]:
        try:
            lognorm_fit, pareto_fit = fit_distribution(frame[metric])
        except ValueError:
            continue
        better = lognorm_fit if lognorm_fit.aic < pareto_fit.aic else pareto_fit
        distribution_rows.extend(
            [
                {
                    "platform": platform,
                    "metric": metric,
                    "distribution": lognorm_fit.distribution,
                    "aic": lognorm_fit.aic,
                    "log_likelihood": lognorm_fit.log_likelihood,
                },
                {
                    "platform": platform,
                    "metric": metric,
                    "distribution": pareto_fit.distribution,
                    "aic": pareto_fit.aic,
                    "log_likelihood": pareto_fit.log_likelihood,
                },
                {
                    "platform": platform,
                    "metric": metric,
                    "distribution": "better_fit",
                    "aic": better.aic,
                    "log_likelihood": better.log_likelihood,
                    "winner": better.distribution,
                },
            ]
        )

    for metric in ["dependents_count", "dependent_repos_count"]:
        for pct in [0.01, 0.05, 0.1]:
            concentration_rows.append(
                {
                    "platform": platform,
                    "metric": metric,
                    "top_pct": pct,
                    "share": concentration(frame[metric], pct),
                }
            )

    license_stats = (
        frame.groupby("license")
        .agg(
            count=("name", "count"),
            median_gap=("gap", "median"),
            mean_gap=("gap", "mean"),
        )
        .reset_index()
    )
    license_outlier = frame[frame["gap"] >= outlier_threshold]["license"].value_counts()
    license_stats["outlier_share"] = license_stats["license"].map(
        lambda lic: license_outlier.get(lic, 0) / max(1, (frame["license"] == lic).sum())
    )
    save_table(license_stats.sort_values("count", ascending=False), OUTPUT_ROOT / f"{platform}_license_gap.csv")

    domain_stats = (
        frame.groupby("domain")
        .agg(
            count=("name", "count"),
            median_gap=("gap", "median"),
            mean_gap=("gap", "mean"),
        )
        .reset_index()
    )
    save_table(domain_stats.sort_values("count", ascending=False), OUTPUT_ROOT / f"{platform}_domain_gap.csv")

    stale_threshold = 2.0
    stale = frame[frame["staleness_years"] >= stale_threshold].sort_values(
        "dependents_count", ascending=False
    )
    save_table(
        stale[[
            "name",
            "dependents_count",
            "dependent_repos_count",
            "staleness_years",
            "latest_release_date",
            "license",
        ]].head(200),
        OUTPUT_ROOT / f"{platform}_stale_critical.csv",
    )

    staleness_mask = frame["staleness_years"].notna()
    if staleness_mask.sum() > 2:
        corr, pval = pearsonr(frame.loc[staleness_mask, "staleness_years"], frame.loc[staleness_mask, "log_dependents"])
        results["staleness_corr"] = corr
        results["staleness_pval"] = pval

        plt.figure(figsize=(6, 4))
        plt.scatter(frame["staleness_years"], frame["log_dependents"], alpha=0.2, s=12)
        plt.xlabel("staleness (years)")
        plt.ylabel("log10(dependents_count + 1)")
        plt.title(f"{platform} staleness vs dependence")
        plt.tight_layout()
        plt.savefig(OUTPUT_ROOT / f"{platform}_staleness_scatter.png", dpi=160)
        plt.close()

    cohort_bins = [0, 2010, 2015, 2019, 2023, 2100]
    cohort_labels = ["<=2010", "2011-2015", "2016-2019", "2020-2023", "2024+?"]
    frame["first_release_cohort"] = pd.cut(frame["first_release_year"], bins=cohort_bins, labels=cohort_labels)
    cadence_stats = (
        frame.groupby("first_release_cohort", observed=True)
        .agg(
            count=("name", "count"),
            median_gap=("gap", "median"),
            mean_gap=("gap", "mean"),
            median_releases_per_year=("releases_per_year", "median"),
        )
        .reset_index()
    )
    save_table(cadence_stats, OUTPUT_ROOT / f"{platform}_cadence_cohorts.csv")

    critical_fragile = frame.sort_values("critical_fragile", ascending=False)
    save_table(
        critical_fragile[[
            "name",
            "dependents_count",
            "dependent_repos_count",
            "stars",
            "forks",
            "contributions_count",
            "staleness_years",
            "critical_fragile",
        ]].head(200),
        OUTPUT_ROOT / f"{platform}_critical_fragile.csv",
    )

    deprecated = frame[(frame.get("deprecation_reason").notna()) | (frame.get("status").notna())]
    deprecated = deprecated[(deprecated.get("deprecation_reason").notna()) | (deprecated.get("status") != "Active")]
    save_table(
        deprecated.sort_values("dependents_count", ascending=False)[
            ["name", "status", "deprecation_reason", "dependents_count", "dependent_repos_count", "gap"]
        ].head(200),
        OUTPUT_ROOT / f"{platform}_deprecation_risk.csv",
    )

    host_stats = (
        frame.groupby("repo_host")
        .agg(
            count=("name", "count"),
            median_gap=("gap", "median"),
            mean_gap=("gap", "mean"),
        )
        .reset_index()
        .sort_values("count", ascending=False)
    )
    save_table(host_stats, OUTPUT_ROOT / f"{platform}_repo_hosts.csv")

    github_orgs = frame[frame["repo_host"] == "github.com"]
    org_outliers = github_orgs[github_orgs["gap"] >= outlier_threshold]
    org_stats = (
        org_outliers.groupby("repo_org")
        .agg(outlier_count=("name", "count"), avg_gap=("gap", "mean"))
        .reset_index()
        .sort_values("outlier_count", ascending=False)
    )
    save_table(org_stats.head(200), OUTPUT_ROOT / f"{platform}_github_orgs_hidden.csv")

    predicted_rank, rank_residuals = regression_residuals(frame["log_dependents"], frame["rank"])
    if rank_residuals.size:
        rank_frame = frame.copy()
        rank_frame["rank_residual"] = rank_residuals
        save_table(
            rank_frame.sort_values("rank_residual", ascending=False)[
                ["name", "rank", "dependents_count", "log_dependents", "gap", "rank_residual"]
            ].head(200),
            OUTPUT_ROOT / f"{platform}_rank_gap_underappreciated.csv",
        )
        save_table(
            rank_frame.sort_values("rank_residual", ascending=True)[
                ["name", "rank", "dependents_count", "log_dependents", "gap", "rank_residual"]
            ].head(200),
            OUTPUT_ROOT / f"{platform}_rank_gap_overappreciated.csv",
        )

    hidden_gap = frame[frame["gap"] >= outlier_threshold]
    mainstream = frame.sort_values("dependent_repos_count", ascending=False).head(max(200, int(len(frame) * 0.05)))
    surprises = keyword_surprises(hidden_gap, mainstream)
    save_table(surprises.head(200), OUTPUT_ROOT / f"{platform}_keyword_surprises.csv")

    cluster_summary, cluster_labels = build_clusters(frame, platform)
    frame["cluster"] = cluster_labels

    leverage = frame[
        (frame["dependents_count"] >= hidden_threshold)
        & (frame["dependent_repos_count"] <= frame["dependent_repos_count"].median())
        & (frame["stars_forks"] <= frame["stars_forks"].median())
    ].sort_values(["dependents_count", "gap"], ascending=False)
    save_table(
        leverage[[
            "name",
            "dependents_count",
            "dependent_repos_count",
            "stars",
            "forks",
            "gap",
            "license",
            "domain",
        ]].head(200),
        OUTPUT_ROOT / f"{platform}_leverage_candidates.csv",
    )

    metrics_cols = [
        "name",
        "platform",
        "dependents_count",
        "dependent_repos_count",
        "stars",
        "forks",
        "contributions_count",
        "rank",
        "gap",
        "reverse_gap",
        "hidden_score",
        "critical_fragile",
        "staleness_years",
        "release_count",
        "releases_per_year",
        "first_release_year",
        "last_release_year",
        "license",
        "domain",
        "repo_host",
        "repo_org",
        "status",
        "deprecation_reason",
        "cluster",
        "keywords_text",
    ]
    metrics_frame = frame[metrics_cols]
    save_table(metrics_frame, OUTPUT_ROOT / f"{platform}_metrics.csv")

    results["frame"] = frame
    return results


def main() -> None:
    pypi = prepare_frame(load_platform("pypi"))
    npm = prepare_frame(load_platform("npm"))

    distribution_rows: list[dict[str, object]] = []
    concentration_rows: list[dict[str, object]] = []

    pypi_results = analysis_for_platform(pypi, "pypi", distribution_rows, concentration_rows)
    npm_results = analysis_for_platform(npm, "npm", distribution_rows, concentration_rows)

    if distribution_rows:
        save_table(pd.DataFrame(distribution_rows), OUTPUT_ROOT / "distribution_fits.csv")
    if concentration_rows:
        save_table(pd.DataFrame(concentration_rows), OUTPUT_ROOT / "concentration.csv")

    common = pypi.merge(
        npm,
        on="name",
        suffixes=("_pypi", "_npm"),
        how="inner",
    )
    if not common.empty:
        common["gap_diff"] = common["gap_pypi"] - common["gap_npm"]
        save_table(
            common[[
                "name",
                "gap_pypi",
                "gap_npm",
                "dependents_count_pypi",
                "dependents_count_npm",
                "dependent_repos_count_pypi",
                "dependent_repos_count_npm",
                "gap_diff",
            ]].sort_values("gap_diff", ascending=False),
            OUTPUT_ROOT / "cross_ecosystem_name_collisions.csv",
        )

    staleness_summary = []
    for platform, result in [("pypi", pypi_results), ("npm", npm_results)]:
        if "staleness_corr" in result:
            staleness_summary.append(
                {
                    "platform": platform,
                    "staleness_corr": result["staleness_corr"],
                    "staleness_pval": result["staleness_pval"],
                }
            )
    if staleness_summary:
        save_table(pd.DataFrame(staleness_summary), OUTPUT_ROOT / "staleness_correlation.csv")

    robustness_gap_rows = []
    robustness_min_repos_rows = []
    robustness_subsample_rows = []
    robustness_shuffle_rows = []
    robustness_domain_rows = []
    robustness_regression_rows = []
    robustness_zero_repo_rows = []
    robustness_ratio_rows = []
    robustness_outlier_host_rows = []

    rng = np.random.default_rng(42)

    for platform, frame in [("pypi", pypi), ("npm", npm)]:
        baseline_outliers, baseline_threshold = outlier_set(frame, 0.99)
        baseline_count = len(baseline_outliers)

        for quantile in [0.995, 0.99, 0.98]:
            outliers, threshold = outlier_set(frame, quantile)
            robustness_gap_rows.append(
                {
                    "platform": platform,
                    "quantile": quantile,
                    "outlier_count": len(outliers),
                    "threshold": threshold,
                    "jaccard_with_0.99": jaccard(baseline_outliers, outliers),
                    "overlap_with_0.99": len(baseline_outliers & outliers),
                    "baseline_count": baseline_count,
                }
            )

        for min_repos in [0, 1, 5, 20]:
            outliers, threshold = outlier_set(frame, 0.99, min_repos=min_repos)
            robustness_min_repos_rows.append(
                {
                    "platform": platform,
                    "min_repos": min_repos,
                    "outlier_count": len(outliers),
                    "threshold": threshold,
                    "jaccard_with_0.99": jaccard(baseline_outliers, outliers),
                    "overlap_with_0.99": len(baseline_outliers & outliers),
                    "baseline_count": baseline_count,
                }
            )

        for idx in range(10):
            sample = frame.sample(frac=0.8, random_state=42 + idx)
            outliers, _ = outlier_set(sample, 0.99)
            robustness_subsample_rows.append(
                {
                    "platform": platform,
                    "iteration": idx,
                    "sample_size": len(sample),
                    "outlier_count": len(outliers),
                    "jaccard_with_full": jaccard(baseline_outliers, outliers),
                    "overlap_with_full": len(baseline_outliers & outliers),
                    "baseline_count": baseline_count,
                }
            )

        actual_corr, actual_pval, actual_n = safe_corr(frame["log_dependents"], frame["log_repos"])
        staleness_corr, staleness_pval, staleness_n = safe_corr(
            frame["staleness_years"], frame["log_dependents"]
        )
        robustness_shuffle_rows.append(
            {
                "platform": platform,
                "pair": "log_dependents_vs_log_repos",
                "actual_corr": actual_corr,
                "actual_pval": actual_pval,
                "n": actual_n,
                "shuffle_mean_corr": None,
                "shuffle_std_corr": None,
            }
        )
        robustness_shuffle_rows.append(
            {
                "platform": platform,
                "pair": "staleness_years_vs_log_dependents",
                "actual_corr": staleness_corr,
                "actual_pval": staleness_pval,
                "n": staleness_n,
                "shuffle_mean_corr": None,
                "shuffle_std_corr": None,
            }
        )

        shuffle_corrs = []
        for idx in range(10):
            shuffled = rng.permutation(frame["log_repos"].to_numpy())
            corr, _ = pearsonr(frame["log_dependents"], shuffled)
            shuffle_corrs.append(corr)
        if shuffle_corrs:
            robustness_shuffle_rows.append(
                {
                    "platform": platform,
                    "pair": "log_dependents_vs_log_repos_shuffle",
                    "actual_corr": actual_corr,
                    "actual_pval": actual_pval,
                    "n": actual_n,
                    "shuffle_mean_corr": float(np.mean(shuffle_corrs)),
                    "shuffle_std_corr": float(np.std(shuffle_corrs)),
                }
            )

        for domain, domain_frame in frame.groupby("domain"):
            if len(domain_frame) < 50:
                continue
            dep_corr, dep_pval, dep_n = safe_corr(domain_frame["log_dependents"], domain_frame["log_repos"])
            stale_corr, stale_pval, stale_n = safe_corr(
                domain_frame["staleness_years"], domain_frame["log_dependents"]
            )
            robustness_domain_rows.append(
                {
                    "platform": platform,
                    "domain": domain,
                    "count": len(domain_frame),
                    "dep_repo_corr": dep_corr,
                    "dep_repo_pval": dep_pval,
                    "dep_repo_n": dep_n,
                    "stale_dep_corr": stale_corr,
                    "stale_dep_pval": stale_pval,
                    "stale_dep_n": stale_n,
                }
            )

        coefs, r2, n_rows = standardized_regression(
            frame,
            ["log_repos", "log_stars_forks", "staleness_years"],
            "log_dependents",
        )
        robustness_regression_rows.append(
            {
                "platform": platform,
                "n": n_rows,
                "r2": r2,
                **coefs,
            }
        )

        zero_repos = frame[frame["dependent_repos_count"] == 0]
        dependents_total = frame["dependents_count"].sum() or 1.0
        robustness_zero_repo_rows.append(
            {
                "platform": platform,
                "zero_repo_packages": len(zero_repos),
                "zero_repo_share_packages": len(zero_repos) / len(frame),
                "zero_repo_dependents_share": float(zero_repos["dependents_count"].sum() / dependents_total),
                "zero_repo_median_gap": float(zero_repos["gap"].median()) if len(zero_repos) else None,
            }
        )

        ratio = frame["dependents_count"] / (frame["dependent_repos_count"] + 1)
        ratio_corr, ratio_pval = spearmanr(frame["gap"], ratio)
        ratio_threshold = ratio.quantile(0.99)
        ratio_top = set(frame.loc[ratio >= ratio_threshold, "name"])
        gap_top = baseline_outliers
        robustness_ratio_rows.append(
            {
                "platform": platform,
                "spearman_gap_ratio": float(ratio_corr),
                "spearman_pval": float(ratio_pval),
                "top1_jaccard_gap_ratio": jaccard(gap_top, ratio_top),
                "top1_overlap_gap_ratio": len(gap_top & ratio_top),
            }
        )

        outlier_hosts = (
            frame[frame["name"].isin(baseline_outliers)]["repo_host"]
            .fillna("unknown")
            .value_counts()
        )
        outlier_total = outlier_hosts.sum() or 1
        for host, count in outlier_hosts.items():
            robustness_outlier_host_rows.append(
                {
                    "platform": platform,
                    "repo_host": host,
                    "count": int(count),
                    "share": float(count / outlier_total),
                }
            )

    save_table(pd.DataFrame(robustness_gap_rows), OUTPUT_ROOT / "robustness_gap_thresholds.csv")
    save_table(pd.DataFrame(robustness_min_repos_rows), OUTPUT_ROOT / "robustness_min_repos.csv")
    save_table(pd.DataFrame(robustness_subsample_rows), OUTPUT_ROOT / "robustness_subsample.csv")
    save_table(pd.DataFrame(robustness_shuffle_rows), OUTPUT_ROOT / "robustness_shuffle_corr.csv")
    save_table(pd.DataFrame(robustness_domain_rows), OUTPUT_ROOT / "robustness_domain_corr.csv")
    save_table(pd.DataFrame(robustness_regression_rows), OUTPUT_ROOT / "robustness_regression.csv")
    save_table(pd.DataFrame(robustness_zero_repo_rows), OUTPUT_ROOT / "robustness_zero_repo.csv")
    save_table(pd.DataFrame(robustness_ratio_rows), OUTPUT_ROOT / "robustness_gap_ratio.csv")
    save_table(pd.DataFrame(robustness_outlier_host_rows), OUTPUT_ROOT / "robustness_outlier_hosts.csv")


if __name__ == "__main__":
    main()
