import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Task:
    id: str
    title: str
    description: str
    status: str        # "todo" | "in_progress" | "done" | "force_completed"
    assigned_to: str
    created_at: str    # ISO 8601
    depends_on: list   # (2.2) list of task titles that must complete first


_DONE_STATUSES = frozenset({"done", "force_completed"})


class Backlog:
    def __init__(self, project_workspace: Path):
        self._path = project_workspace / "backlog.json"
        self._tasks: list[Task] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._tasks = []
                for t in data:
                    # Handle older serialized tasks that lack depends_on
                    if "depends_on" not in t:
                        t["depends_on"] = []
                    self._tasks.append(Task(**t))
            except (json.JSONDecodeError, TypeError):
                self._tasks = []

    def _save(self) -> None:
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps([asdict(t) for t in self._tasks], indent=2), encoding="utf-8")
        os.replace(tmp, self._path)

    def add_task(self, title: str, description: str, depends_on: list | None = None) -> Task:
        task = Task(
            id=str(uuid.uuid4())[:8],
            title=title,
            description=description,
            status="todo",
            assigned_to="",
            created_at=datetime.now(timezone.utc).isoformat(),
            depends_on=depends_on or [],
        )
        self._tasks.append(task)
        self._save()
        return task

    def assign_task(self, task_id: str, agent_name: str) -> Task:
        task = self._get(task_id)
        task.status = "in_progress"
        task.assigned_to = agent_name
        self._save()
        return task

    def complete_task(self, task_id: str) -> Task:
        task = self._get(task_id)
        task.status = "done"
        self._save()
        return task

    def force_complete_task(self, task_id: str) -> Task:
        """Mark a task force_completed (shipped after max rejections). (1.4)"""
        task = self._get(task_id)
        task.status = "force_completed"
        self._save()
        return task

    def get_pending(self) -> list[Task]:
        return [t for t in self._tasks if t.status == "todo"]

    def get_in_progress(self) -> list[Task]:
        return [t for t in self._tasks if t.status == "in_progress"]

    def all_done(self) -> bool:
        return all(t.status in _DONE_STATUSES for t in self._tasks)

    def summary(self) -> str:
        todo = sum(1 for t in self._tasks if t.status == "todo")
        doing = sum(1 for t in self._tasks if t.status == "in_progress")
        done = sum(1 for t in self._tasks if t.status == "done")
        forced = sum(1 for t in self._tasks if t.status == "force_completed")
        lines = [f"Backlog ({todo} todo, {doing} in_progress, {done} done, {forced} force_completed):"]
        for t in self._tasks:
            assignee = f" ({t.assigned_to})" if t.assigned_to else ""
            lines.append(f"  [{t.status:<16}] #{t.id} — {t.title}{assignee}")
        return "\n".join(lines)

    def update_task(self, task_id: str, **updates) -> Task:
        task = self._get(task_id)
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        self._save()
        return task

    def _get(self, task_id: str) -> Task:
        for t in self._tasks:
            if t.id == task_id:
                return t
        raise KeyError(f"Task {task_id} not found")
