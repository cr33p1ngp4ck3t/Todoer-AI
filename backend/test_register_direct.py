"""Test register directly"""
import os
from dotenv import load_dotenv
from sqlmodel import Session, create_engine
from src.models.user import User
from src.api.auth import get_password_hash

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Connecting to: {DATABASE_URL}...")

engine = create_engine(f"{DATABASE_URL}")

try:
    with Session(engine) as session:
        print("\nCreating user...")
        user = User(
            username="324112345",
            email="dev123@gmail.com",
            hashed_password=get_password_hash("tasty123"),
            is_active=True,
        )
        print(f"User object created: username={user.username}, email={user.email}")

        session.add(user)
        session.commit()
        session.refresh(user)

        print(f"\nUser registered successfully!")
        print(f"  ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Created at: {user.created_at}")
        print(f"  Created at type: {type(user.created_at)}")
        print(f"  created_at.isoformat(): {user.created_at.isoformat()}")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
