from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProjectSpec:
    name: str
    description: str
    tech_stack: list[str]
    workspace_path: Path = field(init=False)

    def __post_init__(self) -> None:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in self.name).strip("-")
        self.workspace_path = Path("workspace") / safe_name

    def setup_workspace(self) -> None:
        self.workspace_path.mkdir(parents=True, exist_ok=True)

    def tech_stack_str(self) -> str:
        return ", ".join(self.tech_stack)
