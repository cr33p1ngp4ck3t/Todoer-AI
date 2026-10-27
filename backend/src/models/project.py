from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from .task import utcnow


class Project(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100)
    owner_id: UUID = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)


class ProjectMember(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="project.id", index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    role: str = Field(default="editor")
    accepted: bool = Field(default=False)


class TaskImport(SQLModel, table=True):
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    source_id: UUID = Field(primary_key=True)
