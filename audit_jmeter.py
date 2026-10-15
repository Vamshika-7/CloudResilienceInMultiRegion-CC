#!/usr/bin/env python3
"""Audit JMeter JTL files and compute corrected metrics."""

import csv
import os


def analyze_jtl(filepath):
    """Analyze a single JTL file and return metrics."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    timestamps = [int(row['timeStamp']) for row in rows]
    elapsed_values = [int(row['elapsed']) for row in rows]
    success_count = sum(1 for row in rows if row['success'] == 'true')
    error_count = len(rows) - success_count
    response_code_dist = {}
    for row in rows:
        rc = row['responseCode']
        response_code_dist[rc] = response_code_dist.get(rc, 0) + 1
    
    span_ms = timestamps[-1] - timestamps[0]
    span_s = span_ms / 1000.0
    count = len(rows)
    
    # Compute percentiles
    sorted_elapsed = sorted(elapsed_values)
    p50 = sorted_elapsed[int(count * 0.50)] if count > 0 else 0
    p90 = sorted_elapsed[int(count * 0.90)] if count > 0 else 0
    p95 = sorted_elapsed[int(count * 0.95)] if count > 0 else 0
    p99 = sorted_elapsed[int(count * 0.99)] if count > 0 else 0
    
    return {
        'file': os.path.basename(filepath),
        'sample_count': count,
        'success_count': success_count,
        'error_count': error_count,
        'error_rate_pct': round(error_count / count * 100, 1) if count > 0 else 0.0,
        'http_status_dist': response_code_dist,
        'min_elapsed_ms': min(elapsed_values),
        'max_elapsed_ms': max(elapsed_values),
        'avg_elapsed_ms': round(sum(elapsed_values) / count, 2) if count > 0 else 0.0,
        'p50_elapsed_ms': p50,
        'p90_elapsed_ms': p90,
        'p95_elapsed_ms': p95,
        'p99_elapsed_ms': p99,
        'timestamp_span_ms': span_ms,
        'timestamp_span_s': round(span_s, 3) if span_s > 0 else 0.0,
        'throughput_samples_per_s': round(count / span_s, 2) if span_s > 0 else 0.0,
    }


def main():
    active_dir = r'results/active-active'
    jtl_files = sorted([os.path.join(active_dir, f) for f in os.listdir(active_dir) if f.endswith('.jtl')])
    
    print(f"=== JMeter JTL Audit ===")
    print(f"Active directory: {active_dir}")
    print(f"JTL files: {[os.path.basename(f) for f in jtl_files]}")
    print()
    
    results = []
    for filepath in jtl_files:
        result = analyze_jtl(filepath)
        results.append(result)
        print(f"--- {result['file']} ---")
        print(f"  Sample count: {result['sample_count']}")
        print(f"  Success: {result['success_count']}, Failed: {result['error_count']}")
        print(f"  Error rate: {result['error_rate_pct']}%")
        print(f"  HTTP status dist: {result['http_status_dist']}")
        print(f"  Min latency: {result['min_elapsed_ms']} ms")
        print(f"  Max latency: {result['max_elapsed_ms']} ms")
        print(f"  Avg latency: {result['avg_elapsed_ms']} ms")
        print(f"  P50: {result['p50_elapsed_ms']} ms, P90: {result['p90_elapsed_ms']} ms")
        print(f"  P95: {result['p95_elapsed_ms']} ms, P99: {result['p99_elapsed_ms']} ms")
        print(f"  Timestamp span: {result['timestamp_span_ms']} ms ({result['timestamp_span_s']} s)")
        print(f"  Throughput: {result['throughput_samples_per_s']} samples/s")
        print()
    
    # Combined summary
    print(f"=== Combined Summary ===")
    total_samples = sum(r['sample_count'] for r in results)
    total_errors = sum(r['error_count'] for r in results)
    combined_error_rate = round(total_errors / total_samples * 100, 1) if total_samples > 0 else 0.0
    
    # Weighted average latency
    weighted_sum = sum(r['avg_elapsed_ms'] * r['sample_count'] for r in results)
    weighted_avg = round(weighted_sum / total_samples, 2) if total_samples > 0 else 0.0
    
    print(f"Total samples across all runs: {total_samples}")
    print(f"Total errors: {total_errors} ({combined_error_rate}%)")
    print(f"Weighted average latency: {weighted_avg} ms")
    print()
    
    # Save audit report
    output_path = os.path.join(active_dir, 'metrics-audit-report.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== JMeter JTL Audit Report ===\n")
        f.write(f"Active directory: {active_dir}\n")
        f.write(f"JTL files: {[os.path.basename(f) for f in jtl_files]}\n")
        f.write("\n")
        for result in results:
            f.write(f"--- {result['file']} ---\n")
            f.write(f"  Sample count: {result['sample_count']}\n")
            f.write(f"  Success: {result['success_count']}, Failed: {result['error_count']}\n")
            f.write(f"  Error rate: {result['error_rate_pct']}%\n")
            f.write(f"  HTTP status dist: {result['http_status_dist']}\n")
            f.write(f"  Min latency: {result['min_elapsed_ms']} ms\n")
            f.write(f"  Max latency: {result['max_elapsed_ms']} ms\n")
            f.write(f"  Avg latency: {result['avg_elapsed_ms']} ms\n")
            f.write(f"  P50: {result['p50_elapsed_ms']} ms, P90: {result['p90_elapsed_ms']} ms\n")
            f.write(f"  P95: {result['p95_elapsed_ms']} ms, P99: {result['p99_elapsed_ms']} ms\n")
            f.write(f"  Timestamp span: {result['timestamp_span_ms']} ms ({result['timestamp_span_s']} s)\n")
            f.write(f"  Throughput: {result['throughput_samples_per_s']} samples/s\n")
            f.write("\n")
        f.write("=== Combined Summary ===\n")
        f.write(f"Total samples across all runs: {total_samples}\n")
        f.write(f"Total errors: {total_errors} ({combined_error_rate}%)\n")
        f.write(f"Weighted average latency: {weighted_avg} ms\n")
    
    print(f"\nAudit report written to: {output_path}")
    
    # Also save CSV summary
    csv_path = os.path.join(active_dir, 'metrics-audit-summary.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['file', 'sample_count', 'success_count', 'error_count',
                         'error_rate_pct', 'min_elapsed_ms', 'max_elapsed_ms',
                         'avg_elapsed_ms', 'p50_elapsed_ms', 'p90_elapsed_ms',
                         'p95_elapsed_ms', 'p99_elapsed_ms', 
                         'timestamp_span_ms', 'timestamp_span_s', 
                         'throughput_samples_per_s'])
        for result in results:
            writer.writerow([
                result['file'],
                result['sample_count'],
                result['success_count'],
                result['error_count'],
                result['error_rate_pct'],
                result['min_elapsed_ms'],
                result['max_elapsed_ms'],
                result['avg_elapsed_ms'],
                result['p50_elapsed_ms'],
                result['p90_elapsed_ms'],
                result['p95_elapsed_ms'],
                result['p99_elapsed_ms'],
                result['timestamp_span_ms'],
                result['timestamp_span_s'],
                result['throughput_samples_per_s'],
            ])
    
    print(f"CSV summary written to: {csv_path}")


if __name__ == '__main__':
    main()