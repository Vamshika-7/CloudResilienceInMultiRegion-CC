
import csv
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

URL = os.getenv("TARGET_URL", "http://gateway:8000/live")
OUTPUT = os.getenv("OUTPUT_CSV", "/tmp/request-monitor.csv")
INTERVAL = float(os.getenv("INTERVAL_SECONDS", "0.5"))
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "2"))

start = time.monotonic()
print(f"Monitoring {URL}")
print(f"Writing request results to {OUTPUT}")
print("Press Ctrl+C to stop.")

with open(OUTPUT, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow([
        "time_utc",
        "elapsed_seconds",
        "http_status",
        "responding_region",
        "latency_ms",
    ])
    file.flush()

    try:
        while True:
            request_start = time.monotonic()
            timestamp = datetime.now(timezone.utc).isoformat()
            status = ""
            region = ""
            request = urllib.request.Request(URL, method="GET")

            try:
                with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                    status = response.status
                    body = json.loads(response.read().decode("utf-8"))
                    region = body.get("region", "")
            except urllib.error.HTTPError as exc:
                status = exc.code
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                status = 0
                print(f"Request failed: {exc}")

            latency_ms = (time.monotonic() - request_start) * 1000
            elapsed = time.monotonic() - start

            writer.writerow([
                timestamp,
                f"{elapsed:.3f}",
                status,
                region,
                f"{latency_ms:.2f}",
            ])
            file.flush()

            print(
                f"t={elapsed:.3f}s status={status} "
                f"region={region or '-'} latency={latency_ms:.2f}ms"
            )

            remaining = INTERVAL - (time.monotonic() - request_start)
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        print("\nRequest monitoring stopped.")
