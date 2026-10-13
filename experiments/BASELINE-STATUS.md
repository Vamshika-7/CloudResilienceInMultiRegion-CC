# Experiment 1 baseline status

**Status: blocked before smoke testing; no measurements were collected.**

## Environment inspection

Inspection time: 2026-10-13 (local time, UTC+05:30).

- Git branch: `main`. The worktree already contained modified gateway and
  Kubernetes files and untracked files before experiment changes; those files
  were left untouched.
- Java was present (`24.0.2`). Apache JMeter was not found.
- Python 3.14.3 was available. `pandas` and `matplotlib` were not installed.
  No software or packages were downloaded or installed.
- Both kubeconfig context names were present, but `kubectl get nodes` could not
  connect to either API server (`127.0.0.1:56561` and `127.0.0.1:59845`).
- `docker ps` could not connect to Docker Desktop's Linux engine.
- `http://localhost:8000/live` and `http://localhost:8010/live` both refused
  connection. Their HTTP status and region identities could not be verified.
- Host: 13th Gen Intel Core i5-1335U, 10 cores / 12 logical processors,
  reported CPU load 40%; approximately 0.57–0.77 GB of 7.65 GB memory was free
  in two nearby checks.

## Experimental outcome

No liveness smoke test, business-request smoke test, or full baseline was run.
No JTL files, HTML reports, comparison CSV, or charts exist. No results have
been fabricated. The configured starting workload is 1 user, 1-second
ramp-up, and 10-second duration; the documented smoke duration is 5 seconds.
The 10-user, 10-second ramp-up, 60-second baseline candidate must not be used
until the clusters and endpoints recover, smoke tests succeed, and a fresh
resource check indicates adequate headroom.

The existing safe business workload identified in the application is
`GET /api/products`. The baseline plan can run it separately from gateway-only
`GET /live`; see [README.md](./README.md) for invocation and metric definitions.

The Region B Kubernetes configuration points to the PostgreSQL endpoint on
`k3d-ecommerce-server-0:30432`, in the Region A cluster. This experiment does
not establish independent database resilience: both regions share PostgreSQL.

## Unblock requirements

1. Start/recover both existing clusters and gateways outside this experiment;
   verify node readiness and that each `/live` responds HTTP 200 with its
   correct region. No cluster or deployment changes were made here.
2. Obtain authorization before installing missing software. Official JMeter
   downloads and minimum setup notes are in [README.md](./README.md); analysis
   requires pandas and matplotlib.
3. Recheck host resources, run sequential 1-user smoke tests against both
   regions, validate raw JTL rows, and only then consider the candidate full
   workload.
