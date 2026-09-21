import json

from extract_glassdoor import build


def test_complete_counts_and_summaries():
    data = build()
    assert data["overview"]["company"]["overview"]["description"]
    assert data["overview"]["ratings"]["overallRating"]
    assert data["reviews"]["public_default_summary"]["filteredReviewsCount"] >= 190
    assert data["reviews"]["all_reviews_summary"]["filteredReviewsCount"] >= 208
    assert len(data["reviews"]["items"]) == len({row["reviewId"] for row in data["reviews"]["items"]})
    assert len(data["interviews"]["items"]) == 41
    assert data["interviews"]["summary"]["interviewQuestionCount"] == 64
    assert len(data["pay_and_benefits"]["salary_estimates"]) == 103
    assert len(data["pay_and_benefits"]["benefit_categories"]) == 6
    assert sum(len(x["benefits"]) for x in data["pay_and_benefits"]["benefit_categories"]) == 16
    assert len(data["pay_and_benefits"]["general_benefit_reviews"]) == 15
    assert len(data["pay_and_benefits"]["benefit_details"]) == 16
    assert len(data["overview"]["awards"]) == 13


def test_rich_records_are_merged():
    data = build()
    reviews = {row["reviewId"]: row for row in data["reviews"]["items"]}
    assert reviews[89757694]["employerResponses"][0]["id"] == 5603345
    assert reviews[89757694]["url"].endswith("RVW89757694.htm")
    assert "viewsCount" in reviews[89757694]
    interviews = {row["id"]: row for row in data["interviews"]["items"]}
    assert interviews[6800038]["advice"]
    assert any(question.get("answers") for row in interviews.values() for question in row["userQuestions"])
    assert interviews[96711740]["location"]["type"] == "CITY"


def test_output_is_serializable_and_contains_no_auth_material():
    text = json.dumps(build())
    lowered = text.lower()
    for forbidden in ["gd-csrf-token", '"jwt"', '"token"', "websocketdebuggerurl"]:
        assert forbidden not in lowered
