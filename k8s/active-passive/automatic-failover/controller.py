
import csv
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException

NAMESPACE = os.getenv("NAMESPACE", "ecommerce")
SERVICE_NAME = os.getenv("SERVICE_NAME", "gateway")
REGION_A = os.getenv("REGION_A", "region-a")
REGION_B = os.getenv("REGION_B", "region-b")

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "3"))
FAILURE_THRESHOLD = int(os.getenv("FAILURE_THRESHOLD", "3"))
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "2"))
LOG_PATH = os.getenv("LOG_PATH", "/logs/automatic-failover.csv")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("failover-controller")


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def write_event(event, **fields):
    path = Path(LOG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()

    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "timestamp_utc",
                "event",
                "active_region",
                "consecutive_failures",
                "details",
            ],
        )
        if not exists:
            writer.writeheader()

        writer.writerow({
            "timestamp_utc": timestamp(),
            "event": event,
            "active_region": fields.get("active_region", ""),
            "consecutive_failures": fields.get("failures", ""),
            "details": fields.get("details", ""),
        })


def region_pods_ready(core, region):
    pods = core.list_namespaced_pod(
        namespace=NAMESPACE,
        label_selector=f"app=gateway,region={region}",
    ).items

    return any(
        pod.status.phase == "Running"
        and pod.status.conditions
        and any(
            condition.type == "Ready" and condition.status == "True"
            for condition in pod.status.conditions
        )
        for pod in pods
    )


def probe_region(core, region):
    """Check both Kubernetes readiness and the gateway's live endpoint."""
    if not region_pods_ready(core, region):
        return False, "no ready gateway pod"

    pods = core.list_namespaced_pod(
        namespace=NAMESPACE,
        label_selector=f"app=gateway,region={region}",
    ).items

    ready_pod = next(
        pod for pod in pods
        if pod.status.phase == "Running"
        and pod.status.conditions
        and any(
            condition.type == "Ready" and condition.status == "True"
            for condition in pod.status.conditions
        )
    )

    # Use the pod IP directly so this probe does not depend on the
    # Service selector that we may need to change during failover.
    url = f"http://{ready_pod.status.pod_ip}:8000/live"

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        body = response.json()

        if body.get("region") != region:
            return False, f"unexpected region response: {body.get('region')}"

        return True, "live endpoint healthy"
    except (requests.RequestException, ValueError) as exc:
        return False, str(exc)


def main():
    config.load_incluster_config()
    core = client.CoreV1Api()

    failures = 0
    switched = False

    log.info("Monitoring %s in namespace %s", REGION_A, NAMESPACE)
    write_event("controller_started", active_region=REGION_A)

    while True:
        try:
            service = core.read_namespaced_service(SERVICE_NAME, NAMESPACE)
            active_region = service.spec.selector.get("region", "")

            if active_region == REGION_B:
                switched = True
                log.info("Service already selects %s; failback is disabled", REGION_B)
                time.sleep(CHECK_INTERVAL)
                continue

            if active_region != REGION_A:
                log.error("Unexpected Service selector region: %s", active_region)
                write_event(
                    "unexpected_selector",
                    active_region=active_region,
                    details="Controller will not modify an unknown selector",
                )
                time.sleep(CHECK_INTERVAL)
                continue

            healthy, detail = probe_region(core, REGION_A)

            if healthy:
                if failures:
                    write_event(
                        "region_a_recovered_before_switch",
                        active_region=REGION_A,
                        failures=failures,
                        details=detail,
                    )
                failures = 0
                time.sleep(CHECK_INTERVAL)
                continue

            failures += 1
            log.warning(
                "Region A probe failed (%s/%s): %s",
                failures, FAILURE_THRESHOLD, detail,
            )

            write_event(
                "region_a_probe_failed",
                active_region=REGION_A,
                failures=failures,
                details=detail,
            )

            if failures < FAILURE_THRESHOLD:
                time.sleep(CHECK_INTERVAL)
                continue

            write_event(
                "failover_detected",
                active_region=REGION_A,
                failures=failures,
                details="Consecutive failure threshold reached",
            )

            region_b_healthy, region_b_detail = probe_region(core, REGION_B)
            if not region_b_healthy:
                log.error("Region B is not ready; keeping Region A selected")
                write_event(
                    "failover_blocked_region_b_unhealthy",
                    active_region=REGION_A,
                    failures=failures,
                    details=region_b_detail,
                )
                time.sleep(CHECK_INTERVAL)
                continue

            # Re-read the Service immediately before patching to avoid
            # overwriting a selector change made by another operator.
            latest = core.read_namespaced_service(SERVICE_NAME, NAMESPACE)
            if latest.spec.selector.get("region") != REGION_A:
                log.warning("Service selector changed externally; aborting patch")
                write_event(
                    "failover_aborted_selector_changed",
                    active_region=latest.spec.selector.get("region", ""),
                )
                time.sleep(CHECK_INTERVAL)
                continue

            write_event(
                "failover_switch_initiated",
                active_region=REGION_A,
                failures=failures,
                details="Patching gateway Service selector to Region B",
            )

            core.patch_namespaced_service(
                name=SERVICE_NAME,
                namespace=NAMESPACE,
                body={
                    "spec": {
                        "selector": {
                            "app": "gateway",
                            "region": REGION_B,
                        }
                    }
                },
            )

            switched = True
            log.info("Service selector switched to %s", REGION_B)
            write_event(
                "failover_switch_completed",
                active_region=REGION_B,
                failures=failures,
                details="Service selector patch accepted; verify endpoint and client success separately",
            )

            # Do not automatically fail back. Keep monitoring and log
            # that Region B remains selected.
            while switched:
                time.sleep(CHECK_INTERVAL)
                latest = core.read_namespaced_service(SERVICE_NAME, NAMESPACE)
                if latest.spec.selector.get("region") != REGION_B:
                    log.warning("Service no longer selects Region B; stopping controller")
                    write_event(
                        "selector_changed_after_failover",
                        active_region=latest.spec.selector.get("region", ""),
                    )
                    return

        except ApiException as exc:
            log.exception("Kubernetes API error: %s", exc)
            write_event("kubernetes_api_error", details=str(exc))
        except Exception as exc:
            log.exception("Unexpected controller error: %s", exc)
            write_event("controller_error", details=str(exc))

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
