from pydantic import BaseModel, Field


class BuildRequest(BaseModel):
    # 2.4: Input validation constraints
    name: str = Field(
        ...,
        min_length=1,
        max_length=80,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Short project name, e.g. 'task-manager-api'",
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=8000,
        description="Full project description / requirements",
    )
    tech_stack: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Languages and frameworks, e.g. ['Python', 'FastAPI']",
    )
    build_timeout_seconds: int = Field(default=1800, ge=60, le=7200)
    human_checkpoints: list[str] = Field(
        default_factory=list,
        description="Pipeline checkpoints requiring human approval: after_prd, after_architecture, after_build, after_safety",
    )


class BuildCreated(BaseModel):
    id: str
    status: str = "running"


class BuildInfo(BaseModel):
    id: str
    status: str
    spec_name: str
    events_count: int
    result: dict = {}


# 4.3: Skill invocation endpoint model
class SkillInvokeRequest(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=100)
    task: str = Field(..., min_length=1, max_length=4000)


# 5.7: Human-in-the-loop approval
class BuildApproveRequest(BaseModel):
    checkpoint: str = Field(..., description="The checkpoint being approved")
    comment: str = Field(default="", max_length=1000)
