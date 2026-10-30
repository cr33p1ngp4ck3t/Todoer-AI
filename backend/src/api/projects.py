from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_
from sqlmodel import Session, select
from src.api.auth import get_current_user
from src.lib.database import get_session
from src.models.project import Project, ProjectMember
from src.models.user import User
from src.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def nonempty_name(cls, value):
        if not value.strip():
            raise ValueError("Project name cannot be empty")
        return value.strip()


class InvitationCreate(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    role: Literal["editor", "viewer"] = "editor"


@router.get("")
def list_projects(
    user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    accepted_ids = select(ProjectMember.project_id).where(
        ProjectMember.user_id == user.id,
        ProjectMember.accepted == True,  # noqa: E712
    )
    projects = session.exec(
        select(Project)
        .where(or_(Project.owner_id == user.id, Project.id.in_(accepted_ids)))
        .order_by(Project.created_at)
    ).all()
    service = ProjectService(user.id)
    return [service.response(project, session) for project in projects]


@router.post("", status_code=201)
def create_project(
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    project = Project(name=payload.name, owner_id=user.id)
    session.add(project)
    session.commit()
    session.refresh(project)
    return ProjectService(user.id).response(project, session, detail=True)


@router.get("/invitations")
def list_invitations(
    user: User = Depends(get_current_user), session: Session = Depends(get_session)
):
    invitations = session.exec(
        select(ProjectMember).where(
            ProjectMember.user_id == user.id,
            ProjectMember.accepted == False,  # noqa: E712
        )
    ).all()
    return [
        {
            "id": invite.id,
            "project_id": invite.project_id,
            "project_name": session.get(Project, invite.project_id).name,
            "role": invite.role,
        }
        for invite in invitations
    ]


@router.post("/invitations/{invitation_id}/accept")
def accept_invitation(
    invitation_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    invite = session.get(ProjectMember, invitation_id)
    if invite is None or invite.user_id != user.id:
        raise HTTPException(404, "Invitation not found")
    invite.accepted = True
    session.add(invite)
    session.commit()
    return ProjectService(user.id).response(
        session.get(Project, invite.project_id), session, detail=True
    )


@router.get("/{project_id}")
def get_project(
    project_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = ProjectService(user.id)
    service.require_access(project_id, session)
    return service.response(session.get(Project, project_id), session, detail=True)


@router.post("/{project_id}/invitations", status_code=201)
def invite_member(
    project_id: UUID,
    payload: InvitationCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    service = ProjectService(user.id)
    service.require_access(project_id, session, owner=True)
    email = payload.email.strip()
    invited = session.exec(
        select(User).where(User.email == email, User.is_active.is_(True))
    ).first()
    if invited is None:
        matches = session.exec(
            select(User)
            .where(func.lower(User.email) == email.lower(), User.is_active.is_(True))
            .limit(2)
        ).all()
        if len(matches) > 1:
            raise HTTPException(
                400, "Email is ambiguous; use the account's exact email"
            )
        invited = matches[0] if matches else None
    if invited is None:
        raise HTTPException(400, "Invite an existing registered user's email")
    if invited.id == user.id:
        raise HTTPException(400, "The owner is already a member")
    previous = session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == invited.id
        )
    ).first()
    if previous:
        raise HTTPException(409, "This user is already invited or a member")
    invite = ProjectMember(project_id=project_id, user_id=invited.id, role=payload.role)
    session.add(invite)
    session.commit()
    return {
        "id": invite.id,
        "project_id": project_id,
        "user_id": invited.id,
        "role": invite.role,
        "accepted": False,
    }


@router.delete("/{project_id}/members/{user_id}", status_code=204)
def remove_member(
    project_id: UUID,
    user_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    ProjectService(user.id).remove_member(project_id, user_id, session)
