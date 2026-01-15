"""Run Alembic migration with DATABASE_URL from .env"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Set DATABASE_URL environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Using DATABASE_URL: {DATABASE_URL[:50]}...")

# Now run alembic upgrade
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=os.path.dirname(__file__),
    capture_output=True,
    text=True,
)

print(result.stdout)
if result.stderr:
    print(result.stderr)

sys.exit(result.returncode)
