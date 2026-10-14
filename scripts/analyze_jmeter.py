#!/usr/bin/env python3
"""
JMeter Results Analysis Script

Analyzes JMeter CSV output from Summary Report export and generates
summary statistics and comparison graphs.

Usage:
    python scripts/analyze_jmeter.py <csv_file> [--compare <csv_file>]

    csv_file:   Path to a JMeter Summary Report CSV (comma-separated)
    --compare:  Optional second CSV to compare against (e.g., after chaos injection)

Output:
    - Prints summary statistics to stdout
    - Writes a combined comparison CSV to <basename>_comparison.csv
    - Saves PNG graphs to <basename>_charts/ (if matplotlib available)
"""

import sys
import os
import csv
import statistics
import argparse
import matplotlib.pyplot
import numpy


def parse_jmeter_csv(filepath):
    """
    Parse a JMeter Summary Report CSV file.

    Expected columns (in order):
        Label, # Samples, Average, Min, Max, Std. Dev., Error %, \
              Throughput, Received KB/sec, Sent KB/sec, Avg. Bytes

    Returns a dict with sample-level data extracted from the CSV.
    """
    labels = []
    samples = []
    averages = []
    mins = []
    maxs = []
    std_devs = []
    error_pcts = []
    throughputs = []
    received_kb = []
    sent_kb = []
    avg_bytes = []

    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # skip header
        for row in reader:
            if not row or len(row) < 11:
                continue
            try:
                label = row[0].strip()
                num_samples = int(row[1].strip())
                avg = float(row[2].strip())
                mn = float(row[3].strip())
                mx = float(row[4].strip())
                sd = float(row[5].strip()) if row[5].strip() else 0.0
                error = float(row[6].strip()) if row[6].strip() else 0.0
                throughput = float(row[7].strip())
                rcv_kb = float(row[8].strip())
                snt_kb = float(row[9].strip())
                ab = float(row[10].strip())

                labels.append(label)
                samples.append(num_samples)
                averages.append(avg)
                mins.append(mn)
                maxs.append(mx)
                std_devs.append(sd)
                error_pcts.append(error)
                throughputs.append(throughput)
                received_kb.append(rcv_kb)
                sent_kb.append(snt_kb)
                avg_bytes.append(ab)
            except (ValueError, IndexError):
                # Skip malformed rows
                continue

    return {
        'labels': labels,
        'samples': samples,
        'averages': averages,
        'mins': mins,
        'maxs': maxs,
        'std_devs': std_devs,
        'error_pcts': error_pcts,
        'throughputs': throughputs,
        'received_kb': received_kb,
        'sent_kb': sent_kb,
        'avg_bytes': avg_bytes,
    }


def compute_statistics(data_points):
    """
    Compute key statistics from a list of latency/duration values.
    Returns dict with count, mean, median, p95, min, max.
    """
    if not data_points:
        return {
            'count': 0,
            'mean': 0.0,
            'median': 0.0,
            'p95': 0.0,
            'min': 0.0,
            'max': 0.0,
        }

    sorted_points = sorted(data_points)
    count = len(sorted_points)
    mean = statistics.mean(sorted_points)
    median = statistics.median(sorted_points)

    # P95 calculation (nearest-rank method)
    rank = int(0.95 * count)
    rank = max(1, min(rank, count))
    p95 = sorted_points[rank - 1]

    return {
        'count': count,
        'mean': round(mean, 2),
        'median': round(median, 2),
        'p95': round(p95, 2),
        'min': round(min(sorted_points), 2),
        'max': round(max(sorted_points), 2),
    }


def analyze_csv(filepath, compare_filepath=None):
    """
    Analyze a JMeter Summary Report CSV and optionally compare it
    with a second CSV.
    """
    data = parse_jmeter_csv(filepath)

    print(f"\n=== JMeter Analysis: {os.path.basename(filepath)} ===\n")

    # Print per-label statistics
    for i, label in enumerate(data['labels']):
        stats = compute_statistics(data['averages'] if i == 0 else [])
        # Use the per-row data we have
        label_samples = data['samples'][i] if i < len(data['samples']) else 0
        label_avg = data['averages'][i] if i < len(data['averages']) else 0.0
        label_min = data['mins'][i] if i < len(data['mins']) else 0.0
        label_max = data['maxs'][i] if i < len(data['maxs']) else 0.0
        label_error = data['error_pcts'][i] if i < len(data['error_pcts']) else 0.0
        label_throughput = data['throughputs'][i] if i < len(data['throughputs']) else 0.0

        print(f"Label: {label}")
        print(f"  Sample Count: {label_samples}")
        print(f"  Average Latency: {label_avg:.2f} ms")
        print(f"  Min Latency: {label_min:.2f} ms")
        print(f"  Max Latency: {label_max:.2f} ms")
        print(f"  Error Rate: {label_error:.2f}%")
        print(f"  Throughput: {label_throughput:.2f} req/s")
        print()

    # Overall TOTAL row statistics
    print("=== Overall TOTAL ===")
    total_samples = sum(data['samples']) if data['samples'] else 0
    total_avg = statistics.mean(data['averages']) if data['averages'] else 0.0
    total_min = min(data['mins']) if data['mins'] else 0.0
    total_max = max(data['maxs']) if data['maxs'] else 0.0
    total_error = statistics.mean(data['error_pcts']) if data['error_pcts'] else 0.0
    total_throughput = statistics.mean(data['throughputs']) if data['throughputs'] else 0.0

    print(f"  Total Sample Count: {total_samples}")
    print(f"  Average Latency: {total_avg:.2f} ms")
    print(f"  Min Latency: {total_min:.2f} ms")
    print(f"  Max Latency: {total_max:.2f} ms")
    print(f"  Error Rate: {total_error:.2f}%")
    print(f"  Throughput: {total_throughput:.2f} req/s")

    # Compute additional stats from average latencies
    latencies = data['averages'] if data['averages'] else []
    if latencies:
        lat_stats = compute_statistics(latencies)
        print(f"  Latency Count: {lat_stats['count']}")
        print(f"  Mean Latency: {lat_stats['mean']:.2f} ms")
        print(f"  Median Latency: {lat_stats['median']:.2f} ms")
        print(f"  P95 Latency: {lat_stats['p95']:.2f} ms")

    # Comparison if second file provided
    if compare_filepath:
        print(f"\n=== Comparison: {os.path.basename(filepath)} vs {os.path.basename(compare_filepath)} ===")
        compare_data = parse_jmeter_csv(compare_filepath)

        # Compare TOTAL rows
        our_total = sum(data['samples']) if data['samples'] else 0
        their_total = sum(compare_data['samples']) if compare_data['samples'] else 0

        print(f"  Sample Count: ours={our_total}, theirs={their_total}")
        print(f"  Ratio: {our_total/their_total:.2f}x" if their_total > 0 else "  Ratio: N/A")

        # Compare error rates
        our_error = statistics.mean(data['error_pcts']) if data['error_pcts'] else 0.0
        their_error = statistics.mean(compare_data['error_pcts']) if compare_data['error_pcts'] else 0.0
        print(f"  Error Rate: ours={our_error:.2f}%, theirs={their_error:.2f}%")
        print(f"  Error Delta: {our_error - their_error:.2f} percentage points")

        # Compare throughputs
        our_throughput = statistics.mean(data['throughputs']) if data['throughputs'] else 0.0
        their_throughput = statistics.mean(compare_data['throughputs']) if compare_data['throughputs'] else 0.0
        print(f"  Throughput: ours={our_throughput:.2f} req/s, theirs={their_throughput:.2f} req/s")
        print(f"  Throughput Delta: {our_throughput - their_throughput:.2f} req/s")

        # Generate comparison CSV
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        compare_base = os.path.splitext(os.path.basename(compare_filepath))[0]
        comparison_csv_path = f"{base_name}_comparison.csv"

        with open(comparison_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Current', 'Previous', 'Delta', 'Change'])
            writer.writerow(['Sample Count', our_total, their_total,
                           our_total - their_total,
                           'increase' if our_total > their_total else 'decrease' if our_total < their_total else 'unchanged'])
            writer.writerow(['Average Latency (ms)', round(total_avg, 2), round(their_avg, 2) if 'their_avg' in dir() else 'N/A',
                           round(total_avg - (their_avg if 'their_avg' in dir() else 0), 2),
                           'worse' if (their_avg if 'their_avg' in dir() else 0) > total_avg else 'better'])
            writer.writerow(['P95 Latency (ms)', lat_stats['p95'], 'N/A', 'N/A', 'N/A'])
            writer.writerow(['Error Rate (%)', round(total_error, 2), 'N/A', 'N/A', 'N/A'])
            writer.writerow(['Throughput (req/s)', round(total_throughput, 2), 'N/A', 'N/A', 'N/A'])

        print(f"\nComparison CSV written to: {comparison_csv_path}")

    # Try to generate graphs if matplotlib is available
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        base_name = os.path.splitext(os.path.basename(filepath))[0]
        chart_dir = f"{base_name}_charts"
        os.makedirs(chart_dir, exist_ok=True)

        # Latency distribution comparison
        if data['averages']:
            plt.figure(figsize=(10, 6))
            plt.bar(range(len(data['averages'])), data['averages'], color='steelblue')
            plt.xlabel('Request Label/Index')
            plt.ylabel('Average Latency (ms)')
            plt.title(f'Latency Analysis: {os.path.basename(filepath)}')
            plt.tight_layout()
            plt.savefig(f'{chart_dir}/latency_bar.png', dpi=150)
            plt.close()

            # Throughput bar chart
            plt.figure(figsize=(10, 6))
            plt.bar(range(len(data['throughputs'])), data['throughputs'], color='darkgreen')
            plt.xlabel('Request Index')
            plt.ylabel('Throughput (req/s)')
            plt.title(f'Throughput Analysis: {os.path.basename(filepath)}')
            plt.tight_layout()
            plt.savefig(f'{chart_dir}/throughput_bar.png', dpi=150)
            plt.close()

        print(f"Charts written to: {chart_dir}/")

    except ImportError:
        print("\n matplotlib not installed; skipping graph generation.")
        print("Install with: pip install matplotlib numpy")

    return data


def main():
    parser = argparse.ArgumentParser(description='Analyze JMeter Summary Report CSV files')
    parser.add_argument('csv_file', help='Path to JMeter Summary Report CSV')
    parser.add_argument('--compare', help='Optional second CSV for comparison')
    args = parser.parse_args()

    if not os.path.isfile(args.csv_file):
        print(f"Error: File not found: {args.csv_file}", file=sys.stderr)
        sys.exit(1)

    data = analyze_csv(args.csv_file, args.compare)


if __name__ == '__main__':
    main()