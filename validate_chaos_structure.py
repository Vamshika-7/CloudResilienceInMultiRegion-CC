from pathlib import Path
import yaml

folder = Path("k8s")
files = [
    "network-delay.yaml",
    "network-jitter.yaml",
    "network-packet-loss.yaml",
    "network-bandwidth.yaml",
    "network-partition.yaml",
    "network-corruption.yaml",
]

for name in files:
    with (folder / name).open(encoding="utf-8-sig") as f:
        doc = yaml.safe_load(f)

    errors = []
    if doc.get("apiVersion") != "chaos-mesh.org/v1alpha1":
        errors.append("unexpected apiVersion")
    if doc.get("kind") != "NetworkChaos":
        errors.append("kind must be NetworkChaos")

    metadata = doc.get("metadata") or {}
    spec = doc.get("spec") or {}
    selector = spec.get("selector") or {}

    if not metadata.get("name"):
        errors.append("missing metadata.name")
    if not metadata.get("namespace"):
        errors.append("missing metadata.namespace")
    if not spec.get("duration"):
        errors.append("missing spec.duration")
    if not selector.get("namespaces"):
        errors.append("missing selector.namespaces")
    if not selector.get("labelSelectors"):
        errors.append("missing selector.labelSelectors")

    action = spec.get("action")
    if action not in {"delay", "loss", "bandwidth", "partition", "corrupt"}:
        errors.append(f"unexpected action: {action}")

    if errors:
        print(f"CHECK FAILED: {name}: " + "; ".join(errors))
    else:
        print(f"STRUCTURE OK: {name} (action={action})")
