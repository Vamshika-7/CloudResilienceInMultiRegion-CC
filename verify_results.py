#!/usr/bin/env python3
"""Verify Active-Active experiment results against raw JMeter JTL data."""

import csv
import os


def analyze_jtl(filepath):
    """Parse a JMeter JTL file and return statistics."""
    samples = []
    errors = 0
    total_elapsed = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append(row)
            if row.get('responseCode', '') != '200':
                errors += 1
            total_elapsed += int(row.get('elapsed', '0'))

    count = len(samples)
    avg = round(total_elapsed / count, 2) if count > 0 else 0.0

    latencies = sorted([int(r['elapsed']) for r in samples])
    min_lat = latencies[0] if latencies else 0
    max_lat = latencies[-1] if latencies else 0
    # P95 nearest-rank method
    p95_idx = int(count * 0.95) - 1
    p95_idx = max(0, min(p95_idx, count - 1))
    p95 = latencies[p95_idx] if count > 0 else 0

    return {
        'count': count,
        'errors': errors,
        'avg_latency_ms': avg,
        'min_latency_ms': min_lat,
        'max_latency_ms': max_lat,
        'p95_latency_ms': p95,
    }


def main():
    base = r'.'
    active_dir = os.path.join(base, 'results', 'active-active')

    a_file = os.path.join(active_dir, 'region-a.jtl')
    b_file = os.path.join(active_dir, 'region-b.jtl')
    summary_file = os.path.join(active_dir, 'active-active-summary.csv')

    print(f"=== Active-Active Experiment Verification ===")
    print()

    # Analyze both JTL files
    a_stats = analyze_jtl(a_file) if os.path.exists(a_file) else None
    b_stats = analyze_jtl(b_file) if os.path.exists(b_file) else None

    print(f"Region A JTL: {a_file}")
    if a_stats:
        print(f"  Samples: {a_stats['count']}")
        print(f"  Errors (non-200): {a_stats['errors']}")
        print(f"  Avg latency: {a_stats['avg_latency_ms']} ms")
        print(f"  Min latency: {a_stats['min_latency_ms']} ms")
        print(f"  Max latency: {a_stats['max_latency_ms']} ms")
        print(f"  P95 latency: {a_stats['p95_latency_ms']} ms")
    print()

    print(f"Region B JTL: {b_file}")
    if b_stats:
        print(f"  Samples: {b_stats['count']}")
        print(f"  Errors (non-200): {b_stats['errors']}")
        print(f"  Avg latency: {b_stats['avg_latency_ms']} ms")
        print(f"  Min latency: {b_stats['min_latency_ms']} ms")
        print(f"  Max latency: {b_stats['max_latency_ms']} ms")
        print(f"  P95 latency: {b_stats['p95_latency_ms']} ms")
    print()

    # Combined stats
    if a_stats and b_stats:
        total = a_stats['count'] + b_stats['count']
        combined_errors = a_stats['errors'] + b_stats['errors']
        combined_avg = round(
            (a_stats['avg_latency_ms'] * a_stats['count'] +
             b_stats['avg_latency_ms'] * b_stats['count']) / total, 2
        ) if total > 0 else 0.0

        print(f"Combined Summary:")
        print(f"  Total samples: {total}")
        print(f"  Total errors: {combined_errors} ({round(combined_errors / total * 100, 1)}%)")
        print(f"  Weighted avg latency: {combined_avg} ms")

    # Verify summary CSV
    print()
    print(f"Summary CSV: {summary_file}")
    if os.path.exists(summary_file):
        with open(summary_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            print(f"  Header: {header}")
            for row in reader:
                print(f"  Row: {row}")

    # Verify against analysis script output
    print()
    print(f"Analysis script output (from earlier run):")
    print(f"  Region A: 1000 samples, 0% errors, avg 11.84 ms, P95 47 ms")
    print(f"  Region B: 1000 samples, 0% errors, avg 101.81 ms, P95 281 ms")
    print(f"  Combined: 2000 samples, 0 errors, weighted avg 56.83 ms")

    # Facts verification
    print()
    print(f"=== Verified Facts ===")
    if a_stats:
        print(f"  Region A sample count: {a_stats['count']} (expected 1000)")
        print(f"  Region A errors: {a_stats['errors']} (expected 0)")
        print(f"  Region A 0% error rate: {'CONFIRMED' if a_stats['errors'] == 0 else 'DISPUTED'}")
    if b_stats:
        print(f"  Region B sample count: {b_stats['count']} (expected 1000)")
        print(f"  Region B errors: {b_stats['errors']} (expected 0)")
        print(f"  Region B 0% error rate: {'CONFIRMED' if b_stats['errors'] == 0 else 'DISPUTED'}")
    if a_stats and b_stats:
        print(f"  Combined 2000 samples: {'CONFIRMED' if a_stats['count'] + b_stats['count'] == 2000 else 'DISPUTED'}")
        print(f"  Combined 0 errors: {'CONFIRMED' if a_stats['errors'] + b_stats['errors'] == 0 else 'DISPUTED'}")


if __name__ == '__main__':
    main()