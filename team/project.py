import os
from dataclasses import dataclass, field
from pathlib import Path

from config import cfg


@dataclass
class ProjectSpec:
    name: str
    description: str
    tech_stack: list[str]
    build_timeout_seconds: int = field(default_factory=lambda: cfg.BUILD_TIMEOUT_SECS)
    human_checkpoints: list = field(default_factory=list)  # (5.7) e.g. ["after_prd", "after_architecture"]
    workspace_path: Path = field(init=False)

    def __post_init__(self) -> None:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in self.name).strip("-")
        # 2.6: Resolve to absolute path to prevent CWD-relative misses
        workspace_root = Path(os.environ.get("WORKSPACE_ROOT", cfg.WORKSPACE_ROOT))
        self.workspace_path = (workspace_root / safe_name).resolve()

    def setup_workspace(self) -> None:
        self.workspace_path.mkdir(parents=True, exist_ok=True)

    def tech_stack_str(self) -> str:
        return ", ".join(self.tech_stack)
