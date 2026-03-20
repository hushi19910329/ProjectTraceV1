from pydantic import BaseModel, Field, field_validator


class ProjectNodeBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    sequence: int = Field(default=1, ge=1)
    status: str = "not_started"
    owner_id: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    output_summary: str = ""

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()


class ProjectNodeCreate(ProjectNodeBase):
    pass


class ProjectCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    status: str = "not_started"
    priority: str = "medium"
    project_type: str = "work"
    owner_id: int
    start_date: str | None = None
    end_date: str | None = None
    goal: str = ""
    tags: list[str] = Field(default_factory=list)
    member_ids: list[int] = Field(default_factory=list)
    nodes: list[ProjectNodeCreate] = Field(default_factory=list)

    @field_validator("code", "name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class ProjectMemberPayload(BaseModel):
    user_id: int
    role: str = "member"


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    project_type: str | None = None
    owner_id: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    goal: str | None = None
    tags: list[str] | None = None
    member_ids: list[int] | None = None


class TaskCreate(BaseModel):
    node_id: int | None = None
    parent_task_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    task_type: str = "development"
    status: str = "todo"
    priority: str = "medium"
    tags: list[str] = Field(default_factory=list)
    assignee_id: int | None = None
    collaborator_ids: list[int] = Field(default_factory=list)
    watcher_ids: list[int] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    estimated_hours: int = Field(default=0, ge=0)
    actual_hours: int = Field(default=0, ge=0)
    progress: int = Field(default=0, ge=0, le=100)
    acceptance_criteria: str = ""

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        return value.strip()


class TaskUpdate(BaseModel):
    node_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    task_type: str | None = None
    status: str | None = None
    priority: str | None = None
    tags: list[str] | None = None
    assignee_id: int | None = None
    collaborator_ids: list[int] | None = None
    watcher_ids: list[int] | None = None
    start_date: str | None = None
    end_date: str | None = None
    estimated_hours: int | None = Field(default=None, ge=0)
    actual_hours: int | None = Field(default=None, ge=0)
    progress: int | None = Field(default=None, ge=0, le=100)
    acceptance_criteria: str | None = None


class TaskAbandonPayload(BaseModel):
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    mentioned_user_ids: list[int] = Field(default_factory=list)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        return value.strip()


class ReminderCreate(BaseModel):
    user_ids: list[int] = Field(min_length=1)
    content: str = Field(min_length=1, max_length=500)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        return value.strip()


class TaskStatusUpdateCreate(BaseModel):
    status: str
    progress: int = Field(ge=0, le=100)
    actual_hours: int = Field(default=0, ge=0)
    content: str = Field(min_length=1, max_length=2000)
    assignee_id: int | None = None

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        return value.strip()
