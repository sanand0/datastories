# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "openreview-py",
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import openreview
from dotenv import load_dotenv

VENUE_ID = "Agents4Science/2025/Conference"
SUBMISSION_INVITATION = f"{VENUE_ID}/-/Submission"
OUTPUT_PATH = Path("reviews.json")
REVIEW_NAME_FALLBACK = "Official_Review"
MAX_RETRIES = 5
DEFAULT_RETRY_SECONDS = 20


def utc_now_iso() -> str:
    """Return an ISO timestamp in UTC with timezone info."""
    return datetime.now(timezone.utc).isoformat()


def get_client() -> openreview.api.OpenReviewClient:
    """Create an authenticated OpenReview client."""
    load_dotenv()
    return openreview.api.OpenReviewClient(
        baseurl="https://api2.openreview.net",
        username=os.environ["OPENREVIEW_USERNAME"],
        password=os.environ["OPENREVIEW_PASSWORD"],
    )


def retry_after_seconds(error: dict[str, Any]) -> int:
    """Estimate how long to wait before retrying a rate-limited request."""
    message = str(error.get("message", ""))
    match = re.search(r"try again in (\d+) seconds", message)
    if match:
        return max(1, int(match.group(1)) + 1)

    reset_time = error.get("details", {}).get("resetTime")
    if reset_time:
        try:
            reset_dt = datetime.fromisoformat(reset_time.replace("Z", "+00:00"))
        except ValueError:
            return DEFAULT_RETRY_SECONDS
        return max(1, int((reset_dt - datetime.now(timezone.utc)).total_seconds()) + 1)

    return DEFAULT_RETRY_SECONDS


def fetch_notes_with_retry(
    client: openreview.api.OpenReviewClient, invitation: str
) -> list[openreview.api.Note]:
    """Fetch notes with retries on rate limiting."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.get_all_notes(invitation=invitation)
        except openreview.OpenReviewException as exc:
            error = exc.args[0] if exc.args else {}
            if isinstance(error, dict) and error.get("status") == 429 and attempt < MAX_RETRIES:
                wait_seconds = retry_after_seconds(error)
                print(f"Rate limited on {invitation}; retrying in {wait_seconds}s.")
                time.sleep(wait_seconds)
                continue
            raise
    return []


def load_existing_reviews(path: Path) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    """Load previously downloaded reviews if present."""
    if not path.exists():
        return [], set(), set()

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list):
        reviews = data
        processed = set()
    else:
        reviews = data.get("reviews", []) if isinstance(data, dict) else []
        processed = (
            set(data.get("processed_submission_ids", [])) if isinstance(data, dict) else set()
        )

    review_ids = {review.get("id") for review in reviews if review.get("id")}
    return reviews, review_ids, processed


def save_reviews(
    path: Path,
    submissions: list[openreview.api.Note],
    review_name: str,
    reviews: list[dict[str, Any]],
    processed_submission_ids: set[str],
) -> None:
    """Persist the current snapshot of reviews to disk."""
    payload = {
        "venue_id": VENUE_ID,
        "submission_invitation": SUBMISSION_INVITATION,
        "review_name": review_name,
        "generated_at": utc_now_iso(),
        "submission_count": len(submissions),
        "review_count": len(reviews),
        "processed_submission_ids": sorted(processed_submission_ids),
        "reviews": reviews,
    }
    tmp_path = path.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True, separators=(",", ":"))
    tmp_path.replace(path)


def main() -> None:
    client = get_client()
    group = client.get_group(VENUE_ID)
    review_name = (
        (group.content or {}).get("review_name", {}).get("value") or REVIEW_NAME_FALLBACK
    )

    submissions = client.get_all_notes(invitation=SUBMISSION_INVITATION)
    submissions = sorted(submissions, key=lambda note: note.number or 0)
    reviews, review_ids, processed_submission_ids = load_existing_reviews(OUTPUT_PATH)

    print(
        f"Found {len(submissions)} submissions. "
        f"Loaded {len(reviews)} reviews from cache."
    )

    for index, submission in enumerate(submissions, start=1):
        if submission.id in processed_submission_ids:
            continue

        if submission.number is None:
            print(f"[{index}/{len(submissions)}] Skipping {submission.id}: no number.")
            processed_submission_ids.add(submission.id)
            save_reviews(OUTPUT_PATH, submissions, review_name, reviews, processed_submission_ids)
            continue

        invitation = f"{VENUE_ID}/Submission{submission.number}/-/{review_name}"
        new_reviews = fetch_notes_with_retry(client, invitation)
        added = 0
        for review in new_reviews:
            record = review.to_json()
            record["submission_id"] = submission.id
            record["submission_number"] = submission.number
            review_id = record.get("id")
            if review_id and review_id not in review_ids:
                review_ids.add(review_id)
                reviews.append(record)
                added += 1

        processed_submission_ids.add(submission.id)
        save_reviews(OUTPUT_PATH, submissions, review_name, reviews, processed_submission_ids)
        print(
            f"[{index}/{len(submissions)}] Submission {submission.number}: "
            f"{added} reviews (total {len(reviews)})."
        )

    save_reviews(OUTPUT_PATH, submissions, review_name, reviews, processed_submission_ids)
    print(f"Saved {len(reviews)} reviews to {OUTPUT_PATH}.")


if __name__ == "__main__":
    main()
