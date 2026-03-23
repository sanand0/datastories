#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.28.1",
#   "numpy>=2.2.4",
#   "pandas>=2.2.3",
#   "python-dotenv>=1.0.1",
#   "ruptures>=1.1.9",
#   "typer>=0.16.0",
# ]
# ///
"""Collect and analyze GitHub commit activity around Nov 2025."""

from __future__ import annotations

import json
import math
import os
import random
import re
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd
import ruptures as rpt
import typer

app = typer.Typer(add_completion=False, help=__doc__)

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "results.md"

HYPOTHESIS_DATE = date(2025, 11, 1)
WINDOW_DAYS = 91
PANEL_START = date(2025, 3, 1)
PANEL_END = date(2026, 2, 28)
SEED_START = date(2025, 5, 1)
SEED_END = date(2025, 10, 31)
RANDOM_SEED = 42
SEARCH_MIN_INTERVAL = 2.5
CORE_MIN_INTERVAL = 0.8
BAD_REPO_PATTERN = re.compile(
    r"(tutorial|example|demo|practice|course|bootcamp|hello[-_ ]?world|sandbox|learn|training|leetcode|kata|test)",
    re.IGNORECASE,
)
DATA_DIR = ROOT / "data" / "github_activity"
RAW_DIR = DATA_DIR / "raw"
ANALYSIS_DIR = DATA_DIR / "analysis"


class GitHubClient:
    """GitHub API client with simple search/core pacing."""

    def __init__(self, token: str) -> None:
        self.client = httpx.Client(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "github-activity-analysis",
            },
            timeout=30.0,
        )
        self.last_search_at = 0.0
        self.last_core_at = 0.0

    def close(self) -> None:
        self.client.close()

    def _sleep_if_needed(self, kind: str) -> None:
        min_interval = SEARCH_MIN_INTERVAL if kind == "search" else CORE_MIN_INTERVAL
        last_request_at = self.last_search_at if kind == "search" else self.last_core_at
        remaining = min_interval - (time.monotonic() - last_request_at)
        if remaining > 0:
            time.sleep(remaining)

    def _mark_request(self, kind: str) -> None:
        now = time.monotonic()
        if kind == "search":
            self.last_search_at = now
        else:
            self.last_core_at = now

    def _sleep_for_reset(self, response: httpx.Response) -> None:
        reset_at = response.headers.get("x-ratelimit-reset")
        if not reset_at:
            return
        delay = max(int(reset_at) - int(time.time()) + 1, 1)
        typer.echo(f"Rate limit exhausted for {response.headers.get('x-ratelimit-resource', 'unknown')}; sleeping {delay}s.")
        time.sleep(delay)

    def request(self, method: str, url: str, *, kind: str, params: dict[str, Any] | None = None) -> httpx.Response:
        attempts = 0
        while True:
            attempts += 1
            self._sleep_if_needed(kind)
            try:
                response = self.client.request(method, url, params=params)
            except httpx.HTTPError:
                if attempts >= 4:
                    raise
                time.sleep(min(2**attempts, 8))
                continue
            self._mark_request(kind)
            if response.status_code == 403:
                if response.headers.get("x-ratelimit-remaining") == "0":
                    self._sleep_for_reset(response)
                    continue
                if kind == "search" and attempts < 4:
                    time.sleep(60)
                    continue
            if response.status_code in {500, 502, 503, 504} and attempts < 4:
                time.sleep(min(2**attempts, 8))
                continue
            return response

    def search_commits(self, *, query: str, per_page: int, page: int = 1, sort: str | None = None) -> tuple[dict[str, Any], httpx.Headers]:
        params: dict[str, Any] = {"q": query, "per_page": per_page, "page": page}
        if sort:
            params["sort"] = sort
        response = self.request("GET", "/search/commits", kind="search", params=params)
        response.raise_for_status()
        return response.json(), response.headers

    def count_repo_commits(self, *, repo: str, author: str, start: date, end: date) -> dict[str, Any]:
        params = {
            "author": author,
            "since": f"{start.isoformat()}T00:00:00Z",
            "until": f"{end.isoformat()}T23:59:59Z",
            "per_page": 1,
            "page": 1,
        }
        response = self.request("GET", f"/repos/{repo}/commits", kind="core", params=params)
        if response.status_code in {404, 409, 422, 500, 502, 503, 504}:
            return {"count": 0, "error": response.status_code, "link": ""}
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, list):
            return {"count": 0, "error": "unexpected_payload", "link": response.headers.get("link", "")}
        last_page = parse_link_last_page(response.headers.get("link"))
        count = last_page if last_page is not None else len(body)
        return {"count": count, "error": "", "link": response.headers.get("link", "")}


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


def configure_paths(batch_label: str) -> None:
    global DATA_DIR, RAW_DIR, ANALYSIS_DIR
    if batch_label == "main":
        DATA_DIR = ROOT / "data" / "github_activity"
    else:
        DATA_DIR = ROOT / "data" / "github_activity" / "batches" / batch_label
    RAW_DIR = DATA_DIR / "raw"
    ANALYSIS_DIR = DATA_DIR / "analysis"


def load_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    raise RuntimeError("GITHUB_TOKEN is required in .env (KEY=VALUE format). Run with `set -a && source .env && ...` or export it first.")


def parse_link_last_page(link_header: str | None) -> int | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        if 'rel="last"' not in part:
            continue
        match = re.search(r"[?&]page=(\d+)", part)
        if match:
            return int(match.group(1))
    return None


def daterange_weeks(start: date, end: date) -> list[tuple[date, date]]:
    ranges: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        bucket_end = min(cursor + timedelta(days=6), end)
        ranges.append((cursor, bucket_end))
        cursor = bucket_end + timedelta(days=1)
    return list(reversed(ranges))


def month_ranges(start: date, end: date) -> list[tuple[str, date, date]]:
    ranges: list[tuple[str, date, date]] = []
    cursor = start.replace(day=1)
    while cursor <= end:
        if cursor.month == 12:
            next_month = cursor.replace(year=cursor.year + 1, month=1, day=1)
        else:
            next_month = cursor.replace(month=cursor.month + 1, day=1)
        month_end = min(next_month - timedelta(days=1), end)
        ranges.append((cursor.strftime("%Y-%m"), cursor, month_end))
        cursor = next_month
    return ranges


def is_good_repo(full_name: str | None, is_fork: bool | None) -> bool:
    if not full_name or is_fork:
        return False
    return BAD_REPO_PATTERN.search(full_name) is None


def safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else math.inf


def pre_post_windows() -> dict[str, date]:
    pre_end = HYPOTHESIS_DATE - timedelta(days=1)
    pre_start = HYPOTHESIS_DATE - timedelta(days=WINDOW_DAYS)
    post_start = HYPOTHESIS_DATE
    post_end = HYPOTHESIS_DATE + timedelta(days=WINDOW_DAYS - 1)
    return {
        "pre_start": pre_start,
        "pre_end": pre_end,
        "post_start": post_start,
        "post_end": post_end,
    }


def classify_user(pre_count: int, post_count: int) -> str:
    ratio = safe_ratio(post_count, pre_count)
    delta = post_count - pre_count
    if pre_count <= 2 and post_count >= 20:
        return "newly_active"
    if pre_count <= 5 and post_count >= max(15, pre_count * 3):
        return "dormant_returner"
    if pre_count >= 10 and 0.67 <= ratio <= 1.5:
        return "consistently_active"
    if pre_count >= 10 and post_count <= pre_count * 0.67 and delta <= -5:
        return "declining"
    if delta >= 10 and ratio >= 2:
        return "meaningful_increase_other"
    return "other"


def collect_seed_observations(
    client: GitHubClient,
    *,
    sample_target: int,
    oversample_factor: float,
    max_pages_per_bucket: int,
    seed_page_start: int,
    seed_start: date,
    seed_end: date,
    excluded_logins: set[str],
) -> pd.DataFrame:
    output_path = RAW_DIR / "seed_observations.csv"
    if output_path.exists():
        return pd.read_csv(output_path)

    target_unique_users = math.ceil(sample_target * oversample_factor)
    unique_users: set[str] = set()
    rows: list[dict[str, Any]] = []

    for page in range(seed_page_start, seed_page_start + max_pages_per_bucket):
        for start, end in daterange_weeks(seed_start, seed_end):
            if len(unique_users) >= target_unique_users:
                break
            query = f"author-date:{start.isoformat()}..{end.isoformat()}"
            body, _ = client.search_commits(query=query, per_page=100, page=page, sort="author-date")
            for item in body.get("items", []):
                author = item.get("author") or {}
                repo = item.get("repository") or {}
                login = author.get("login")
                full_name = repo.get("full_name")
                if not login or author.get("type") != "User":
                    continue
                if login in excluded_logins or login in unique_users:
                    continue
                if login.endswith("[bot]"):
                    continue
                if not is_good_repo(full_name, repo.get("fork")):
                    continue
                commit_author = (item.get("commit") or {}).get("author") or {}
                commit_date = commit_author.get("date")
                if not commit_date:
                    continue
                owner = (full_name or "").split("/", 1)[0]
                rows.append(
                    {
                        "login": login,
                        "repo": full_name,
                        "repo_owner": owner,
                        "owner_matches_login": owner.lower() == login.lower(),
                        "seed_commit_date": commit_date,
                        "seed_sha": item.get("sha"),
                        "seed_query_week_start": start.isoformat(),
                        "seed_query_week_end": end.isoformat(),
                    }
                )
                unique_users.add(login)
            typer.echo(f"Seed page {page}, week {start}..{end}: {len(unique_users)} unique users")
            pd.DataFrame(rows).to_csv(output_path, index=False)
        if len(unique_users) >= target_unique_users:
            break

    observations = pd.DataFrame(rows)
    observations.to_csv(output_path, index=False)
    return observations


def build_candidates(observations: pd.DataFrame, *, max_repos_per_user: int) -> pd.DataFrame:
    output_path = RAW_DIR / "seed_candidates.csv"
    if output_path.exists():
        return pd.read_csv(output_path)

    rows: list[dict[str, Any]] = []
    for login, group in observations.groupby("login", sort=False):
        repo_scores = (
            group.groupby(["repo", "repo_owner", "owner_matches_login"], as_index=False)
            .agg(observations=("repo", "size"), last_seen=("seed_commit_date", "max"))
            .sort_values(["owner_matches_login", "observations", "last_seen", "repo"], ascending=[False, False, False, True])
        )
        selected_repos = repo_scores.head(max_repos_per_user)
        rows.append(
            {
                "login": login,
                "observed_commits": int(len(group)),
                "observed_repo_count": int(group["repo"].nunique()),
                "selected_repo_count": int(len(selected_repos)),
                "selected_repos": "|".join(selected_repos["repo"].tolist()),
                "primary_repo": selected_repos.iloc[0]["repo"],
                "primary_repo_owner_match": bool(selected_repos.iloc[0]["owner_matches_login"]),
                "latest_seed_commit_date": group["seed_commit_date"].max(),
            }
        )

    candidates = pd.DataFrame(rows).sort_values(["observed_commits", "latest_seed_commit_date", "login"], ascending=[False, False, True])
    candidates.to_csv(output_path, index=False)
    return candidates


def repo_list_from_row(row: dict[str, Any], *, limit: int) -> list[str]:
    values = [value for value in str(row.get("selected_repos", "")).split("|") if value]
    return values[:limit]


def count_user_across_repos(
    client: GitHubClient,
    *,
    login: str,
    repos: list[str],
    start: date,
    end: date,
) -> tuple[int, list[dict[str, Any]]]:
    details: list[dict[str, Any]] = []
    total = 0
    for repo in repos:
        result = client.count_repo_commits(repo=repo, author=login, start=start, end=end)
        total += int(result["count"])
        details.append({"repo": repo, "count": int(result["count"]), "error": result["error"]})
    return total, details


def load_excluded_logins(batch_labels: str | None) -> set[str]:
    if not batch_labels:
        return set()
    excluded: set[str] = set()
    for batch_label in [part.strip() for part in batch_labels.split(",") if part.strip()]:
        batch_root = ROOT / "data" / "github_activity"
        if batch_label != "main":
            batch_root = batch_root / "batches" / batch_label
        user_windows_path = batch_root / "raw" / "user_windows.csv"
        if not user_windows_path.exists():
            continue
        frame = pd.read_csv(user_windows_path)
        excluded.update(frame["login"].astype(str))
    return excluded


def collect_user_windows(
    client: GitHubClient,
    candidates: pd.DataFrame,
    *,
    sample_target: int,
    max_repos_per_user: int,
) -> pd.DataFrame:
    output_path = RAW_DIR / "user_windows.csv"
    existing = pd.read_csv(output_path) if output_path.exists() else pd.DataFrame()
    processed = set(existing.get("login", pd.Series(dtype=str)).astype(str))
    rows = existing.to_dict("records") if not existing.empty else []
    eligible_count = int(existing.get("eligible", pd.Series(dtype=bool)).fillna(False).sum()) if not existing.empty else 0
    windows = pre_post_windows()

    candidate_rows = candidates.to_dict("records")
    random.Random(RANDOM_SEED).shuffle(candidate_rows)

    for index, candidate in enumerate(candidate_rows, start=1):
        login = str(candidate["login"])
        if login in processed:
            continue
        if eligible_count >= sample_target:
            break

        repos = repo_list_from_row(candidate, limit=max_repos_per_user)
        pre_count, pre_details = count_user_across_repos(
            client,
            login=login,
            repos=repos,
            start=windows["pre_start"],
            end=windows["pre_end"],
        )
        if pre_count <= 0:
            row = {
                **candidate,
                "eligible": False,
                "exclude_reason": "no_pre_window_activity",
                "pre_count": pre_count,
                "post_count": np.nan,
                "pre_repo_counts": json.dumps(pre_details),
                "post_repo_counts": "",
                "cohort": "excluded",
            }
        else:
            post_count, post_details = count_user_across_repos(
                client,
                login=login,
                repos=repos,
                start=windows["post_start"],
                end=windows["post_end"],
            )
            row = {
                **candidate,
                "eligible": True,
                "exclude_reason": "",
                "pre_count": pre_count,
                "post_count": post_count,
                "pre_repo_counts": json.dumps(pre_details),
                "post_repo_counts": json.dumps(post_details),
                "cohort": classify_user(pre_count, post_count),
            }
            eligible_count += 1

        rows.append(row)
        processed.add(login)

        if index % 25 == 0 or eligible_count >= sample_target:
            pd.DataFrame(rows).to_csv(output_path, index=False)
            typer.echo(f"Processed {len(processed)} candidates; eligible users={eligible_count}")

    final_df = pd.DataFrame(rows)
    final_df.to_csv(output_path, index=False)
    return final_df


def collect_monthly_aggregate(
    client: GitHubClient,
    eligible_users: pd.DataFrame,
    *,
    aggregate_subset_size: int,
    monthly_repos_per_user: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    subset_path = RAW_DIR / "aggregate_subset.csv"
    counts_path = RAW_DIR / "monthly_user_counts.csv"

    eligible = eligible_users.loc[eligible_users["eligible"] == True].copy()
    if subset_path.exists():
        subset = pd.read_csv(subset_path)
    else:
        subset_size = min(aggregate_subset_size, len(eligible))
        subset = eligible.sample(n=subset_size, random_state=RANDOM_SEED).sort_values("login")
        subset.to_csv(subset_path, index=False)

    if counts_path.exists():
        monthly_user_counts = pd.read_csv(counts_path)
    else:
        rows: list[dict[str, Any]] = []
        for month_label, start, end in month_ranges(PANEL_START, PANEL_END):
            for row in subset.to_dict("records"):
                repos = repo_list_from_row(row, limit=monthly_repos_per_user)
                count, repo_details = count_user_across_repos(
                    client,
                    login=str(row["login"]),
                    repos=repos,
                    start=start,
                    end=end,
                )
                rows.append(
                    {
                        "month": month_label,
                        "month_start": start.isoformat(),
                        "month_end": end.isoformat(),
                        "login": row["login"],
                        "repos_used": "|".join(repos),
                        "count": count,
                        "repo_counts": json.dumps(repo_details),
                    }
                )
            pd.DataFrame(rows).to_csv(counts_path, index=False)
            typer.echo(f"Monthly aggregate complete for {month_label}")
        monthly_user_counts = pd.DataFrame(rows)

    monthly = (
        monthly_user_counts.groupby(["month", "month_start", "month_end"], as_index=False)["count"]
        .sum()
        .sort_values("month_start")
    )
    monthly["subset_users"] = len(subset)
    monthly["eligible_users"] = len(eligible)
    monthly["scaled_count"] = monthly["count"] * monthly["eligible_users"] / monthly["subset_users"]
    monthly.to_csv(RAW_DIR / "monthly_aggregate.csv", index=False)
    return subset, monthly


def build_analysis(user_windows: pd.DataFrame, monthly: pd.DataFrame) -> dict[str, Any]:
    eligible = user_windows.loc[user_windows["eligible"] == True].copy()
    eligible["delta"] = eligible["post_count"] - eligible["pre_count"]
    eligible["ratio"] = np.where(eligible["pre_count"] > 0, eligible["post_count"] / eligible["pre_count"], np.inf)
    eligible["meaningful_increase"] = (eligible["delta"] >= 10) & (eligible["ratio"] >= 2.0)
    eligible["strong_increase"] = (eligible["delta"] >= 15) & (eligible["ratio"] >= 2.5)
    eligible["meaningful_decrease"] = (eligible["delta"] <= -10) & (eligible["ratio"] <= 0.5)
    eligible["strong_decrease"] = (eligible["delta"] <= -15) & (eligible["ratio"] <= 0.4)
    eligible["decline_flag"] = eligible["meaningful_decrease"]

    eligible.to_csv(ANALYSIS_DIR / "eligible_user_windows.csv", index=False)
    eligible.sort_values("delta", ascending=False).head(25).to_csv(ANALYSIS_DIR / "top_increasers.csv", index=False)
    eligible.sort_values("delta").head(25).to_csv(ANALYSIS_DIR / "top_decliners.csv", index=False)
    cohort_counts = eligible["cohort"].value_counts().rename_axis("cohort").reset_index(name="users")
    cohort_counts["share"] = cohort_counts["users"] / len(eligible)
    cohort_counts.to_csv(ANALYSIS_DIR / "cohort_counts.csv", index=False)

    monthly = monthly.copy()
    monthly["log_scaled_count"] = np.log1p(monthly["scaled_count"])
    signal = monthly[["log_scaled_count"]].to_numpy(dtype=float)
    model = rpt.Pelt(model="l2", min_size=2).fit(signal)
    penalty = max(np.var(signal) * np.log(len(signal)), 1.0)
    breakpoints = model.predict(pen=penalty)
    break_months = [monthly.iloc[index - 1]["month"] for index in breakpoints if index < len(monthly)]

    scan_rows: list[dict[str, Any]] = []
    values = monthly["log_scaled_count"].to_numpy(dtype=float)
    for split in range(2, len(values) - 1):
        left = values[:split]
        right = values[split:]
        sse = ((left - left.mean()) ** 2).sum() + ((right - right.mean()) ** 2).sum()
        scan_rows.append(
            {
                "split_index": split,
                "month_after_split": monthly.iloc[split]["month"],
                "sse": float(sse),
                "left_mean": float(left.mean()),
                "right_mean": float(right.mean()),
            }
        )
    one_break = min(scan_rows, key=lambda row: row["sse"])
    pd.DataFrame(scan_rows).to_csv(ANALYSIS_DIR / "one_break_scan.csv", index=False)
    monthly.to_csv(ANALYSIS_DIR / "monthly_series.csv", index=False)

    hypo_month = HYPOTHESIS_DATE.strftime("%Y-%m")
    pre_mask = monthly["month"] < hypo_month
    post_mask = monthly["month"] >= hypo_month
    summary = {
        "eligible_users": int(len(eligible)),
        "meaningful_increase_users": int(eligible["meaningful_increase"].sum()),
        "meaningful_increase_share": float(eligible["meaningful_increase"].mean()),
        "strong_increase_users": int(eligible["strong_increase"].sum()),
        "strong_increase_share": float(eligible["strong_increase"].mean()),
        "meaningful_decrease_users": int(eligible["meaningful_decrease"].sum()),
        "meaningful_decrease_share": float(eligible["meaningful_decrease"].mean()),
        "strong_decrease_users": int(eligible["strong_decrease"].sum()),
        "strong_decrease_share": float(eligible["strong_decrease"].mean()),
        "declining_users": int(eligible["decline_flag"].sum()),
        "declining_share": float(eligible["decline_flag"].mean()),
        "median_pre_count": float(eligible["pre_count"].median()),
        "median_post_count": float(eligible["post_count"].median()),
        "mean_pre_count": float(eligible["pre_count"].mean()),
        "mean_post_count": float(eligible["post_count"].mean()),
        "monthly_pre_mean": float(monthly.loc[pre_mask, "scaled_count"].mean()),
        "monthly_post_mean": float(monthly.loc[post_mask, "scaled_count"].mean()),
        "pelt_break_months": break_months,
        "best_one_break_month": one_break["month_after_split"],
    }
    pd.DataFrame([summary]).to_csv(ANALYSIS_DIR / "summary_metrics.csv", index=False)
    return summary


def parse_repo_count_json(cell: Any) -> list[dict[str, Any]]:
    if not isinstance(cell, str) or not cell.strip():
        return []
    return json.loads(cell)


def run_efficiency_experiments(user_windows: pd.DataFrame, monthly_user_counts: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    eligible = user_windows.loc[user_windows["eligible"] == True].copy()
    eligible["pre_primary_repo_count"] = eligible["pre_repo_counts"].map(lambda cell: sum(item["count"] for item in parse_repo_count_json(cell)[:1]))
    eligible["post_primary_repo_count"] = eligible["post_repo_counts"].map(lambda cell: sum(item["count"] for item in parse_repo_count_json(cell)[:1]))
    eligible["primary_repo_share_pre"] = np.where(eligible["pre_count"] > 0, eligible["pre_primary_repo_count"] / eligible["pre_count"], np.nan)
    eligible["primary_repo_share_post"] = np.where(eligible["post_count"] > 0, eligible["post_primary_repo_count"] / eligible["post_count"], np.nan)

    one_repo_increase = ((eligible["post_primary_repo_count"] - eligible["pre_primary_repo_count"] >= 10) & (eligible["post_primary_repo_count"] / eligible["pre_primary_repo_count"].replace(0, np.nan) >= 2)).fillna(False)
    two_repo_increase = eligible["meaningful_increase"] if "meaningful_increase" in eligible else ((eligible["post_count"] - eligible["pre_count"] >= 10) & (eligible["post_count"] / eligible["pre_count"].replace(0, np.nan) >= 2)).fillna(False)
    one_repo_decrease = ((eligible["post_primary_repo_count"] - eligible["pre_primary_repo_count"] <= -10) & (eligible["post_primary_repo_count"] / eligible["pre_primary_repo_count"].replace(0, np.nan) <= 0.5)).fillna(False)
    two_repo_decrease = ((eligible["post_count"] - eligible["pre_count"] <= -10) & (eligible["post_count"] / eligible["pre_count"].replace(0, np.nan) <= 0.5)).fillna(False)

    monthly_summary = (
        monthly_user_counts.groupby("month")
        .agg(total=("count", "sum"), median=("count", "median"), p95=("count", lambda s: s.quantile(0.95)))
        .reset_index()
    )
    experiments = pd.DataFrame(
        [
            {
                "experiment": "one_repo_prepost",
                "api_saving_pct_vs_two_repos": 50.0,
                "median_primary_repo_share_pre_pct": float(eligible["primary_repo_share_pre"].median() * 100),
                "median_primary_repo_share_post_pct": float(eligible["primary_repo_share_post"].median() * 100),
                "meaningful_increase_agreement_pct": float((one_repo_increase == two_repo_increase).mean() * 100),
                "meaningful_decrease_agreement_pct": float((one_repo_decrease == two_repo_decrease).mean() * 100),
            },
            {
                "experiment": "monthly_panel_50_vs_100",
                "api_saving_pct_vs_100_users": 50.0,
                "notes_value": float(monthly_summary["median"].mean()),
                "meaningful_increase_agreement_pct": np.nan,
                "meaningful_decrease_agreement_pct": np.nan,
            },
        ]
    )
    experiments.to_csv(ANALYSIS_DIR / "efficiency_experiments.csv", index=False)
    return experiments, {
        "median_primary_repo_share_pre_pct": float(eligible["primary_repo_share_pre"].median() * 100),
        "median_primary_repo_share_post_pct": float(eligible["primary_repo_share_post"].median() * 100),
        "increase_agreement_pct": float((one_repo_increase == two_repo_increase).mean() * 100),
        "decrease_agreement_pct": float((one_repo_decrease == two_repo_decrease).mean() * 100),
    }


def build_robustness_tables(monthly_user_counts: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = monthly_user_counts.copy()
    raw["month"] = raw["month"].astype(str)
    user_totals = raw.groupby("login")["count"].sum().sort_values(ascending=False)
    cutoff_99 = user_totals.quantile(0.99)
    cutoff_95 = user_totals.quantile(0.95)
    keep_99 = user_totals[user_totals <= cutoff_99].index
    keep_95 = user_totals[user_totals <= cutoff_95].index

    series_map = {
        "raw_sum": raw.groupby("month")["count"].sum().sort_index(),
        "exclude_top_1pct_users": raw[raw["login"].isin(keep_99)].groupby("month")["count"].sum().sort_index(),
        "exclude_top_5pct_users": raw[raw["login"].isin(keep_95)].groupby("month")["count"].sum().sort_index(),
        "winsorized_95": raw.assign(count_cap=raw.groupby("month")["count"].transform(lambda s: s.clip(upper=s.quantile(0.95)))).groupby("month")["count_cap"].sum().sort_index(),
        "median_user_count": raw.groupby("month")["count"].median().sort_index(),
    }

    series_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    hypo = HYPOTHESIS_DATE.strftime("%Y-%m")
    for name, series in series_map.items():
        for month, value in series.items():
            series_rows.append({"series": name, "month": month, "value": float(value)})
        vals = np.log1p(series.to_numpy(dtype=float)).reshape(-1, 1)
        model = rpt.Pelt(model="l2", min_size=2).fit(vals)
        penalty = max(np.var(vals) * np.log(len(vals)), 1.0)
        breakpoints = [index for index in model.predict(pen=penalty) if index < len(series)]
        break_months = "|".join(series.index[index - 1] for index in breakpoints)
        best_month = None
        best_sse = None
        arr = np.log1p(series.to_numpy(dtype=float))
        for split in range(2, len(arr) - 1):
            left = arr[:split]
            right = arr[split:]
            sse = float(((left - left.mean()) ** 2).sum() + ((right - right.mean()) ** 2).sum())
            if best_sse is None or sse < best_sse:
                best_sse = sse
                best_month = series.index[split]
        pre = float(series[series.index < hypo].mean())
        post = float(series[series.index >= hypo].mean())
        summary_rows.append(
            {
                "series": name,
                "pre_mean": pre,
                "post_mean": post,
                "lift_pct": (post / pre - 1) * 100 if pre else np.nan,
                "pelt_break_months": break_months,
                "best_one_break_month": best_month,
            }
        )

    robustness_series = pd.DataFrame(series_rows)
    robustness_summary = pd.DataFrame(summary_rows)
    concentration = pd.DataFrame(
        [
            {
                "top_10_user_share_pct": user_totals.head(10).sum() / user_totals.sum() * 100,
                "top_1pct_cutoff_total_commits": cutoff_99,
                "top_5pct_cutoff_total_commits": cutoff_95,
            }
        ]
    )
    robustness_series.to_csv(ANALYSIS_DIR / "robustness_series.csv", index=False)
    robustness_summary.to_csv(ANALYSIS_DIR / "robustness_summary.csv", index=False)
    concentration.to_csv(ANALYSIS_DIR / "concentration_metrics.csv", index=False)
    return robustness_summary, concentration


def render_results(summary: dict[str, Any], user_windows: pd.DataFrame, monthly: pd.DataFrame, *, sample_target: int, aggregate_subset_size: int, max_repos_per_user: int, monthly_repos_per_user: int, efficiency: dict[str, float], robustness_summary: pd.DataFrame, concentration: pd.DataFrame) -> str:
    eligible = user_windows.loc[user_windows["eligible"] == True].copy()
    cohort_table = (
        eligible["cohort"]
        .value_counts(normalize=False)
        .rename_axis("cohort")
        .reset_index(name="users")
        .assign(share=lambda frame: (frame["users"] / len(eligible) * 100).round(1))
    )
    cohort_lines = "\n".join(
        f"- `{row.cohort}`: {int(row.users)} users ({row.share:.1f}%)"
        for row in cohort_table.itertuples(index=False)
    )
    break_months = ", ".join(summary["pelt_break_months"]) if summary["pelt_break_months"] else "none"
    hypo_month = HYPOTHESIS_DATE.strftime("%Y-%m")
    before = monthly.loc[monthly["month"] < hypo_month, "scaled_count"].mean()
    after = monthly.loc[monthly["month"] >= hypo_month, "scaled_count"].mean()
    lift = ((after / before) - 1) * 100 if before else float("nan")
    top10_share = float(concentration.iloc[0]["top_10_user_share_pct"])
    winsor = robustness_summary.loc[robustness_summary["series"] == "winsorized_95"].iloc[0]
    trimmed = robustness_summary.loc[robustness_summary["series"] == "exclude_top_1pct_users"].iloc[0]

    return f"""# GitHub activity analysis

## Headline

Using a pre-break-biased sample of {summary['eligible_users']} GitHub users, {summary['meaningful_increase_users']} users ({summary['meaningful_increase_share'] * 100:.1f}%) showed a meaningful post-{HYPOTHESIS_DATE.isoformat()} increase under the primary rule of at least +10 commits and at least a 2x lift in the 91-day post window versus the 91-day pre window. Symmetrically, {summary['meaningful_decrease_users']} users ({summary['meaningful_decrease_share'] * 100:.1f}%) showed a meaningful decrease of at least -10 commits and at least a 50% drop.

The aggregate monthly series points to a break around **{summary['best_one_break_month']}** in the one-break scan, while `ruptures` with PELT detected: **{break_months}**.

Average monthly commits in the sampled cohort proxy rose from {before:,.1f} before {hypo_month} to {after:,.1f} after it, a change of {lift:.1f}%.

That raw rise is not robust: the top 10 users account for {top10_share:.1f}% of monthly commits in the panel, trimming the top 1% changes the post-Nov shift to {trimmed['lift_pct']:.1f}%, and winsorizing at 95% changes it to {winsor['lift_pct']:.1f}%.

## Method

- Seeded candidate users from `/search/commits` queries restricted to **May-Oct 2025**, so users were sampled for pre-break activity rather than post-break activity.
- Filtered out non-user accounts, bots, fork commits, obvious tutorial/demo repos, and users with zero activity in the pre window.
- Counted commits with the repo commits REST endpoint and the `per_page=1` + `Link` header trick, summing across up to **{max_repos_per_user} observed repos per user** discovered in the seed phase.
- Built a 12-month monthly series from **{PANEL_START.isoformat()}** to **{PANEL_END.isoformat()}** on a random subset of **{aggregate_subset_size} users**, using up to **{monthly_repos_per_user} repo per user** for the panel to stay within the API budget.

## Cohorts

{cohort_lines}

## Symmetric increase / decrease metrics

- Meaningful increases: `{summary['meaningful_increase_users']}` users ({summary['meaningful_increase_share'] * 100:.1f}%)
- Strong increases: `{summary['strong_increase_users']}` users ({summary['strong_increase_share'] * 100:.1f}%)
- Meaningful decreases: `{summary['meaningful_decrease_users']}` users ({summary['meaningful_decrease_share'] * 100:.1f}%)
- Strong decreases: `{summary['strong_decrease_users']}` users ({summary['strong_decrease_share'] * 100:.1f}%)

## Efficiency experiments

- Using only the primary observed repo for pre/post windows would cut those API calls roughly in half. In the collected data, the primary repo captured a median of {efficiency['median_primary_repo_share_pre_pct']:.1f}% of pre-window commits and {efficiency['median_primary_repo_share_post_pct']:.1f}% of post-window commits.
- On the first-batch validation, one-repo counting matched the two-repo meaningful-increase label {efficiency['increase_agreement_pct']:.1f}% of the time and the meaningful-decrease label {efficiency['decrease_agreement_pct']:.1f}% of the time.
- The monthly panel is already the expensive part; reducing it from 100 users to 50 would save roughly half those panel requests, so the best optimization is: `1 repo/user` for pre/post plus a smaller or more targeted monthly panel.

## Caveats

- This is observational GitHub activity, so it does **not** prove Opus 4.5 caused any shift; it only tests whether activity changed around that period.
- The repo-based counts capture activity in the users' observed active repos from the seed phase, not necessarily every repository they touched on GitHub.
- Because the monthly panel is the expensive part, the 12-month change-point series is estimated from a representative subcohort rather than the full user sample.

## Files

- Raw seed/users/monthly data: `data/github_activity/raw/`
- Analysis tables: `data/github_activity/analysis/`
- This memo: `results.md`
"""


@app.command()
def collect(
    sample_target: int = typer.Option(900, min=10, help="Target number of eligible users."),
    aggregate_subset_size: int = typer.Option(100, min=10, help="Subset size for monthly change-point series."),
    oversample_factor: float = typer.Option(1.6, min=1.2, help="Seed oversampling factor."),
    max_seed_pages_per_bucket: int = typer.Option(1, min=1, max=5, help="How many pages to scan per seed week."),
    max_repos_per_user: int = typer.Option(2, min=1, max=5, help="How many observed repos to count per user for pre/post windows."),
    monthly_repos_per_user: int = typer.Option(1, min=1, max=3, help="How many observed repos per user to use in the monthly panel."),
    batch_label: str = typer.Option("main", help="Output batch label; 'main' keeps the legacy top-level paths."),
    seed_page_start: int = typer.Option(1, min=1, help="Starting search page within each week bucket."),
    exclude_batch_label: str | None = typer.Option(None, help="Optional batch label whose logins should be excluded from seeding."),
    seed_start_date: str = typer.Option(SEED_START.isoformat(), help="Seed window start date, YYYY-MM-DD."),
    seed_end_date: str = typer.Option(SEED_END.isoformat(), help="Seed window end date, YYYY-MM-DD."),
) -> None:
    """Collect candidate users, repo-based pre/post counts, and monthly aggregate counts."""
    configure_paths(batch_label)
    ensure_dirs()
    token = load_token()
    client = GitHubClient(token)
    try:
        seed_start = date.fromisoformat(seed_start_date)
        seed_end = date.fromisoformat(seed_end_date)
        excluded_logins = load_excluded_logins(exclude_batch_label)
        observations = collect_seed_observations(
            client,
            sample_target=sample_target,
            oversample_factor=oversample_factor,
            max_pages_per_bucket=max_seed_pages_per_bucket,
            seed_page_start=seed_page_start,
            seed_start=seed_start,
            seed_end=seed_end,
            excluded_logins=excluded_logins,
        )
        candidates = build_candidates(observations, max_repos_per_user=max_repos_per_user)
        user_windows = collect_user_windows(
            client,
            candidates,
            sample_target=sample_target,
            max_repos_per_user=max_repos_per_user,
        )
        eligible = user_windows.loc[user_windows["eligible"] == True]
        if eligible.empty:
            raise RuntimeError("No eligible users collected.")
        subset, monthly = collect_monthly_aggregate(
            client,
            eligible,
            aggregate_subset_size=aggregate_subset_size,
            monthly_repos_per_user=monthly_repos_per_user,
        )
        metadata = {
            "collected_at_utc": datetime.now(UTC).isoformat(),
            "sample_target": sample_target,
            "aggregate_subset_size": aggregate_subset_size,
            "oversample_factor": oversample_factor,
            "max_seed_pages_per_bucket": max_seed_pages_per_bucket,
            "max_repos_per_user": max_repos_per_user,
            "monthly_repos_per_user": monthly_repos_per_user,
            "batch_label": batch_label,
            "seed_page_start": seed_page_start,
            "exclude_batch_label": exclude_batch_label or "",
            "seed_start_date": seed_start_date,
            "seed_end_date": seed_end_date,
            "observations": int(len(observations)),
            "candidate_users": int(candidates["login"].nunique()),
            "eligible_users": int(len(eligible)),
            "monthly_subset_users": int(len(subset)),
            **{key: value.isoformat() for key, value in pre_post_windows().items()},
        }
        pd.DataFrame([metadata]).to_csv(RAW_DIR / "collection_metadata.csv", index=False)
        typer.echo(f"Collection complete: {len(eligible)} eligible users, {len(monthly)} monthly rows.")
    finally:
        client.close()


@app.command()
def analyze(batch_labels: str = typer.Option("main", help="Comma-separated batch labels to analyze together.")) -> None:
    """Run cohort metrics and change-point detection, then write results.md."""
    labels = [label.strip() for label in batch_labels.split(",") if label.strip()]
    user_frames: list[pd.DataFrame] = []
    monthly_user_frames: list[pd.DataFrame] = []
    metadata_rows: list[dict[str, Any]] = []
    for label in labels:
        configure_paths(label)
        ensure_dirs()
        user_frame = pd.read_csv(RAW_DIR / "user_windows.csv")
        monthly_user_frame = pd.read_csv(RAW_DIR / "monthly_user_counts.csv")
        metadata_row = pd.read_csv(RAW_DIR / "collection_metadata.csv").iloc[0].to_dict()
        user_frame["batch_label"] = label
        monthly_user_frame["batch_label"] = label
        metadata_row["batch_label"] = label
        user_frames.append(user_frame)
        monthly_user_frames.append(monthly_user_frame)
        metadata_rows.append(metadata_row)

    configure_paths("main")
    ensure_dirs()
    user_windows = pd.concat(user_frames, ignore_index=True)
    monthly_user_counts = pd.concat(monthly_user_frames, ignore_index=True)
    metadata = pd.DataFrame(metadata_rows)
    subset_users = monthly_user_counts["login"].nunique()
    eligible_users = int((user_windows["eligible"] == True).sum())
    monthly = (
        monthly_user_counts.groupby(["month", "month_start", "month_end"], as_index=False)["count"]
        .sum()
        .sort_values("month_start")
    )
    monthly["subset_users"] = subset_users
    monthly["eligible_users"] = eligible_users
    monthly["scaled_count"] = monthly["count"] * monthly["eligible_users"] / monthly["subset_users"]
    monthly.to_csv(ANALYSIS_DIR / "monthly_series_combined_input.csv", index=False)
    summary = build_analysis(user_windows, monthly)
    robustness_summary, concentration = build_robustness_tables(monthly_user_counts)
    _, efficiency = run_efficiency_experiments(user_windows, monthly_user_counts)
    RESULTS_PATH.write_text(
        render_results(
            summary,
            user_windows,
            monthly,
            sample_target=int(metadata["sample_target"].sum()),
            aggregate_subset_size=int(metadata["monthly_subset_users"].sum()),
            max_repos_per_user=int(metadata["max_repos_per_user"].max()),
            monthly_repos_per_user=int(metadata["monthly_repos_per_user"].max()),
            efficiency=efficiency,
            robustness_summary=robustness_summary,
            concentration=concentration,
        )
    )
    typer.echo(f"Analysis complete. Results written to {RESULTS_PATH}")


if __name__ == "__main__":
    app()
