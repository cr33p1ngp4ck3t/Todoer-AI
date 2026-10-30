"""Application pod policies must match their image users and prevent escalation."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "component,path,document,container_count",
    [
        ("backend", "k8s/backend-deployment.yaml", 0, 1),
        ("frontend", "k8s/frontend-deployment.yaml", 0, 1),
        ("backend", "helm/todo-app/templates/deployment.yaml", 0, 2),
        ("frontend", "helm/todo-app/templates/deployment.yaml", 1, 1),
    ],
)
def test_application_pod_security_matches_image_user(
    component, path, document, container_count
):
    # Policy mappings use YAML's JSON syntax so these checks need no YAML dependency.
    workload = (ROOT / path).read_text().split("\n---\n")[document]
    policies = [
        json.loads(value)
        for value in re.findall(
            r"^\s*securityContext: (\{.*\})$", workload, re.MULTILINE
        )
    ]
    assert len(policies) == 1 + container_count
    pod, *containers = policies
    image_definition = (ROOT / component / "Dockerfile").read_text()
    uid = int(re.search(r"useradd.*?-u (\d+)", image_definition).group(1))
    assert pod["runAsUser"] == uid > 0
    assert pod["runAsNonRoot"] is True
    assert pod["seccompProfile"]["type"] == "RuntimeDefault"
    for container in containers:
        assert container["allowPrivilegeEscalation"] is False
        assert container["capabilities"]["drop"] == ["ALL"]
        assert not container.get("privileged", False)
        assert container.get("runAsUser", uid) == uid
