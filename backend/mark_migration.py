"""Mark migration as applied"""
import os
from dotenv import load_dotenv
from alembic.config import Config
from alembic import command

# Load .env
load_dotenv()

# Configure alembic
cfg = Config("alembic.ini")

# Mark as applied
command.stamp(cfg, "002_add_username")
print("Migration 002_add_username marked as applied")
