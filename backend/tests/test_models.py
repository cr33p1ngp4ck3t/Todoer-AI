"""Persistence and relationship contracts for the current task data model."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from src.models.task import Tag, Task
from src.models.user import User


def test_task_model_creation(db_session, test_user):
    task = Task(
        owner_id=test_user.id,
        title="Test Task",
        description="Test Description",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.id is not None
    assert task.title == "Test Task"
    assert task.description == "Test Description"
    assert task.status == "pending"
    assert task.priority == "medium"
    assert task.owner.id == test_user.id


def test_tag_model_creation(db_session, task_service):
    task = task_service.create(db_session, title="Tagged task")
    tag = Tag(task_id=task.id, name="work")
    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)

    assert tag.id is not None
    assert tag.name == "work"
    assert tag.task_id == task.id
    assert tag.task.id == task.id


def test_task_tag_association(db_session, test_user):
    task = Task(owner_id=test_user.id, title="Test Task")
    task.tags = [Tag(name="work"), Tag(name="personal")]
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert {tag.name for tag in task.tags} == {"work", "personal"}
    assert all(tag.task_id == task.id for tag in task.tags)


def test_user_model_creation(db_session):
    user = User(
        username="model-user",
        email="user@example.com",
        hashed_password="hashed_pass",
    )
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.username == "model-user"
    assert user.email == "user@example.com"
    assert user.is_active is True


@pytest.mark.parametrize(
    "username,email",
    [("another-user", "tester@example.com"), ("tester", "another@example.com")],
)
def test_user_identity_unique(db_session, test_user, username, email):
    db_session.add(User(username=username, email=email, hashed_password="hashed"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    assert db_session.exec(select(User)).all() == [test_user]
