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
    path = folder / name
    try:
        with path.open(encoding="utf-8-sig") as f:
            docs = list(yaml.safe_load_all(f))

        if len(docs) != 1 or not isinstance(docs[0], dict):
            print(f"INVALID: {name} - expected one YAML object")
        else:
            print(f"YAML syntax OK: {name}")

    except Exception as e:
        print(f"INVALID: {name} - {e}")
