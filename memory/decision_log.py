import json
from datetime import datetime, timezone
from pathlib import Path


class DecisionLog:
    """
    Append-only JSONL log of decisions, outcomes, and failures across all projects.
    Injected into agent system prompts so agents learn from past runs.
    """

    def __init__(self, base_path: str = "memory"):
        self._log_file = Path(base_path) / "decisions.jsonl"
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        project_name: str,
        decision_type: str,
        decision: str,
        rationale: str,
        outcome: str = "",
    ) -> None:
        """
        Record a decision or outcome to the log.

        decision_type: "tech_choice" | "pattern" | "failure" | "success" | "rejection" | "outcome"
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": project_name,
            "type": decision_type,
            "decision": decision,
            "rationale": rationale,
            "outcome": outcome,
        }
        with self._log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def recent(self, n: int = 10, project: str | None = None) -> list[dict]:
        """Return the n most recent entries, optionally filtered by project."""
        if not self._log_file.exists():
            return []
        entries = []
        with self._log_file.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        if project:
            entries = [e for e in entries if e.get("project") == project]
        return entries[-n:]

    def context_block(self, n: int = 8) -> str:
        """
        Format recent decisions as a memory block for injection into agent system prompts.
        Returns empty string if no history exists yet.
        """
        entries = self.recent(n)
        if not entries:
            return ""
        lines = ["## Cross-Project Memory (Recent Decisions)\n"]
        for e in entries:
            outcome_str = f" → {e['outcome']}" if e.get("outcome") else ""
            lines.append(f"- [{e['type'].upper()}] {e['project']}: {e['decision']}{outcome_str}")
            rationale = e.get("rationale", "")
            if rationale and len(rationale) < 200:
                lines.append(f"  Rationale: {rationale}")
        return "\n".join(lines)
