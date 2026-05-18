from pydantic import BaseModel, Field


class BuildRequest(BaseModel):
    name: str = Field(..., description="Short project name, e.g. 'task-manager-api'")
    description: str = Field(..., description="Full project description / requirements")
    tech_stack: list[str] = Field(..., description="Languages and frameworks, e.g. ['Python', 'FastAPI']")


class BuildCreated(BaseModel):
    id: str
    status: str = "running"


class BuildInfo(BaseModel):
    id: str
    status: str
    spec_name: str
    events_count: int
    result: dict = {}
