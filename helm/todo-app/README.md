# Helm policy checks

CI renders this chart with Helm v3.17.3 and scans the rendered Kubernetes objects
with **kube-score v1.19.0**, alongside kubeconform v0.7.0 schema validation.

The severity gate is kube-score's default: **Critical (grade 1) findings fail CI**
with a nonzero exit code. Critical is kube-score's highest severity and is the
high-severity gate for this repository. Warning (grade 5) findings are printed
without failing; optional checks are not enabled. No broad checks are skipped.
Schema errors and scanner execution errors also fail the infrastructure job.

Reproduce the policy check:

```sh
helm template todo helm/todo-app > /tmp/todo-manifests.yaml
docker run --rm -v /tmp:/manifests:ro zegl/kube-score:v1.19.0 score /manifests/todo-manifests.yaml
```

This step scans the Helm-rendered application; the standalone experimental
manifests in `k8s/` retain their separate schema check.

The defaults use versioned image tags and Always pull policy. Set image repositories
and tags to releases you have actually published before deploying. Pods use UID/GID
10001 and read-only root filesystems; bounded temporary/cache volumes remain writable.
CPU, memory, and ephemeral storage budgets also apply to the migration container.
Ingress policies allow only each application's listening port; they allow any source
and leave egress unrestricted so external databases, LLMs, OAuth, and Dapr remain
reachable. Restrict sources and egress for your cluster's topology. Policies require
a supporting CNI. PodDisruptionBudgets permit at most one unavailable replica.
