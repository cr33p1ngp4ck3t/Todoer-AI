"""Check CORS configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
print(f"Raw CORS_ORIGINS from .env: '{cors_origins}'")

# Parse the same way main.py does
cors_origins_list = [origin.strip().replace('"', "") for origin in cors_origins.split(",")]

print(f"\nParsed CORS origins ({len(cors_origins_list)} origins):")
for i, origin in enumerate(cors_origins_list, 1):
    print(f"  {i}. '{origin}' (length: {len(origin)})")

print("\nCORS is configured to allow requests from these origins.")
