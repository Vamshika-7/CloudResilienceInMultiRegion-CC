#!/usr/bin/env python3
"""Simple JMeter CSV analysis script."""

import csv
import statistics
import os
import sys


def parse_csv(filepath):
    """Parse JMeter Summary Report CSV into lists of values."""
    labels = []
    samples = []
    averages = []
    mins = []
    maxs = []
    errors = []
    throughputs = []

    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # skip header
        for row in reader:
            if not row or len(row) < 11:
                continue
            try:
                labels.append(row[0].strip())
                samples.append(int(row[1].strip()))
                averages.append(float(row[2].strip()))
                mins.append(float(row[3].strip()))
                maxs.append(float(row[4].strip()))
                errors.append(float(row[6].strip()) if row[6].strip() else 0.0)
                throughputs.append(float(row[7].strip()))
            except (ValueError, IndexError):
                continue

    return {
        'labels': labels,
        'samples': samples,
        'averages': averages,
        'mins': mins,
        'maxs': maxs,
        'errors': errors,
        'throughputs': throughputs,
    }


def compute_stats(values):
    """Count, mean, median, p95, min, max."""
    if not values:
        return {'count': 0, 'mean': 0.0, 'median': 0.0, 'p95': 0.0, 'min': 0.0, 'max': 0.0}

    sorted_vals = sorted(values)
    count = len(sorted_vals)
    mean_val = statistics.mean(sorted_vals)
    median_val = statistics.median(sorted_vals)

    # p95 nearest-rank
    rank = max(1, min(int(0.95 * count), count))
    p95 = sorted_vals[rank - 1]

    return {
        'count': count,
        'mean': round(mean_val, 2),
        'median': round(median_val, 2),
        'p95': round(p95, 2),
        'min': round(min(sorted_vals), 2),
        'max': round(max(sorted_vals), 2),
    }


def analyze(filepath, compare_filepath=None):
    data = parse_csv(filepath)

    print(f"\n=== JMeter Analysis: {os.path.basename(filepath)} ===\n")

    # Per-label stats (only first label typically in Summary Report)
    for i, label in enumerate(data['labels']):
        print(f"Label: {label}")
        print(f"  Sample Count: {data['samples'][i] if i < len(data['samples']) else 0}")
        print(f"  Average Latency: {data['averages'][i]:.2f} ms")
        print(f"  Min Latency: {data['mins'][i]:.2f} ms")
        print(f"  Max Latency: {data['maxs'][i]:.2f} ms")
        print(f"  Error Rate: {data['errors'][i]:.2f}%")
        print(f"  Throughput: {data['throughputs'][i]:.2f} req/s")
        print()

    # TOTAL / overall stats
    total_samples = sum(data['samples']) if data['samples'] else 0
    total_avg = statistics.mean(data['averages']) if data['averages'] else 0.0
    total_min = min(data['mins']) if data['mins'] else 0.0
    total_max = max(data['maxs']) if data['maxs'] else 0.0
    total_error = statistics.mean(data['errors']) if data['errors'] else 0.0
    total_throughput = statistics.mean(data['throughputs']) if data['throughputs'] else 0.0

    print("=== Overall TOTAL ===")
    print(f"  Total Sample Count: {total_samples}")
    print(f"  Average Latency: {total_avg:.2f} ms")
    print(f"  Min Latency: {total_min:.2f} ms")
    print(f"  Max Latency: {total_max:.2f} ms")
    print(f"  Error Rate: {total_error:.2f}%")
    print(f"  Throughput: {total_throughput:.2f} req/s")

    # Latency additional stats from average latencies
    lat_stats = compute_stats(data['averages']) if data['averages'] else {}
    if lat_stats:
        print(f"  Latency Count: {lat_stats['count']}")
        print(f"  Mean Latency: {lat_stats['mean']:.2f} ms")
        print(f"  Median Latency: {lat_stats['median']:.2f} ms")
        print(f"  P95 Latency: {lat_stats['p95']:.2f} ms")

    # Comparison
    if compare_filepath:
        print(f"\n=== Comparison: {os.path.basename(filepath)} vs {os.path.basename(compare_filepath)} ===")
        cdata = parse_csv(compare_filepath)

        our_total = sum(data['samples']) if data['samples'] else 0
        their_total = sum(cdata['samples']) if cdata['samples'] else 0
        print(f"  Sample Count: ours={our_total}, theirs={their_total}")

        our_error = statistics.mean(data['errors']) if data['errors'] else 0.0
        their_error = statistics.mean(cdata['errors']) if cdata['errors'] else 0.0
        print(f"  Error Rate: ours={our_error:.2f}%, theirs={their_error:.2f}%")
        print(f"  Error Delta: {our_error - their_error:.2f} pp")

        our_throughput = statistics.mean(data['throughputs']) if data['throughputs'] else 0.0
        their_throughput = statistics.mean(cdata['throughputs']) if cdata['throughputs'] else 0.0
        print(f"  Throughput: ours={our_throughput:.2f} req/s, theirs={their_throughput:.2f} req/s")
        print(f"  Throughput Delta: {our_throughput - their_throughput:.2f} req/s")

        # Write comparison CSV
        base = os.path.splitext(os.path.basename(filepath))[0]
        cbase = os.path.splitext(os.path.basename(compare_filepath))[0]
        comp_path = f"{base}_comparison.csv"
        with open(comp_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['Metric', 'Current', 'Previous', 'Delta', 'Change'])
            w.writerow(['Sample Count', our_total, their_total,
                       our_total - their_total,
                       'increase' if our_total > their_total else 'decrease' if our_total < their_total else 'unchanged'])
            w.writerow(['Avg Latency (ms)', round(total_avg, 2), round(their_avg, 2) if 'their_avg' in dir() else 'N/A',
                       round(total_avg - (their_avg if 'their_avg' in dir() else 0), 2),
                       'worse' if (their_avg if 'their_avg' in dir() else 0) > total_avg else 'better'])
        print(f"  Comparison CSV: {comp_path}")

    # Try matplotlib graphs
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        base = os.path.splitext(os.path.basename(filepath))[0]
        chart_dir = f"{base}_charts"
        os.makedirs(chart_dir, exist_ok=True)

        if data['averages']:
            plt.figure(figsize=(8, 4))
            plt.bar(range(len(data['averages'])), data['averages'], color='steelblue')
            plt.xlabel('Sample Index')
            plt.ylabel('Average Latency (ms)')
            plt.title(f'Latency: {os.path.basename(filepath)}')
            plt.tight_layout()
            plt.savefig(f'{chart_dir}/latency.png', dpi=100)
            plt.close()

            plt.figure(figsize=(8, 4))
            plt.bar(range(len(data['throughputs'])), data['throughputs'], color='darkgreen')
            plt.xlabel('Sample Index')
            plt.ylabel('Throughput (req/s)')
            plt.title(f'Throughput: {os.path.basename(filepath)}')
            plt.tight_layout()
            plt.savefig(f'{chart_dir}/throughput.png', dpi=100)
            plt.close()

        print(f"  Charts written to: {chart_dir}/")
    except ImportError:
        print("  (matplotlib not installed; skip graphs)")

    return data


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze JMeter Summary Report CSV')
    parser.add_argument('csv_file', help='Path to JMeter CSV')
    parser.add_argument('--compare', help='Second CSV for comparison')
    args = parser.parse_args()

    if not os.path.isfile(args.csv_file):
        print(f"Error: {args.csv_file} not found", file=sys.stderr)
        sys.exit(1)

    analyze(args.csv_file, args.compare)


if __name__ == '__main__':
    main()