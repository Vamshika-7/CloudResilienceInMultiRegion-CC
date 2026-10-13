# Regional baseline performance experiment

This experiment uses the same JMeter plan for both regions. It makes only `GET`
requests, first to the gateway liveness route and then, as a separate workload,
to the existing read-only product catalog route. No fault injection, writes,
deployment changes, or simultaneous regional runs are part of this baseline.

## Targets and interpretation

| Workload | Region A | Region B | What it measures |
| --- | --- | --- | --- |
| Gateway liveness | `http://localhost:8000/live` | `http://localhost:8010/live` | Gateway response only; no service/database request |
| Product catalog read | `http://localhost:8000/api/products` | `http://localhost:8010/api/products` | Read-only gateway-to-product-service request, including its database read |

`GET /api/products` is implemented by the gateway and product service. It is safe
for repeated reads. Liveness and business-request measurements must be kept
separate; neither should be described as the other's performance.

## Prerequisites and current environment

Java is present. Apache JMeter, pandas, and matplotlib were not found during the
environment inspection. Nothing was downloaded or installed.

- Apache JMeter official downloads: <https://jmeter.apache.org/download_jmeter.cgi>.
  Download and extract a binary distribution, then add its `bin` directory to
  `PATH` (or invoke `jmeter.bat` by its full path). JMeter 5.6.x is suitable for
  this plan; use a supported Java runtime as described in the JMeter
  documentation.
- pandas and matplotlib installation: `python -m pip install pandas matplotlib`
  in the Python environment used to run the analyzer.

Do not install either until authorized. Recheck `java -version`, `jmeter
--version`, and the Python imports after installation.

## Safety gate and workload

Before **each** run, verify both named Kubernetes contexts, confirm the relevant
gateway `/live` returns HTTP 200 with the expected `region`, and check that the
host has adequate free memory and CPU. Do not proceed if either region is
unhealthy or the host is under pressure. At inspection time (2026-10-13), both
Kubernetes APIs and both gateway URLs were unreachable and only about 0.6–0.8
GB of 7.65 GB host memory was free. Therefore no smoke or baseline load test
was run. The 10-user / 10-second ramp / 60-second candidate was not approved
for this machine state.

Capture the exact tool versions once before running; the values are required
JTL metadata:

```powershell
$javaVersion = ((java -version 2>&1 | Select-Object -First 1).ToString() -replace '.*version "([^"]+)".*', '$1')
$jmeterVersion = ((jmeter --version 2>&1 | Select-String 'Version' | Select-Object -First 1).Line -replace '.*Version\s+([^\s]+).*', '$1')
if (-not $javaVersion -or -not $jmeterVersion) { throw "Could not determine Java/JMeter versions" }
```

Once the environment is healthy, start with the small smoke parameters below.
Proceed to the candidate full run only after smoke results validate and a fresh
resource check supports it. Run one region and one workload at a time, then
recheck health/resources before the next run:

- Smoke: 1 virtual user, 1-second ramp-up, 5-second duration.
- Candidate baseline: 10 virtual users, 10-second ramp-up, 60-second duration.

These values are explicit parameters rather than hard-coded plan settings.

## Running in PowerShell

Run from the repository root. Create each report destination only if it does
not already exist; JMeter's `-o` requires a new or empty destination. Results
and generated reports are ignored by Git.

The examples below intentionally run Region A before Region B. They start with
liveness smoke tests, then business smoke tests, then full liveness tests, and
finally full business tests. Stop if health or resource checks fail at any
stage. Use unique output names for reruns; do not overwrite prior raw files.

### Smoke tests

```powershell
New-Item -ItemType Directory -Force experiments\results | Out-Null

jmeter -n -t experiments\jmeter\regional-baseline.jmx `
  -Jregion=region-a -Jworkload="Gateway liveness" `
  -JtargetUrl="http://localhost:8000/live" -Jusers=1 -JrampUpSec=1 -JdurationSec=5 `
  "-JjavaVersion=$javaVersion" "-JjmeterVersion=$jmeterVersion" `
  -Jjmeter.save.saveservice.output_format=csv `
  -Jjmeter.save.saveservice.print_field_names=true `
  -Jjmeter.save.saveservice.timestamp_format=ms `
  -Jjmeter.save.saveservice.response_message=true `
  -Jjmeter.save.saveservice.assertion_results_failure_message=true `
  -Jsample_variables=region,workload,endpoint,users,rampUpSec,durationSec,jmeterVersion,javaVersion `
  -l experiments\results\region-a-liveness-smoke.jtl

jmeter -n -t experiments\jmeter\regional-baseline.jmx `
  -Jregion=region-b -Jworkload="Gateway liveness" `
  -JtargetUrl="http://localhost:8010/live" -Jusers=1 -JrampUpSec=1 -JdurationSec=5 `
  "-JjavaVersion=$javaVersion" "-JjmeterVersion=$jmeterVersion" `
  -Jjmeter.save.saveservice.output_format=csv `
  -Jjmeter.save.saveservice.print_field_names=true `
  -Jjmeter.save.saveservice.timestamp_format=ms `
  -Jjmeter.save.saveservice.response_message=true `
  -Jjmeter.save.saveservice.assertion_results_failure_message=true `
  -Jsample_variables=region,workload,endpoint,users,rampUpSec,durationSec,jmeterVersion,javaVersion `
  -l experiments\results\region-b-liveness-smoke.jtl
```

Inspect both JTL files for nonempty sample rows, the expected region metadata,
HTTP 200 response codes, and successful assertions before continuing. Repeat
the smoke pair for `GET /api/products` using `-Jworkload="Product catalog read"`
and the URLs `http://localhost:8000/api/products` and
`http://localhost:8010/api/products`, with distinct `region-a-products-smoke.jtl`
and `region-b-products-smoke.jtl` output names. Use the same liveness command
options; set the region and target URL for each command as shown in the table
and use the product-catalog workload label and product smoke output filename.

### Full baseline

After successful smoke runs and a fresh resource/health check, repeat the
sequential commands with `-Jusers=10 -JrampUpSec=10 -JdurationSec=60`. Use:

| Run | `-JtargetUrl` | JTL output | HTML report output |
| --- | --- | --- | --- |
| A liveness | `http://localhost:8000/live` | `experiments\results\region-a-liveness-baseline.jtl` | `experiments\reports\region-a-liveness` |
| B liveness | `http://localhost:8010/live` | `experiments\results\region-b-liveness-baseline.jtl` | `experiments\reports\region-b-liveness` |
| A products | `http://localhost:8000/api/products` | `experiments\results\region-a-products-baseline.jtl` | `experiments\reports\region-a-products` |
| B products | `http://localhost:8010/api/products` | `experiments\results\region-b-products-baseline.jtl` | `experiments\reports\region-b-products` |

For each row, use `-Jregion=region-a` or `-Jregion=region-b`,
`-Jworkload="Gateway liveness"` or `-Jworkload="Product catalog read"`, its
table URL/output paths, and the save-service options from the smoke commands.
Set `-Jusers=10 -JrampUpSec=10 -JdurationSec=60`, retain the Java/JMeter version
and JTL metadata options, and add `-e -o <that row's new report directory>` to
generate the HTML report. Do not run the two regions simultaneously. Do not
rerun a command using a JTL file or report directory that already exists.

## Analysis

After all four successful runs, from the repository root run:

```powershell
python experiments\scripts\analyze_baseline.py `
  --region-a-liveness experiments\results\region-a-liveness-baseline.jtl `
  --region-b-liveness experiments\results\region-b-liveness-baseline.jtl `
  --region-a-business experiments\results\region-a-products-baseline.jtl `
  --region-b-business experiments\results\region-b-products-baseline.jtl `
  --output-csv experiments\results\baseline-comparison.csv `
  --charts-dir experiments\charts
```

The analyzer leaves raw JTL files untouched and rejects missing, empty,
malformed, mislabeled, or incomplete result files. It requires JMeter CSV JTL
columns including `timeStamp`, `elapsed`, `label`, `responseCode`, `success`,
and the run-metadata columns configured in the test plan.

### Metric definitions

- Average and median are calculated over each sample's JMeter `elapsed`
  response time in milliseconds. p90, p95, and p99 use pandas linear
  interpolation over the same sample values.
- Throughput is total samples divided by the observed sample window, from the
  earliest sample start (`timeStamp`) to the latest sample completion
  (`timeStamp + elapsed`), in seconds. This is the active sample span, not an
  assumed 60 seconds; setup/teardown gaps outside the first and last sample are
  excluded.
- HTTP error rate is the number of samples with a numeric, non-2xx HTTP status
  divided by total samples. Transport failures without an HTTP status are
  reported separately as `transport_error_count`.
- Successful requests are JMeter `success=true` samples (the response
  assertion requires the configured expected status, 200 by default). Failed
  requests are total samples minus successful samples. This can differ from
  HTTP error count when no HTTP response was received.
- Run timestamps, region, endpoint, workload, user count, ramp-up, scheduled
  duration, JMeter and Java versions, analysis Python/pandas/matplotlib
  versions, and raw source filename are included in the comparison CSV.

JMeter's HTML reports are retained as supplementary run reports; the
comparison CSV and charts are calculated reproducibly from the original JTLs.

## Architecture limitation

This baseline does not test independent database resilience. The Region B
Kubernetes configuration points its application database URL at the PostgreSQL
endpoint on `k3d-ecommerce-server-0:30432`, i.e. the Region A cluster's
PostgreSQL service. Both regions therefore share PostgreSQL.
