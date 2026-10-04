"""
Validation script for docker-compose.yml configuration
Checks:
- Valid YAML syntax
- Presence of all required services
- Correct Dockerfile and context paths
- Environment variable configuration for Docker service names (no localhost)
- Healthcheck presence and configuration
- Dependencies and startup order
- Volume and network declarations
"""

import sys
import os
import yaml

def main():
    compose_path = os.path.join(os.path.dirname(__file__), "..", "docker-compose.yml")
    compose_path = os.path.abspath(compose_path)

    if not os.path.exists(compose_path):
        print(f"ERROR: {compose_path} does not exist.")
        sys.exit(1)

    with open(compose_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print(f"=== Docker Compose Configuration Validation ===")
    print(f"Compose Spec Version: {config.get('version')}")

    services = config.get("services", {})
    required_services = [
        "postgres",
        "product-service",
        "order-service",
        "payment-service",
        "gateway",
        "frontend"
    ]

    for req in required_services:
        if req not in services:
            print(f"FAILED: Service '{req}' is missing.")
            sys.exit(1)
        print(f"Service '{req}': DEFINED")

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    for name, s in services.items():
        print(f"\n--- Checking '{name}' ---")
        
        # Build context
        if "build" in s:
            ctx = s["build"]["context"]
            df = s["build"].get("dockerfile", "Dockerfile")
            full_df = os.path.normpath(os.path.join(repo_root, ctx, df))
            if not os.path.exists(full_df):
                print(f"FAILED: Dockerfile does not exist at {full_df}")
                sys.exit(1)
            print(f"  Dockerfile: OK ({full_df})")
        elif "image" in s:
            print(f"  Base Image: {s['image']}")

        # Healthcheck
        if "healthcheck" not in s:
            print(f"FAILED: Service '{name}' is missing healthcheck")
            sys.exit(1)
        hc = s["healthcheck"]
        print(f"  Healthcheck test: {hc.get('test')}")
        print(f"  Interval: {hc.get('interval')}, Timeout: {hc.get('timeout')}, Retries: {hc.get('retries')}")

        # Depends On
        if "depends_on" in s:
            deps = s["depends_on"]
            dep_keys = deps.keys() if isinstance(deps, dict) else deps
            for d in dep_keys:
                if d not in services:
                    print(f"FAILED: '{name}' depends on unknown service '{d}'")
                    sys.exit(1)
            print(f"  Dependencies: {list(dep_keys)}")

        # Environment inter-service URLs
        env = s.get("environment", {})
        if isinstance(env, dict):
            for k, v in env.items():
                if "URL" in k or "HOST" in k:
                    print(f"  Config {k}: {v}")
                    if "localhost" in str(v).lower():
                        print(f"FAILED: Service {name} has hardcoded localhost in {k}: {v}")
                        sys.exit(1)

        # Networks
        if "networks" in s:
            print(f"  Networks: {s['networks']}")

    # Volumes check
    volumes = config.get("volumes", {})
    if "postgres_data" not in volumes:
        print("FAILED: Named volume 'postgres_data' not declared.")
        sys.exit(1)
    print("\nVolume 'postgres_data': OK")

    # Networks check
    networks = config.get("networks", {})
    if "ecommerce-net" not in networks:
        print("FAILED: Network 'ecommerce-net' not declared.")
        sys.exit(1)
    print("Network 'ecommerce-net': OK")

    print("\n=======================================================")
    print("SUCCESS: ALL DOCKER COMPOSE SPECIFICATIONS ARE VALID!")
    print("=======================================================")

if __name__ == "__main__":
    main()
