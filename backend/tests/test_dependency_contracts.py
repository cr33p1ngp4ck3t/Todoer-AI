"""Deployment manifests must use the same compatible dependency graph as CI."""

import re
import tomllib
from pathlib import Path

from packaging.specifiers import SpecifierSet

ROOT = Path(__file__).resolve().parents[2]


def test_runtime_requirements_match_locked_versions():
    lock = tomllib.loads((ROOT / "backend/uv.lock").read_text())
    locked = {package["name"]: package["version"] for package in lock["package"]}
    pins = dict(
        re.findall(
            r"^([\w-]+)==([^\s\\]+)",
            (ROOT / "backend/requirements.txt").read_text(),
            re.MULTILINE,
        )
    )
    assert pins
    assert {name: locked[name] for name in pins} == pins


def test_passlib_bcrypt_compatibility_remains_pinned():
    project = tomllib.loads((ROOT / "backend/pyproject.toml").read_text())
    constraint = next(
        value.removeprefix("bcrypt")
        for value in project["project"]["dependencies"]
        if value.startswith("bcrypt")
    )
    supported = SpecifierSet(constraint)
    assert "4.0.1" in supported
    assert "4.1.0" not in supported
    assert "5.0.0" not in supported


def test_python_image_upgrade_cannot_leave_old_package_copy_paths():
    dockerfile = (ROOT / "backend/Dockerfile").read_text()
    images = re.findall(r"^FROM python:([\d.]+)-slim", dockerfile, re.MULTILINE)
    assert len(images) == 2 and images[0] == images[1]
    paths = re.findall(r"/usr/local/lib/python([\d.]+)/site-packages", dockerfile)
    assert all(version == images[0] for version in paths)
    assert "COPY --from=builder /usr/local /usr/local" in dockerfile or paths
