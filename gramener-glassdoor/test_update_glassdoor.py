import json
from pathlib import Path

import update_glassdoor


def test_task_plan_is_stable_and_covers_all_capture_pages():
    tasks = update_glassdoor.task_names()
    assert tasks[:2] == ["overview", "pay-benefits"]
    assert tasks[-1] == "interviews-9"
    assert len(tasks) == 49


def test_atomic_json_replaces_complete_file(tmp_path: Path):
    path = tmp_path / "nested" / "data.json"
    update_glassdoor.atomic_json(path, {"ok": True})
    assert json.loads(path.read_text()) == {"ok": True}
    assert not list(path.parent.glob(".*"))
