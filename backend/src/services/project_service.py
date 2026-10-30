from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select
from src.models.project import Project, ProjectMember
from src.models.task import Task
from src.models.user import User


class ProjectService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    def role(self, project_id: UUID, session: Session) -> str | None:
        project = session.get(Project, project_id)
        if project is None:
            return None
        if project.owner_id == self.user_id:
            return "owner"
        member = session.exec(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == self.user_id,
                ProjectMember.accepted == True,  # noqa: E712
            )
        ).first()
        return member.role if member else None

    def require_access(
        self,
        project_id: UUID,
        session: Session,
        write: bool = False,
        owner: bool = False,
    ) -> str:
        role = self.role(project_id, session)
        if role is None:
            raise HTTPException(404, "Project not found")
        if (owner and role != "owner") or (write and role == "viewer"):
            raise HTTPException(403, "Project permission denied")
        return role

    def response(
        self, project: Project, session: Session, detail: bool = False
    ) -> dict:
        result = {
            "id": project.id,
            "name": project.name,
            "owner_id": project.owner_id,
            "created_at": project.created_at,
            "role": self.role(project.id, session),
        }
        if detail:
            project_owner = session.get(User, project.owner_id)
            members = [
                {
                    "user_id": project_owner.id,
                    "username": project_owner.username,
                    "email": project_owner.email,
                    "role": "owner",
                    "accepted": True,
                }
            ]
            for member in session.exec(
                select(ProjectMember).where(ProjectMember.project_id == project.id)
            ).all():
                user = session.get(User, member.user_id)
                if user:
                    members.append(
                        {
                            "user_id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "role": member.role,
                            "accepted": member.accepted,
                        }
                    )
            result["members"] = members
        return result

    def remove_member(self, project_id: UUID, user_id: UUID, session: Session):
        self.require_access(project_id, session, owner=True)
        project = session.get(Project, project_id)
        if project.owner_id == user_id:
            raise HTTPException(400, "The project owner cannot be removed")
        member = session.exec(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        ).first()
        if member is None:
            raise HTTPException(404, "Member not found")
        for task in session.exec(
            select(Task).where(
                Task.project_id == project_id, Task.assignee_id == user_id
            )
        ).all():
            task.assignee_id = None
            session.add(task)
        session.delete(member)
        session.commit()
