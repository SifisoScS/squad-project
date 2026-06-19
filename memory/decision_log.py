import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from config import cfg

# Module-level lock (1.3): prevents concurrent parallel-developer threads from
# interleaving writes and producing corrupt JSONL lines.
_write_lock = threading.Lock()


class DecisionLog:
    """
    Append-only JSONL log of decisions, outcomes, and failures across all projects.
    Injected into agent system prompts so agents learn from past runs.

    Thread-safe writes (1.3), atomic file replacement (4.5), size-capped rotation (4.5).
    """

    def __init__(self, base_path: str = "memory"):
        self._log_file = Path(base_path) / "decisions.jsonl"
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._max_entries = cfg.DECISION_LOG_MAX
        self._cache: list[dict] | None = None  # ring-buffer cache

    def record(
        self,
        project_name: str,
        decision_type: str,
        decision: str,
        rationale: str,
        outcome: str = "",
    ) -> None:
        """
        Atomically append a decision entry. Thread-safe.

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
        line = json.dumps(entry) + "\n"

        with _write_lock:
            # Atomic append via tmp + replace
            tmp = self._log_file.with_suffix(".jsonl.tmp")
            try:
                existing = self._log_file.read_bytes() if self._log_file.exists() else b""
                tmp.write_bytes(existing + line.encode("utf-8"))
                os.replace(tmp, self._log_file)
            except OSError:
                # Fallback: direct append (non-atomic but better than crashing)
                with self._log_file.open("a", encoding="utf-8") as f:
                    f.write(line)
            finally:
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except OSError:
                        pass

            # Invalidate cache
            self._cache = None

            # Rotate if over cap
            self._rotate_if_needed()

    def _rotate_if_needed(self) -> None:
        """Rename log to .bak and start fresh when entry count exceeds max_entries."""
        if not self._log_file.exists():
            return
        try:
            count = sum(1 for ln in self._log_file.read_text(encoding="utf-8").splitlines() if ln.strip())
            if count > self._max_entries:
                bak = self._log_file.with_suffix(".jsonl.bak")
                os.replace(self._log_file, bak)
                self._cache = None
        except OSError:
            pass

    def recent(self, n: int = 10, project: str | None = None) -> list[dict]:
        """Return the n most recent entries, optionally filtered by project."""
        if not self._log_file.exists():
            return []
        if self._cache is None:
            entries = []
            try:
                for line in self._log_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            except OSError:
                pass
            self._cache = entries
        entries = self._cache
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
