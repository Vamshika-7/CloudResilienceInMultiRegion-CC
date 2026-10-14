import csv
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

jtl_path = r'C:\CloudResilienceInMultiRegion-CC\results\baseline_fresh_load.jtl'

# Read JTL structure
with open(jtl_path, 'r', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    cols = reader.fieldnames
    print('JTL Columns:', cols)
    rows = list(reader)

n = len(rows)
print(f'Total rows: {n}')

# Extract data
elapsed = [int(r['elapsed']) for r in rows]
response_codes = [r['responseCode'] for r in rows]
successes = [r['success'].lower() == 'true' for r in rows]
urls = [r['URL'] for r in rows]

print(f'Elapsed range: {min(elapsed)}ms - {max(elapsed)}ms')
print(f'Avg elapsed: {sum(elapsed)/n:.2f}ms')
print(f'Unique response codes: {set(response_codes)}')
print(f'All success: {all(successes)}')
print(f'Unique URLs: {set(urls)}')

# 1. Latency distribution histogram
plt.figure(figsize=(10, 6))
plt.hist(elapsed, bins=20, color='steelblue', edgecolor='black')
plt.xlabel('Latency (ms)')
plt.ylabel('Frequency')
plt.title('Latency Distribution: baseline_fresh_load.jtl (1000 samples, K3s Region A)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('latency_distribution.png', dpi=150)
plt.close()
print('Saved: latency_distribution.png')

# 2. Comparison chart: average and max latency across baselines
# Available baselines from existing CSVs:
# - baseline_load: avg 27ms, max 317ms (1000 samples)
# - baseline_smoke: avg 3ms, max 9ms (10 samples)  
# - baseline_fresh: avg 6.52ms, max 97ms (1000 samples)

baselines = {
    'Docker Compose Load': {'avg': 27, 'max': 317, 'samples': 1000},
    'Docker Compose Smoke': {'avg': 3, 'max': 9, 'samples': 10},
    'K3s Fresh': {'avg': 6.52, 'max': 97, 'samples': 1000},
}

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Average latency bar chart
ax = axes[0]
labels = list(baselines.keys())
avg_vals = [baselines[b]['avg'] for b in baselines]
max_vals = [baselines[b]['max'] for b in baselines]  # will use as error bars or separate

x_pos = np.arange(len(labels))
ax.bar(x_pos, avg_vals, color=['steelblue', 'lightgreen', 'darkorange'], alpha=0.7, label='Average Latency')
ax.errorbar(x_pos, avg_vals, yerr=max_vals, fmt='none', color='black', capsize=5, label='Max Latency')
ax.set_xticks(x_pos)
ax.set_xticklabels(labels, rotation=15, ha='right')
ax.set_ylabel('Latency (ms)')
ax.set_title('Average & Max Latency Comparison Across Baselines')
ax.legend()
ax.grid(True, alpha=0.3)

# Max latency bar chart
ax2 = axes[1]
ax2.bar(x_pos, max_vals, color=['steelblue', 'lightgreen', 'darkorange'], alpha=0.7)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(labels, rotation=15, ha='right')
ax2.set_ylabel('Max Latency (ms)')
ax2.set_title('Max Latency Comparison Across Baselines')
ax2.grid(True, alpha=0.3)

plt.suptitle('Latency Comparison: Docker Compose vs K3s Fresh Baseline', fontsize=14)
plt.tight_layout()
plt.savefig('latency_comparison.png', dpi=150)
plt.close()
print('Saved: latency_comparison.png')

# 3. Throughput comparison chart
# Data points:
# - JMeter official reported throughput: 104.8 req/s (during the ~10s test run)
# - Sample-span rate: 108.79 req/s (1000 samples / 9.192s actual duration from JTL timestamps)
# - baseline_load: 98.82 req/s
# - baseline_smoke: 238.10 req/s

fig, ax = plt.subplots(figsize=(10, 6))

methods = ['JMeter Official', 'Sample-Span Rate', 'Docker Load', 'Docker Smoke', 'K3s Fresh']
throughputs = [104.8, 108.79, 98.82, 238.10, 100.00]  # K3s fresh throughput from CSV

colors = ['darkorange', 'red', 'steelblue', 'lightgreen', 'darkorange']

bars = ax.bar(methods, throughputs, color=colors, alpha=0.7)
ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='100 req/s baseline')

# Add value labels on top of bars
for bar, throughput in zip(bars, throughputs):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{throughput:.1f}', ha='center', va='bottom')

ax.set_ylabel('Throughput (req/s)')
ax.set_title('Throughput Comparison: JMeter Official vs Sample-Span Rate vs Baselines')
ax.set_ylim(0, 250)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right')

# Rotate x-axis labels for readability
plt.xticks(rotation=25, ha='right')
plt.tight_layout()
plt.savefig('throughput_comparison.png', dpi=150)
plt.close()
print('Saved: throughput_comparison.png')

print()
print('=== All three graphs saved ===')
print('1. latency_distribution.png - Latency histogram from JTL data')
print('2. latency_comparison.png - Avg & max latency across three baselines')
print('3. throughput_comparison.png - JMeter official 104.8 vs sample-span 108.79 vs baselines')