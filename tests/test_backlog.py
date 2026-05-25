"""
Self-tests for team.backlog.Backlog (#6).
Tests the task lifecycle, persistence, and atomic writes — no Claude API needed.
"""
import json
import pytest
from pathlib import Path
from team.backlog import Backlog, Task


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def backlog(tmp_path):
    """Fresh Backlog backed by a temp directory."""
    return Backlog(tmp_path)


# ── Task lifecycle ────────────────────────────────────────────────────────────

def test_add_task_returns_todo(backlog):
    task = backlog.add_task("Implement auth", "JWT login endpoint")
    assert task.status == "todo"
    assert task.title == "Implement auth"
    assert task.description == "JWT login endpoint"
    assert task.id  # non-empty ID


def test_pending_includes_new_task(backlog):
    backlog.add_task("A", "desc A")
    backlog.add_task("B", "desc B")
    assert len(backlog.get_pending()) == 2


def test_assign_marks_in_progress(backlog):
    task = backlog.add_task("A", "desc")
    backlog.assign_task(task.id, "Priya Patel")
    assert task.status == "in_progress"
    assert task.assigned_to == "Priya Patel"


def test_complete_removes_from_pending(backlog):
    task = backlog.add_task("A", "desc")
    backlog.complete_task(task.id)
    assert task.status == "done"
    assert backlog.get_pending() == []


def test_all_done_true_when_all_complete(backlog):
    t1 = backlog.add_task("A", "")
    t2 = backlog.add_task("B", "")
    assert not backlog.all_done()
    backlog.complete_task(t1.id)
    assert not backlog.all_done()
    backlog.complete_task(t2.id)
    assert backlog.all_done()


def test_update_task_description(backlog):
    task = backlog.add_task("A", "original")
    backlog.update_task(task.id, description="updated description")
    assert task.description == "updated description"


def test_get_unknown_id_raises(backlog):
    with pytest.raises(KeyError):
        backlog._get("nonexistent-id-xyz")


# ── Persistence ───────────────────────────────────────────────────────────────

def test_tasks_survive_reload(tmp_path):
    """Tasks written by one Backlog instance are readable by a new one."""
    b1 = Backlog(tmp_path)
    b1.add_task("Persist me", "I should survive a reload")
    b1.add_task("Also me", "Me too")

    b2 = Backlog(tmp_path)  # fresh instance, same path
    assert len(b2.get_pending()) == 2
    assert b2.get_pending()[0].title == "Persist me"


def test_completed_status_persists(tmp_path):
    b1 = Backlog(tmp_path)
    task = b1.add_task("Do something", "")
    b1.complete_task(task.id)

    b2 = Backlog(tmp_path)
    assert b2.all_done()
    assert b2.get_pending() == []


def test_backlog_file_is_valid_json(tmp_path):
    b = Backlog(tmp_path)
    b.add_task("X", "Y")
    data = json.loads((tmp_path / "backlog.json").read_text())
    assert isinstance(data, list)
    assert data[0]["title"] == "X"


def test_corrupted_backlog_loads_empty(tmp_path):
    """Corrupt JSON should produce an empty backlog without crashing."""
    (tmp_path / "backlog.json").write_text("NOT VALID JSON", encoding="utf-8")
    b = Backlog(tmp_path)
    assert b.get_pending() == []


# ── Summary ───────────────────────────────────────────────────────────────────

def test_summary_contains_task_titles(backlog):
    backlog.add_task("Build API", "FastAPI backend")
    summary = backlog.summary()
    assert "Build API" in summary
    assert "todo" in summary


def test_summary_shows_counts(backlog):
    t = backlog.add_task("A", "")
    backlog.complete_task(t.id)
    backlog.add_task("B", "")
    summary = backlog.summary()
    assert "1 todo" in summary
    assert "1 done" in summary
