import sys
import traceback
from sqlmodel import Session, select
from src.models.user import User
from src.services.task_service import TaskService
from src.main import get_session

try:
    print("Testing /tasks endpoint logic...")

    # Get a session
    with get_session() as session:
        # Get or create dev user
        dev_user = session.exec(select(User).where(User.username == "dev_user")).first()
        if not dev_user:
            print("No dev user found - creating one")
            from src.api.auth import get_password_hash
            dev_user = User(
                username="dev_user",
                email="dev@example.com",
                hashed_password=get_password_hash("dev123"),
                is_active=True,
            )
            session.add(dev_user)
            session.commit()
            session.refresh(dev_user)

        print(f"User: {dev_user.username} ({dev_user.id})")

        # Create service
        service = TaskService(user_id=dev_user.id)

        # Get all tasks
        tasks = service.get_all(
            session=session,
            search=None,
            status=None,
            priority=None,
            sort_by="created_at",
        )

        print(f"Found {len(tasks)} tasks")

        # Try to format a task response (this is where the error might be)
        for t in tasks:
            print(f"Task {t.id}: {t.title}")
            print(f"  created_at type: {type(t.created_at)}")
            print(f"  created_at value: {t.created_at}")
            print(f"  updated_at type: {type(t.updated_at)}")
            print(f"  updated_at value: {t.updated_at}")
            if hasattr(t.created_at, 'isoformat'):
                print(f"  created_at.isoformat(): {t.created_at.isoformat()}")
            else:
                print(f"  ERROR: created_at does not have isoformat method!")

        print("SUCCESS: No error occurred")

except Exception as e:
    print(f"ERROR: {e}")
    print(f"Type: {type(e)}")
    traceback.print_exc()
    sys.exit(1)
