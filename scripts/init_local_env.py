"""Create local Compose credentials once; preserve existing settings and secrets."""

import secrets
from pathlib import Path


def init_local_env(root: Path) -> bool:
    try:
        with (root / ".env").open("x", encoding="utf-8") as env:
            for key in ("POSTGRES_PASSWORD", "SECRET_KEY", "SESSION_SECRET"):
                env.write(f"{key}={secrets.token_hex(32)}\n")
    except FileExistsError:
        return False
    return True


if __name__ == "__main__":
    created = init_local_env(Path(__file__).resolve().parents[1])
    print("Created .env with local credentials." if created else "Using existing .env.")
