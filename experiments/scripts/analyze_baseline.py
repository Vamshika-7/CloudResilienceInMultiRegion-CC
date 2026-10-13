#!/usr/bin/env python3
"""Summarize regional JMeter CSV/JTL files and produce comparison charts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Missing analysis dependency: "
        f"{exc.name}. Install pandas and matplotlib with "
        "`python -m pip install pandas matplotlib`."
    ) from exc


REQUIRED_COLUMNS = {
    "timeStamp",
    "elapsed",
    "label",
    "responseCode",
    "success",
    "region",
    "workload",
    "endpoint",
    "users",
    "rampUpSec",
    "durationSec",
    "jmeterVersion",
    "javaVersion",
}


def read_result(path: Path, expected_region: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not path.is_file():
        raise ValueError(f"Result file does not exist: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Result file is empty: {path}")

    try:
        data = pd.read_csv(path, dtype=str, on_bad_lines="error")
    except (OSError, pd.errors.ParserError, UnicodeError) as exc:
        raise ValueError(f"Cannot read JMeter CSV/JTL file {path}: {exc}") from exc

    if data.empty:
        raise ValueError(f"Result file contains no sample rows: {path}")
    missing = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing:
        raise ValueError(
            f"Invalid JMeter result {path}; missing columns: {', '.join(missing)}"
        )

    for column in ("timeStamp", "elapsed"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
        if data[column].isna().any():
            raise ValueError(f"Invalid or missing {column} values in {path}")
    if (data["elapsed"] < 0).any():
        raise ValueError(f"Negative response times found in {path}")

    normalized_success = data["success"].str.strip().str.lower()
    if not normalized_success.isin({"true", "false"}).all():
        raise ValueError(f"Invalid or missing success values in {path}")
    data["success"] = normalized_success.eq("true")

    for column in ("label", "region", "workload", "endpoint"):
        if data[column].isna().any() or data[column].str.strip().eq("").any():
            raise ValueError(f"Missing {column} values in {path}")
        if data[column].nunique() != 1:
            raise ValueError(f"Mixed {column} values in one run are not supported: {path}")
    for column in ("jmeterVersion", "javaVersion"):
        if (
            data[column].isna().any()
            or data[column].str.strip().eq("").any()
            or data[column].str.strip().eq("not-recorded").any()
            or data[column].nunique() != 1
        ):
            raise ValueError(f"Missing or mixed {column} metadata in {path}")

    region = data["region"].iloc[0]
    if region != expected_region:
        raise ValueError(
            f"Expected {expected_region} rows in {path}, found region {region!r}"
        )
    if data["label"].iloc[0] != data["workload"].iloc[0]:
        raise ValueError(f"JMeter label and workload metadata differ in {path}")

    numeric_parameters: dict[str, int] = {}
    for column in ("users", "rampUpSec", "durationSec"):
        values = pd.to_numeric(data[column], errors="coerce")
        if values.isna().any() or values.nunique() != 1:
            raise ValueError(f"Invalid or mixed {column} metadata in {path}")
        value = int(values.iloc[0])
        if value < 0 or (column == "users" and value < 1):
            raise ValueError(f"Invalid {column} value in {path}: {value}")
        numeric_parameters[column] = value

    response_code = pd.to_numeric(data["responseCode"], errors="coerce")
    total = len(data)
    success_count = int(data["success"].sum())
    http_error_count = int(
        ((response_code.notna()) & ((response_code < 200) | (response_code >= 300))).sum()
    )
    transport_error_count = int(response_code.isna().sum())
    start_ms = float(data["timeStamp"].min())
    end_ms = float((data["timeStamp"] + data["elapsed"]).max())
    observed_window_seconds = (end_ms - start_ms) / 1000
    if observed_window_seconds <= 0:
        raise ValueError(
            f"Cannot calculate throughput from a zero-length sample window in {path}"
        )

    response_times = data["elapsed"]
    summary: dict[str, Any] = {
        "region": region,
        "workload": data["workload"].iloc[0],
        "endpoint": data["endpoint"].iloc[0],
        "run_start_utc": pd.to_datetime(start_ms, unit="ms", utc=True).isoformat(),
        "run_end_utc": pd.to_datetime(end_ms, unit="ms", utc=True).isoformat(),
        "users": numeric_parameters["users"],
        "ramp_up_seconds": numeric_parameters["rampUpSec"],
        "scheduled_duration_seconds": numeric_parameters["durationSec"],
        "jmeter_version": data["jmeterVersion"].iloc[0],
        "java_version": data["javaVersion"].iloc[0],
        "analysis_python_version": sys.version.split()[0],
        "analysis_pandas_version": pd.__version__,
        "analysis_matplotlib_version": matplotlib.__version__,
        "observed_sample_window_seconds": observed_window_seconds,
        "average_response_time_ms": float(response_times.mean()),
        "median_response_time_ms": float(response_times.quantile(0.50, interpolation="linear")),
        "p90_response_time_ms": float(response_times.quantile(0.90, interpolation="linear")),
        "p95_response_time_ms": float(response_times.quantile(0.95, interpolation="linear")),
        "p99_response_time_ms": float(response_times.quantile(0.99, interpolation="linear")),
        "throughput_requests_per_second": total / observed_window_seconds,
        "http_error_rate_percent": 100 * http_error_count / total,
        "http_error_count": http_error_count,
        "transport_error_count": transport_error_count,
        "successful_request_count": success_count,
        "failed_request_count": total - success_count,
        "total_request_count": total,
        "source_file": str(path),
    }
    return data, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze sequential Region A/Region B JMeter baseline runs."
    )
    parser.add_argument("--region-a-liveness", type=Path, required=True)
    parser.add_argument("--region-b-liveness", type=Path, required=True)
    parser.add_argument(
        "--region-a-business",
        type=Path,
        help="Optional Region A GET /api/products result file.",
    )
    parser.add_argument(
        "--region-b-business",
        type=Path,
        help="Optional Region B GET /api/products result file.",
    )
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--charts-dir", type=Path, required=True)
    args = parser.parse_args()
    if (args.region_a_business is None) != (args.region_b_business is None):
        parser.error("Provide both --region-a-business and --region-b-business, or neither.")
    return args


def make_charts(comparison: pd.DataFrame, charts_dir: Path) -> None:
    charts_dir.mkdir(parents=True, exist_ok=True)
    ordered = comparison.sort_values(["workload", "region"])
    categories = [
        f"{row.workload}\n{row.region}"
        for row in ordered.itertuples(index=False)
    ]
    x_positions = list(range(len(ordered)))
    percentile_columns = (
        ("average_response_time_ms", "Mean"),
        ("median_response_time_ms", "Median"),
        ("p90_response_time_ms", "p90"),
        ("p95_response_time_ms", "p95"),
        ("p99_response_time_ms", "p99"),
    )

    figure, axis = plt.subplots(figsize=(max(9, len(ordered) * 2), 5.5))
    for column, label in percentile_columns:
        axis.plot(
            x_positions,
            ordered[column],
            marker="o",
            linewidth=1.8,
            label=label,
        )
    axis.set_xticks(x_positions, categories)
    axis.set_ylabel("Response time (ms)")
    axis.set_title("Regional baseline response-time percentiles")
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(charts_dir / "response-time-percentiles.png", dpi=160)
    plt.close(figure)

    figure, (throughput_axis, error_axis) = plt.subplots(
        2, 1, figsize=(max(9, len(ordered) * 2), 7), sharex=True
    )
    throughput_axis.bar(
        x_positions, ordered["throughput_requests_per_second"], color="#2878B5"
    )
    throughput_axis.set_ylabel("Requests / second")
    throughput_axis.set_title("Throughput")
    throughput_axis.grid(axis="y", alpha=0.25)
    error_axis.bar(x_positions, ordered["http_error_rate_percent"], color="#C44E52")
    error_axis.set_ylabel("HTTP errors (%)")
    error_axis.set_title("HTTP error rate (non-2xx responses / all samples)")
    error_axis.set_xticks(x_positions, categories)
    error_axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(charts_dir / "throughput-and-error-rate.png", dpi=160)
    plt.close(figure)


def main() -> int:
    args = parse_args()
    inputs = [
        (args.region_a_liveness, "region-a"),
        (args.region_b_liveness, "region-b"),
    ]
    if args.region_a_business is not None:
        inputs.extend(
            [
                (args.region_a_business, "region-a"),
                (args.region_b_business, "region-b"),
            ]
        )

    summaries = []
    workloads_by_region: dict[str, str] = {}
    try:
        for path, expected_region in inputs:
            _, summary = read_result(path, expected_region)
            key = f"{summary['workload']}:{summary['region']}"
            if key in workloads_by_region:
                raise ValueError(
                    f"Multiple result files supplied for {summary['workload']} "
                    f"in {summary['region']}"
                )
            workloads_by_region[key] = str(path)
            summaries.append(summary)

        summary_frame = pd.DataFrame(summaries)
        if summary_frame.groupby("workload")["region"].nunique().ne(2).any():
            raise ValueError("Each workload must have results from both regions.")

        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        summary_frame.to_csv(args.output_csv, index=False)
        make_charts(summary_frame, args.charts_dir)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(f"Analysis failed: {exc}", file=sys.stderr)
        return 2

    print(summary_frame.to_string(index=False))
    print(f"\nComparison CSV: {args.output_csv}")
    print(f"Charts: {args.charts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
