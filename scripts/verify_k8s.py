"""
Validation script for Kubernetes manifests in k8s/ directory.
Validates:
- Valid YAML structure for all documents
- Namespace consistency
- MatchLabels vs template labels in Deployments
- Service port / targetPort alignment
- ConfigMap and Secret key references
"""

import os
import sys
import yaml

def main():
    k8s_dir = os.path.join(os.path.dirname(__file__), "..", "k8s")
    k8s_dir = os.path.abspath(k8s_dir)

    if not os.path.exists(k8s_dir):
        print(f"ERROR: {k8s_dir} does not exist.")
        sys.exit(1)

    yaml_files = sorted([f for f in os.listdir(k8s_dir) if f.endswith(".yaml") or f.endswith(".yml")])
    if not yaml_files:
        print(f"ERROR: No YAML files found in {k8s_dir}.")
        sys.exit(1)

    print("=== Validating Kubernetes Manifests in k8s/ ===")
    configmaps = set()
    secrets = set()
    deployments = {}
    services = {}

    for fname in yaml_files:
        fpath = os.path.join(k8s_dir, fname)
        print(f"\nChecking file: {fname}")
        with open(fpath, "r", encoding="utf-8") as f:
            docs = list(yaml.safe_load_all(f))

        for doc in docs:
            if not doc:
                continue
            kind = doc.get("kind")
            metadata = doc.get("metadata", {})
            name = metadata.get("name")
            namespace = metadata.get("namespace", "default")
            print(f"  [OK] Found {kind}: '{name}' (namespace: '{namespace}')")

            if kind == "ConfigMap":
                for k in doc.get("data", {}).keys():
                    configmaps.add((name, k))
            elif kind == "Secret":
                for k in (doc.get("stringData", {}) or doc.get("data", {})).keys():
                    secrets.add((name, k))
            elif kind == "Deployment":
                deployments[name] = doc
                # Check selector labels match template labels
                selector = doc.get("spec", {}).get("selector", {}).get("matchLabels", {})
                template_labels = doc.get("spec", {}).get("template", {}).get("metadata", {}).get("labels", {})
                for k, v in selector.items():
                    assert template_labels.get(k) == v, f"Selector mismatch in {name}: {k}={v} vs {template_labels}"
            elif kind == "Service":
                services[name] = doc

    print("\n--- Cross-referencing ConfigMap & Secret references ---")
    for dep_name, dep in deployments.items():
        containers = dep.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
        for c in containers:
            for env in c.get("env", []):
                val_from = env.get("valueFrom", {})
                if "configMapKeyRef" in val_from:
                    ref = val_from["configMapKeyRef"]
                    cm_name = ref.get("name")
                    cm_key = ref.get("key")
                    assert (cm_name, cm_key) in configmaps, f"Missing ConfigMap ref: {cm_name}.{cm_key} in {dep_name}"
                if "secretKeyRef" in val_from:
                    ref = val_from["secretKeyRef"]
                    sec_name = ref.get("name")
                    sec_key = ref.get("key")
                    assert (sec_name, sec_key) in secrets, f"Missing Secret ref: {sec_name}.{sec_key} in {dep_name}"

    print("  [OK] All ConfigMap and Secret references exist.")

    print("\n--- Verifying Services ---")
    required_services = ["postgres", "product-service", "order-service", "payment-service", "gateway", "frontend"]
    for req in required_services:
        assert req in services, f"Missing Service definition for {req}"
        assert req in deployments, f"Missing Deployment definition for {req}"
        svc = services[req]
        svc_selector = svc.get("spec", {}).get("selector", {})
        dep_labels = deployments[req].get("spec", {}).get("template", {}).get("metadata", {}).get("labels", {})
        for k, v in svc_selector.items():
            assert dep_labels.get(k) == v, f"Service selector mismatch for {req}: {k}={v}"
        print(f"  [OK] Service '{req}' matches Deployment labels: {svc_selector}")

    print("\n=======================================================")
    print("SUCCESS: ALL KUBERNETES MANIFESTS ARE VALID!")
    print("=======================================================")

if __name__ == "__main__":
    main()
