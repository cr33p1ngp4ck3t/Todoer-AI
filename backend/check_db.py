"""Check database for tasks and users"""
import os
from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select
from src.models.user import User
from src.models.task import Task

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Connecting to: {DATABASE_URL}...")

engine = create_engine(f"{DATABASE_URL}")

with Session(engine) as session:
    # Check users
    users = session.exec(select(User)).all()
    print(f"\n{len(users)} users found:")
    for user in users:
        print(f"  - {user.username} ({user.email}) - created_at: {user.created_at}")

    # Check tasks
    tasks = session.exec(select(Task)).all()
    print(f"\n{len(tasks)} tasks found:")
    for task in tasks:
        print(f"  - {task.title}")
        print(f"    created_at type: {type(task.created_at)}, value: {task.created_at}")
        print(f"    updated_at type: {type(task.updated_at)}, value: {task.updated_at}")
        try:
            print(f"    created_at.isoformat(): {task.created_at.isoformat()}")
        except Exception as e:
            print(f"    ERROR calling isoformat(): {e}")
