#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.28",
#   "orjson>=3.10",
#   "pandas>=2.2",
#   "pyarrow>=20.0",
#   "rich>=14.0",
#   "tenacity>=9.1",
#   "typer>=0.16",
# ]
# ///

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
import math
import os
import re
import subprocess
from typing import Any

import httpx
import pandas as pd
from rich.traceback import install
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
import typer

from tds_p1_common import DERIVED_DIR, RAW_DIR, ensure_dir, read_json, write_json

install(show_locals=True)

app = typer.Typer(add_completion=False)

QUESTION_ID = "q-pr-merge-server"
BASE_URL = "https://api.github.com"
PR_URL_RE = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/pulls?/(\d+)(?:[/?#][^\s]*)?", re.I)
BOT_LOGIN_RE = re.compile(r"\[bot\]|bot$|github-actions|renovate|dependabot|mergify|pre-commit-ci", re.I)
DOC_EXTS = {".md", ".rst", ".txt", ".adoc", ".markdown"}
CODE_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".rb", ".rs", ".c", ".cc", ".cpp", ".h", ".hpp", ".cs",
    ".php", ".swift", ".kt", ".scala", ".lua", ".r", ".sql", ".m", ".jl",
}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico", ".avif"}
ASSESSMENT_SINKS = {
    "firstcontributions/first-contributions",
    "lingdojo/kana-dojo",
    "syknapse/contribute-to-this-project",
}
SINK_REPO_NAMES = {
    "first-contributions": "firstcontributions/first-contributions",
    "kana-dojo": "lingdojo/kana-dojo",
    "contribute-to-this-project": "syknapse/contribute-to-this-project",
}
CONFIG_JSON_NAMES = {
    "package.json",
    "package-lock.json",
    "composer.json",
    "tsconfig.json",
    "jsconfig.json",
    "deno.json",
    "deno.jsonc",
    "manifest.json",
    "appsscript.json",
    "cargo.json",
}


def canonical_pr_url(text: str) -> tuple[str, str, str, str] | None:
    match = PR_URL_RE.search(str(text or "").strip())
    if not match:
        return None
    owner, repo, number = match.group(1), match.group(2), match.group(3)
    if repo.endswith(".git"):
        repo = repo[:-4]
    canonical = f"https://github.com/{owner}/{repo}/pull/{number}"
    if owner.upper() == "OWNER" or repo.upper() == "REPO":
        return None
    return owner, repo, number, canonical


def auth_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return token
    result = subprocess.run(
        ["gh", "auth", "token"],
        check=True,
        capture_output=True,
        text=True,
    )
    token = result.stdout.strip()
    if not token:
        raise RuntimeError("No GitHub token available. Run `gh auth login` or set GITHUB_TOKEN.")
    return token


@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    reraise=True,
)
def fetch_json(client: httpx.Client, url: str) -> httpx.Response:
    response = client.get(url)
    if response.status_code == 403 and "rate limit" in response.text.lower():
        response.raise_for_status()
    if response.status_code >= 400:
        response.raise_for_status()
    return response


def fetch_paginated_json(client: httpx.Client, url: str) -> list[Any]:
    rows: list[Any] = []
    next_url = url
    while next_url:
        response = fetch_json(client, next_url)
        payload = response.json()
        if isinstance(payload, list):
            rows.extend(payload)
        else:
            rows.append(payload)
        next_link = response.links.get("next", {})
        next_url = next_link.get("url", "")
    return rows


def raw_repo_path(owner: str, repo: str) -> Path:
    return RAW_DIR / "github" / "repos" / owner / f"{repo}.json"


def raw_pr_dir(owner: str, repo: str, number: str) -> Path:
    return RAW_DIR / "github" / "pulls" / owner / repo / str(number)


def is_bot(user: dict[str, Any] | None) -> bool:
    if not user:
        return False
    if str(user.get("type") or "") == "Bot":
        return True
    return bool(BOT_LOGIN_RE.search(str(user.get("login") or "")))


def user_login(user: dict[str, Any] | None) -> str:
    return str((user or {}).get("login") or "")


def iso_to_ts(value: str | None) -> pd.Timestamp | pd.NaT:
    if not value:
        return pd.NaT
    try:
        return pd.Timestamp(value)
    except Exception:  # noqa: BLE001
        return pd.NaT


def fetch_if_missing(client: httpx.Client, path: Path, url: str, *, paginated: bool = False) -> Any:
    if path.exists():
        return read_json(path)
    ensure_dir(path.parent)
    payload = fetch_paginated_json(client, url) if paginated else fetch_json(client, url).json()
    write_json(path, payload)
    return payload


def classify_file(path: str) -> str:
    lower = path.lower()
    name = Path(path).name.lower()
    suffix = Path(path).suffix.lower()
    if any(token in lower for token in ["/i18n/", "/locale/", "/locales/", "/translations/"]):
        return "translation"
    if lower.startswith(".github/") or suffix in {".yml", ".yaml", ".toml", ".ini", ".cfg"}:
        return "config"
    if any(token in lower for token in ["/test", "/tests", "/spec", "__tests__"]):
        return "test"
    if suffix in DOC_EXTS or any(name in lower for name in ["readme", "changelog", "contributing", "/docs/"]):
        return "docs"
    if suffix in CODE_EXTS:
        return "code"
    if suffix in IMAGE_EXTS:
        return "asset"
    if suffix == ".lock":
        return "config"
    if suffix == ".json":
        if name in CONFIG_JSON_NAMES or any(token in lower for token in ["/config/", "/configs/", "/settings/"]):
            return "config"
        return "data"
    return "other"


def classify_pr_type(files: list[dict[str, Any]], additions: int, deletions: int) -> str:
    categories = {classify_file(str(file.get("filename") or "")) for file in files if file.get("filename")}
    categories.discard("other")
    total_lines = additions + deletions
    if not categories:
        return "OTHER"
    if categories <= {"docs"}:
        return "TYPO_FIX" if total_lines <= 10 else "DOCS_UPDATE"
    if categories <= {"config"}:
        return "CONFIG_CHANGE"
    if categories <= {"translation"}:
        return "TRANSLATION"
    if categories <= {"test"}:
        return "TEST_CHANGE"
    if categories <= {"data"}:
        return "CONTENT_DATA"
    if categories <= {"asset"}:
        return "ASSET_CHANGE"
    if categories <= {"code"}:
        return "CODE_CHANGE"
    if "code" in categories and "test" in categories and categories <= {"code", "test"}:
        return "CODE_PLUS_TEST"
    if "code" in categories:
        return "MIXED_CODE"
    return "MIXED_NONCODE"


def canonical_repo_family(full_name: str, repo_name: str) -> str:
    repo_name = str(repo_name or "").strip().lower()
    full_name = str(full_name or "").strip().lower()
    return SINK_REPO_NAMES.get(repo_name, full_name)


def value_score(record: dict[str, Any]) -> float:
    score = 0.0
    pr_type = record["pr_type"]
    if pr_type in {"CODE_CHANGE", "CODE_PLUS_TEST"}:
        score += 6
    elif pr_type == "TEST_CHANGE":
        score += 5
    elif pr_type == "CONTENT_DATA":
        score += 4
    elif pr_type == "CONFIG_CHANGE":
        score += 3
    elif pr_type == "DOCS_UPDATE":
        score += 2
    elif pr_type == "TYPO_FIX":
        score += 1
    if record["human_reviewers"] > 0:
        score += 3
    if record["manual_participants"] > 0:
        score += 1
    if record["required_edits"]:
        score += 2
    if record["repo_family"] not in ASSESSMENT_SINKS:
        score += 3
    if record["self_merged"]:
        score -= 2
    score += min(math.log10(max(record["repo_stars"], 1)), 5)
    score += min(record["changed_files"], 10) * 0.1
    score += min(record["additions"] + record["deletions"], 100) * 0.02
    return round(score, 2)


def enrich_one_pr(owner: str, repo: str, number: str, url: str, client: httpx.Client) -> dict[str, Any]:
    def error_record(message: str, status: str) -> dict[str, Any]:
        submitted_repo_key = f"{owner}/{repo}".lower()
        return {
            "owner": owner,
            "repo": repo,
            "number": int(number),
            "pr_url": url,
            "submitted_repo_key": submitted_repo_key,
            "repo_key": submitted_repo_key,
            "repo_family": canonical_repo_family(submitted_repo_key, repo),
            "head_repo_key": "",
            "repo_stars": 0,
            "repo_forks": 0,
            "repo_archived": False,
            "repo_fork": False,
            "language": "",
            "title": "",
            "body": message,
            "state": "",
            "draft": False,
            "created_at": pd.NaT,
            "merged_at": pd.NaT,
            "updated_at": pd.NaT,
            "closed_at": pd.NaT,
            "merge_latency_hours": None,
            "merged_by_login": "",
            "merged_by_bot": False,
            "author_login": "",
            "author_association": "",
            "self_merged": False,
            "additions": 0,
            "deletions": 0,
            "changed_files": 0,
            "commits": 0,
            "commit_emails": "",
            "review_count": 0,
            "review_comment_count": 0,
            "issue_comment_count": 0,
            "approvals": 0,
            "changes_requested": 0,
            "commented_reviews": 0,
            "human_reviewers": 0,
            "bot_reviewers": 0,
            "human_issue_commenters": 0,
            "human_review_commenters": 0,
            "manual_participants": 0,
            "approval_type": "FETCH_ERROR",
            "manual_reviewed": False,
            "manual_interaction": False,
            "bot_only": False,
            "required_edits": False,
            "accepted_as_is": False,
            "commits_after_feedback": 0,
            "first_feedback_at": pd.NaT,
            "files_sample": "",
            "pr_type": "FETCH_ERROR",
            "api_status": status,
            "value_score": 0.0,
        }

    repo_path = raw_repo_path(owner, repo)
    pr_dir = ensure_dir(raw_pr_dir(owner, repo, number))
    try:
        repo_json = fetch_if_missing(client, repo_path, f"{BASE_URL}/repos/{owner}/{repo}")
        pr_json = fetch_if_missing(client, pr_dir / "pr.json", f"{BASE_URL}/repos/{owner}/{repo}/pulls/{number}")
    except Exception as exc:  # noqa: BLE001
        return error_record(str(exc), "fetch-error")

    comments_count = int(pr_json.get("comments") or 0)
    review_comments_count = int(pr_json.get("review_comments") or 0)
    changed_files_count = int(pr_json.get("changed_files") or 0)
    commits_count = int(pr_json.get("commits") or 0)

    try:
        reviews = fetch_if_missing(
            client,
            pr_dir / "reviews.json",
            f"{BASE_URL}/repos/{owner}/{repo}/pulls/{number}/reviews?per_page=100",
            paginated=True,
        )
        files = fetch_if_missing(
            client,
            pr_dir / "files.json",
            f"{BASE_URL}/repos/{owner}/{repo}/pulls/{number}/files?per_page=100",
            paginated=True,
        ) if changed_files_count else []
        commits = fetch_if_missing(
            client,
            pr_dir / "commits.json",
            f"{BASE_URL}/repos/{owner}/{repo}/pulls/{number}/commits?per_page=100",
            paginated=True,
        ) if commits_count else []
        issue_comments = fetch_if_missing(
            client,
            pr_dir / "issue_comments.json",
            f"{BASE_URL}/repos/{owner}/{repo}/issues/{number}/comments?per_page=100",
            paginated=True,
        ) if comments_count else []
        review_comments = fetch_if_missing(
            client,
            pr_dir / "review_comments.json",
            f"{BASE_URL}/repos/{owner}/{repo}/pulls/{number}/comments?per_page=100",
            paginated=True,
        ) if review_comments_count else []
    except Exception as exc:  # noqa: BLE001
        return error_record(str(exc), "partial-fetch-error")

    author_login = user_login(pr_json.get("user"))
    merged_by_login = user_login(pr_json.get("merged_by"))
    submitted_repo_key = f"{owner}/{repo}".lower()
    base_repo = ((pr_json.get("base") or {}).get("repo") or {})
    head_repo = ((pr_json.get("head") or {}).get("repo") or {})
    repo_key = str(base_repo.get("full_name") or submitted_repo_key).lower()
    repo_family = canonical_repo_family(repo_key, base_repo.get("name") or repo)
    head_repo_key = str(head_repo.get("full_name") or "").lower()
    repo_info = base_repo or repo_json

    external_reviews = [review for review in reviews if user_login(review.get("user")) != author_login]
    review_states = pd.Series([str(review.get("state") or "") for review in external_reviews]).value_counts().to_dict()
    human_reviewers = {
        user_login(review.get("user"))
        for review in external_reviews
        if user_login(review.get("user")) and not is_bot(review.get("user"))
    }
    bot_reviewers = {
        user_login(review.get("user"))
        for review in external_reviews
        if user_login(review.get("user")) and is_bot(review.get("user"))
    }

    external_issue_comments = [comment for comment in issue_comments if user_login(comment.get("user")) != author_login]
    external_review_comments = [
        comment for comment in review_comments if user_login(comment.get("user")) != author_login
    ]
    human_issue_commenters = {
        user_login(comment.get("user"))
        for comment in external_issue_comments
        if user_login(comment.get("user")) and not is_bot(comment.get("user"))
    }
    human_review_commenters = {
        user_login(comment.get("user"))
        for comment in external_review_comments
        if user_login(comment.get("user")) and not is_bot(comment.get("user"))
    }
    manual_participants = human_reviewers | human_issue_commenters | human_review_commenters

    feedback_times: list[pd.Timestamp] = []
    for review in external_reviews:
        submitted_at = iso_to_ts(review.get("submitted_at"))
        if not pd.isna(submitted_at):
            feedback_times.append(submitted_at)
    for comment in external_issue_comments:
        created_at = iso_to_ts(comment.get("created_at"))
        if not pd.isna(created_at):
            feedback_times.append(created_at)
    for comment in external_review_comments:
        created_at = iso_to_ts(comment.get("created_at"))
        if not pd.isna(created_at):
            feedback_times.append(created_at)
    first_feedback_at = min(feedback_times) if feedback_times else pd.NaT

    commit_times = []
    commit_emails = set()
    for commit in commits:
        author_email = str((((commit.get("commit") or {}).get("author") or {}).get("email")) or "").strip().lower()
        if author_email:
            commit_emails.add(author_email)
        commit_time = iso_to_ts((((commit.get("commit") or {}).get("committer") or {}).get("date")))
        if pd.isna(commit_time):
            commit_time = iso_to_ts((((commit.get("commit") or {}).get("author") or {}).get("date")))
        if not pd.isna(commit_time):
            commit_times.append(commit_time)
    commits_after_feedback = int(sum(commit_time > first_feedback_at for commit_time in commit_times)) if not pd.isna(first_feedback_at) else 0

    manual_reviewed = len(human_reviewers) > 0
    manual_interaction = len(manual_participants) > 0
    requested_changes = int(review_states.get("CHANGES_REQUESTED", 0)) > 0
    bot_only = not manual_interaction and (len(bot_reviewers) > 0 or is_bot(pr_json.get("merged_by")))
    if manual_reviewed and int(review_states.get("APPROVED", 0)) > 0:
        approval_type = "MANUAL_APPROVED"
    elif bot_only:
        approval_type = "BOT_OR_AUTO"
    elif manual_interaction:
        approval_type = "MANUAL_COMMENT_OR_DIRECT"
    else:
        approval_type = "DIRECT_OR_NO_REVIEW"

    additions = int(pr_json.get("additions") or 0)
    deletions = int(pr_json.get("deletions") or 0)
    changed_files = len(files)
    pr_type = classify_pr_type(files, additions, deletions)
    created_at = iso_to_ts(pr_json.get("created_at"))
    merged_at = iso_to_ts(pr_json.get("merged_at"))
    merge_latency_hours = (
        round((merged_at - created_at).total_seconds() / 3600, 2)
        if not pd.isna(created_at) and not pd.isna(merged_at)
        else None
    )
    self_merged = bool(author_login and merged_by_login and author_login == merged_by_login)

    record = {
        "owner": owner,
        "repo": repo,
        "number": int(number),
        "pr_url": url,
        "submitted_repo_key": submitted_repo_key,
        "repo_key": repo_key,
        "repo_family": repo_family,
        "head_repo_key": head_repo_key,
        "repo_stars": int(repo_info.get("stargazers_count") or 0),
        "repo_forks": int(repo_info.get("forks_count") or 0),
        "repo_archived": bool(repo_info.get("archived")),
        "repo_fork": bool(repo_info.get("fork")),
        "language": str(repo_info.get("language") or ""),
        "title": str(pr_json.get("title") or ""),
        "body": str(pr_json.get("body") or ""),
        "state": str(pr_json.get("state") or ""),
        "draft": bool(pr_json.get("draft")),
        "created_at": created_at,
        "merged_at": merged_at,
        "updated_at": iso_to_ts(pr_json.get("updated_at")),
        "closed_at": iso_to_ts(pr_json.get("closed_at")),
        "merge_latency_hours": merge_latency_hours,
        "merged_by_login": merged_by_login,
        "merged_by_bot": is_bot(pr_json.get("merged_by")),
        "author_login": author_login,
        "author_association": str(pr_json.get("author_association") or ""),
        "self_merged": self_merged,
        "additions": additions,
        "deletions": deletions,
        "changed_files": changed_files,
        "commits": int(pr_json.get("commits") or 0),
        "commit_emails": ",".join(sorted(commit_emails)),
        "review_count": len(external_reviews),
        "review_comment_count": len(external_review_comments),
        "issue_comment_count": len(external_issue_comments),
        "approvals": int(review_states.get("APPROVED", 0)),
        "changes_requested": int(review_states.get("CHANGES_REQUESTED", 0)),
        "commented_reviews": int(review_states.get("COMMENTED", 0)),
        "human_reviewers": len(human_reviewers),
        "bot_reviewers": len(bot_reviewers),
        "human_issue_commenters": len(human_issue_commenters),
        "human_review_commenters": len(human_review_commenters),
        "manual_participants": len(manual_participants),
        "approval_type": approval_type,
        "manual_reviewed": manual_reviewed,
        "manual_interaction": manual_interaction,
        "bot_only": bot_only,
        "required_edits": requested_changes or commits_after_feedback > 0,
        "accepted_as_is": not (requested_changes or commits_after_feedback > 0),
        "commits_after_feedback": commits_after_feedback,
        "first_feedback_at": first_feedback_at,
        "files_sample": " | ".join(str(file.get("filename") or "") for file in files[:10]),
        "pr_type": pr_type,
        "api_status": "ok",
    }
    record["value_score"] = value_score(record)
    return record


@app.command()
def main(limit: int = 0, force_refresh: bool = False) -> None:
    """Fetch cached GitHub PR details for successful q-pr-merge submissions."""

    attempts = pd.read_parquet(DERIVED_DIR / "question_attempts.parquet")
    subset = attempts[
        (attempts["question_id"] == QUESTION_ID)
        & (attempts["score"] > 0)
        & (attempts["has_answer"])
    ].copy()

    extracted_rows: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    for row in subset.itertuples(index=False):
        parsed = canonical_pr_url(row.answer_text)
        if not parsed:
            invalid_rows.append(
                {
                    "submission_id": int(row.submission_id),
                    "email": row.email,
                    "submitted_at_utc": pd.Timestamp(row.submitted_at_utc),
                    "answer_text": row.answer_text,
                }
            )
            continue
        owner, repo, number, url = parsed
        extracted_rows.append(
            {
                "submission_id": int(row.submission_id),
                "email": row.email,
                "submitted_at_utc": pd.Timestamp(row.submitted_at_utc),
                "owner": owner,
                "repo": repo,
                "number": int(number),
                "pr_url": url,
            }
        )

    extracted = pd.DataFrame.from_records(extracted_rows).sort_values(["owner", "repo", "number", "submitted_at_utc"])
    invalid = pd.DataFrame.from_records(invalid_rows)
    extracted.to_parquet(DERIVED_DIR / "pr_success_submissions.parquet", index=False)
    if not invalid.empty:
        invalid.to_parquet(DERIVED_DIR / "pr_invalid_success_rows.parquet", index=False)

    unique_prs = (
        extracted.groupby(["owner", "repo", "number", "pr_url"], as_index=False)
        .agg(
            success_rows=("submission_id", "size"),
            distinct_students=("email", "nunique"),
            first_submission_at=("submitted_at_utc", "min"),
            last_submission_at=("submitted_at_utc", "max"),
        )
        .sort_values(["owner", "repo", "number"])
    )
    if limit > 0:
        unique_prs = unique_prs.head(limit)

    token = auth_token()
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "tds-p1-pr-enrichment",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    unique_repos = unique_prs[["owner", "repo"]].drop_duplicates().to_dict(orient="records")
    with httpx.Client(timeout=60, follow_redirects=True, headers=headers) as client:
        for repo_row in unique_repos:
            repo_path = raw_repo_path(repo_row["owner"], repo_row["repo"])
            if force_refresh and repo_path.exists():
                repo_path.unlink()
            try:
                fetch_if_missing(client, repo_path, f"{BASE_URL}/repos/{repo_row['owner']}/{repo_row['repo']}")
            except Exception as exc:  # noqa: BLE001
                write_json(
                    repo_path,
                    {
                        "_error": str(exc),
                        "generated_at_utc": datetime.now(UTC).isoformat(),
                    },
                )

        pr_records: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for row in unique_prs.itertuples(index=False):
                pr_dir = raw_pr_dir(row.owner, row.repo, str(row.number))
                if force_refresh and pr_dir.exists():
                    for child in pr_dir.glob("*.json"):
                        child.unlink()
                futures.append(
                    executor.submit(enrich_one_pr, row.owner, row.repo, str(row.number), row.pr_url, client)
                )
            for index, future in enumerate(as_completed(futures), start=1):
                pr_records.append(future.result())
                if index % 50 == 0 or index == len(futures):
                    typer.echo(f"[pr] enriched {index}/{len(futures)}")

    enriched = pd.DataFrame.from_records(pr_records)
    merged = unique_prs.merge(enriched, on=["owner", "repo", "number", "pr_url"], how="left")
    merged.to_parquet(DERIVED_DIR / "pr_enriched.parquet", index=False)

    summary = {
        "successful_rows": int(len(extracted)),
        "invalid_success_rows": int(len(invalid)),
        "unique_prs": int(len(merged)),
        "unique_repos": int(merged["repo_key"].nunique()),
        "manual_reviewed_prs": int(merged["manual_reviewed"].sum()),
        "bot_only_prs": int(merged["bot_only"].sum()),
        "required_edits_prs": int(merged["required_edits"].sum()),
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }
    write_json(DERIVED_DIR / "pr_enriched_summary.json", summary)
    typer.echo(f"[pr] done: {summary}")


if __name__ == "__main__":
    app()
