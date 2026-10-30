import importlib.util
from pathlib import Path


def test_local_credentials_are_random_and_existing_env_is_preserved(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts/init_local_env.py"
    spec = importlib.util.spec_from_file_location("init_local_env", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.init_local_env(tmp_path)
    original = (tmp_path / ".env").read_text()
    values = dict(line.split("=", 1) for line in original.splitlines())
    assert set(values) == {"POSTGRES_PASSWORD", "SECRET_KEY", "SESSION_SECRET"}
    assert len(set(values.values())) == 3
    assert all(len(bytes.fromhex(value)) == 32 for value in values.values())
    assert not module.init_local_env(tmp_path)
    assert (tmp_path / ".env").read_text() == original
