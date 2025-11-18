"""
Preemptive Experiment Analysis

Compares frame preemption (protected) vs non-preemption (unprotected)
for collective communication operations.

Metrics analyzed:
- Delay (mean, min, max, tail latencies)
- Jitter
- Packet drops
- Preemption events
"""

import sys
import os

# Add project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# Add priority stream simulator (in parent directory)
SIMULATOR_PATH = os.path.dirname(PROJECT_ROOT)
sys.path.insert(0, SIMULATOR_PATH)

from collections import defaultdict


class PreemptionAnalyzer:
    """
    Analyzes and compares preemptive vs non-preemptive experiments.
    """

    def __init__(self, results_dir: str = "../results"):
        """
        Initialize analyzer.

        Args:
            results_dir: Directory containing result files
        """
        self.results_dir = results_dir

    def load_results(self, mode: str, collective: str):
        """
        Load results from CSV file.

        Args:
            mode: 'protected' or 'unprotected'
            collective: 'all-to-all' or 'all-reduce'

        Returns:
            List of dictionaries with results
        """
        csv_file = os.path.join(self.results_dir, mode,
                               f"{mode}_{collective}.csv")

        if not os.path.exists(csv_file):
            print(f"Warning: File not found: {csv_file}")
            return []

        data = []
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                row['stream_id'] = int(row['stream_id'])
                row['priority'] = int(row['priority'])
                row['dropped'] = row['dropped'].lower() == 'true'
                if row['end_to_end_delay_ms']:
                    row['end_to_end_delay_ms'] = float(row['end_to_end_delay_ms'])
                data.append(row)

        return data

    def _compute_flow_metrics(self, flow_data):
        """
        Compute metrics for a set of flows.

        Args:
            flow_data: List of dictionaries with flow results

        Returns:
            Dictionary with metrics including tail latencies
        """
        if len(flow_data) == 0:
            return {}

        # Calculate per-stream metrics
        stream_metrics = defaultdict(lambda: {'delays': [], 'delivered': 0, 'dropped': 0})

        for row in flow_data:
            sid = row['stream_id']
            if row['dropped']:
                stream_metrics[sid]['dropped'] += 1
            else:
                stream_metrics[sid]['delivered'] += 1
                if row['end_to_end_delay_ms']:
                    stream_metrics[sid]['delays'].append(row['end_to_end_delay_ms'])

        # Aggregate metrics
        all_delays = []
        all_jitters = []
        total_delivered = 0
        total_dropped = 0

        for sid, metrics in stream_metrics.items():
            total_delivered += metrics['delivered']
            total_dropped += metrics['dropped']
            all_delays.extend(metrics['delays'])

            # Calculate jitter for this stream
            if len(metrics['delays']) > 1:
                jitters = [abs(metrics['delays'][i] - metrics['delays'][i-1])
                          for i in range(1, len(metrics['delays']))]
                all_jitters.extend(jitters)

        # Sort delays for percentile calculations
        all_delays.sort()

        # Calculate statistics
        mean_delay = sum(all_delays) / len(all_delays) if all_delays else 0
        std_delay = (sum((x - mean_delay)**2 for x in all_delays) / len(all_delays))**0.5 if all_delays else 0
        min_delay = min(all_delays) if all_delays else 0
        max_delay = max(all_delays) if all_delays else 0
        mean_jitter = sum(all_jitters) / len(all_jitters) if all_jitters else 0

        # Tail latencies (percentiles)
        def percentile(data, p):
            if not data:
                return 0
            k = (len(data) - 1) * p / 100.0
            f = int(k)
            c = f + 1 if f + 1 < len(data) else f
            return data[f] + (k - f) * (data[c] - data[f])

        p50 = percentile(all_delays, 50)
        p95 = percentile(all_delays, 95)
        p99 = percentile(all_delays, 99)

        total = total_delivered + total_dropped
        drop_rate = (total_dropped / total * 100) if total > 0 else 0

        return {
            'total_delivered': total_delivered,
            'total_dropped': total_dropped,
            'drop_rate': drop_rate,
            'mean_delay': mean_delay,
            'std_delay': std_delay,
            'min_delay': min_delay,
            'max_delay': max_delay,
            'p50_delay': p50,
            'p95_delay': p95,
            'p99_delay': p99,
            'mean_jitter': mean_jitter,
            'num_streams': len(stream_metrics)
        }

    def analyze_collective(self, data, collective_stream_base: int = 1000, low_priority_stream_min: int = 5000):
        """
        Analyze collective traffic (filter out background).

        Args:
            data: List of dictionaries with results
            collective_stream_base: Base stream ID for collective streams
            low_priority_stream_min: Maximum stream ID for collective streams

        Returns:
            Dictionary with metrics including tail latencies
        """
        # Filter for collective streams only
        coll_data = [row for row in data if collective_stream_base < row['stream_id'] < low_priority_stream_min]
        return self._compute_flow_metrics(coll_data)

    def analyze_low_priority(self, data, low_priority_stream_min: int = 5000):
        """
        Analyze low priority/background traffic.

        Args:
            data: List of dictionaries with results
            low_priority_stream_min: Minimum stream ID for low priority streams

        Returns:
            Dictionary with metrics including tail latencies
        """
        # Filter for low priority streams only (stream_id >= 5000)
        low_prio_data = [row for row in data if row['stream_id'] >= low_priority_stream_min]
        return self._compute_flow_metrics(low_prio_data)

    def compare_modes(self, collective: str):
        """
        Compare protected vs unprotected modes for a collective.

        Args:
            collective: 'all-to-all' or 'all-reduce'

        Returns:
            Dictionary with comparison data
        """
        # Load results
        data_protected = self.load_results('protected', collective)
        data_unprotected = self.load_results('unprotected', collective)

        if not data_protected or not data_unprotected:
            print(f"Warning: Missing data for {collective}")
            return {}

        # Analyze both modes for collective flows
        metrics_protected = self.analyze_collective(data_protected)
        metrics_unprotected = self.analyze_collective(data_unprotected)

        # Analyze low priority flows
        low_prio_protected = self.analyze_low_priority(data_protected)
        low_prio_unprotected = self.analyze_low_priority(data_unprotected)

        return {
            'protected': metrics_protected,
            'unprotected': metrics_unprotected,
            'low_prio_protected': low_prio_protected,
            'low_prio_unprotected': low_prio_unprotected,
            'collective': collective
        }

    def plot_comparison(self, collective: str, output_file: str):
        """
        Create comparison plots for a collective.

        Args:
            collective: 'all-to-all' or 'all-reduce'
            output_file: Output PNG file path
        """
        comparison = self.compare_modes(collective)

        if not comparison:
            print(f"No data to plot for {collective}")
            return

        metrics_prot = comparison['protected']
        metrics_unprot = comparison['unprotected']
        low_prio_prot = comparison['low_prio_protected']
        low_prio_unprot = comparison['low_prio_unprotected']

        # Create figure with 2x3 subplots
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle(f'{collective.replace("-", " ").title()} - Collective vs Low Priority Flows',
                    fontsize=16, fontweight='bold')

        flow_types = ['Collective', 'Low Priority']
        colors_coll = ['#3498db', '#e74c3c']  # Blue for protected, red for unprotected
        colors_low = ['#2ecc71', '#e67e22']   # Green for protected, orange for unprotected

        # Plot 1: Mean Delay - Collective
        ax1 = axes[0, 0]
        if metrics_prot and metrics_unprot:
            delays_coll = [metrics_prot.get('mean_delay', 0), metrics_unprot.get('mean_delay', 0)]
            modes_coll = ['Protected', 'Unprotected']
            bars1 = ax1.bar(modes_coll, delays_coll, color=colors_coll, edgecolor='black', linewidth=2)
            ax1.set_ylabel('Mean Delay (ms)', fontweight='bold')
            ax1.set_title('Collective Flows - Mean Delay', fontweight='bold')
            ax1.grid(axis='y', alpha=0.3)
            for bar, val in zip(bars1, delays_coll):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Plot 2: Mean Delay - Low Priority
        ax2 = axes[0, 1]
        if low_prio_prot and low_prio_unprot:
            delays_low = [low_prio_prot.get('mean_delay', 0), low_prio_unprot.get('mean_delay', 0)]
            modes_low = ['Protected', 'Unprotected']
            bars2 = ax2.bar(modes_low, delays_low, color=colors_low, edgecolor='black', linewidth=2)
            ax2.set_ylabel('Mean Delay (ms)', fontweight='bold')
            ax2.set_title('Low Priority Flows - Mean Delay', fontweight='bold')
            ax2.grid(axis='y', alpha=0.3)
            for bar, val in zip(bars2, delays_low):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Plot 3: P99 Latency Comparison (both flow types)
        ax3 = axes[0, 2]
        x_pos = [0, 1, 3, 4]
        p99_vals = [
            metrics_prot.get('p99_delay', 0) if metrics_prot else 0,
            metrics_unprot.get('p99_delay', 0) if metrics_unprot else 0,
            low_prio_prot.get('p99_delay', 0) if low_prio_prot else 0,
            low_prio_unprot.get('p99_delay', 0) if low_prio_unprot else 0
        ]
        bar_colors = [colors_coll[0], colors_coll[1], colors_low[0], colors_low[1]]
        bars3 = ax3.bar(x_pos, p99_vals, color=bar_colors, edgecolor='black', linewidth=2)
        ax3.set_ylabel('P99 Latency (ms)', fontweight='bold')
        ax3.set_title('P99 Tail Latency Comparison', fontweight='bold')
        ax3.set_xticks([0.5, 3.5])
        ax3.set_xticklabels(['Collective', 'Low Priority'])
        ax3.grid(axis='y', alpha=0.3)
        for i, (bar, val) in enumerate(zip(bars3, p99_vals)):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

        # Plot 4: Jitter - Collective
        ax4 = axes[1, 0]
        if metrics_prot and metrics_unprot:
            jitter_coll = [metrics_prot.get('mean_jitter', 0), metrics_unprot.get('mean_jitter', 0)]
            bars4 = ax4.bar(modes_coll, jitter_coll, color=colors_coll, edgecolor='black', linewidth=2)
            ax4.set_ylabel('Mean Jitter (ms)', fontweight='bold')
            ax4.set_title('Collective Flows - Jitter', fontweight='bold')
            ax4.grid(axis='y', alpha=0.3)
            for bar, val in zip(bars4, jitter_coll):
                ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Plot 5: Jitter - Low Priority
        ax5 = axes[1, 1]
        if low_prio_prot and low_prio_unprot:
            jitter_low = [low_prio_prot.get('mean_jitter', 0), low_prio_unprot.get('mean_jitter', 0)]
            bars5 = ax5.bar(modes_low, jitter_low, color=colors_low, edgecolor='black', linewidth=2)
            ax5.set_ylabel('Mean Jitter (ms)', fontweight='bold')
            ax5.set_title('Low Priority Flows - Jitter', fontweight='bold')
            ax5.grid(axis='y', alpha=0.3)
            for bar, val in zip(bars5, jitter_low):
                ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Plot 6: Throughput Comparison
        ax6 = axes[1, 2]
        throughput_vals = [
            metrics_prot.get('total_delivered', 0) if metrics_prot else 0,
            metrics_unprot.get('total_delivered', 0) if metrics_unprot else 0,
            low_prio_prot.get('total_delivered', 0) if low_prio_prot else 0,
            low_prio_unprot.get('total_delivered', 0) if low_prio_unprot else 0
        ]
        bars6 = ax6.bar(x_pos, throughput_vals, color=bar_colors, edgecolor='black', linewidth=2)
        ax6.set_ylabel('Messages Delivered', fontweight='bold')
        ax6.set_title('Throughput Comparison', fontweight='bold')
        ax6.set_xticks([0.5, 3.5])
        ax6.set_xticklabels(['Collective', 'Low Priority'])
        ax6.grid(axis='y', alpha=0.3)
        for i, (bar, val) in enumerate(zip(bars6, throughput_vals)):
            ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{int(val)}', ha='center', va='bottom', fontsize=9, fontweight='bold')

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=colors_coll[0], edgecolor='black', label='Collective - Protected'),
            Patch(facecolor=colors_coll[1], edgecolor='black', label='Collective - Unprotected'),
            Patch(facecolor=colors_low[0], edgecolor='black', label='Low Priority - Protected'),
            Patch(facecolor=colors_low[1], edgecolor='black', label='Low Priority - Unprotected')
        ]
        fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.97), ncol=4, fontsize=10)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Comparison plot saved: {output_file}")
        plt.close()

    def plot_time_series(self, mode: str, collective: str, output_file: str):
        """
        Create time series plots showing metrics evolution over time.

        Args:
            mode: 'protected' or 'unprotected'
            collective: 'all-to-all' or 'all-reduce'
            output_file: Output PNG file path
        """
        # Load data
        data = self.load_results(mode, collective)

        if not data:
            print(f"No data to plot for {mode} {collective}")
            return

        # Separate collective and low priority flows
        coll_data = [row for row in data if 1000 < row['stream_id'] < 5000]
        low_prio_data = [row for row in data if row['stream_id'] >= 5000]

        # Create figure with 2x2 subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        mode_title = 'Protected (Preemption ON)' if mode == 'protected' else 'Unprotected (Preemption OFF)'
        fig.suptitle(f'{collective.replace("-", " ").title()} - Time Series ({mode_title})',
                    fontsize=16, fontweight='bold')

        # Process collective flows
        if coll_data:
            coll_times = [float(row['arrival_time']) for row in coll_data if not row['dropped'] and row['arrival_time']]
            coll_delays = [row['end_to_end_delay_ms'] for row in coll_data if not row['dropped'] and row['end_to_end_delay_ms']]

            # Plot 1: Collective Flow Delay Over Time
            ax1 = axes[0, 0]
            if coll_times and coll_delays:
                ax1.scatter(coll_times, coll_delays, alpha=0.5, s=10, color='#3498db')
                ax1.set_xlabel('Time (s)', fontweight='bold')
                ax1.set_ylabel('Delay (ms)', fontweight='bold')
                ax1.set_title('Collective Flows - Delay Over Time', fontweight='bold')
                ax1.grid(True, alpha=0.3)

                # Add moving average
                window_size = max(1, len(coll_delays) // 50)
                if len(coll_delays) >= window_size:
                    moving_avg = []
                    moving_times = []
                    for i in range(len(coll_delays) - window_size + 1):
                        moving_avg.append(sum(coll_delays[i:i+window_size]) / window_size)
                        moving_times.append(coll_times[i + window_size // 2])
                    ax1.plot(moving_times, moving_avg, color='red', linewidth=2, label='Moving Average')
                    ax1.legend()

            # Plot 2: Collective Flow Throughput Over Time
            ax2 = axes[0, 1]
            if coll_times:
                # Bin messages into time windows
                time_bins = {}
                bin_width = 0.1  # 100ms bins
                for t in coll_times:
                    bin_key = int(t / bin_width)
                    time_bins[bin_key] = time_bins.get(bin_key, 0) + 1

                bin_centers = [k * bin_width + bin_width/2 for k in sorted(time_bins.keys())]
                throughputs = [time_bins[k] / bin_width for k in sorted(time_bins.keys())]  # messages per second

                ax2.plot(bin_centers, throughputs, color='#2ecc71', linewidth=2)
                ax2.fill_between(bin_centers, throughputs, alpha=0.3, color='#2ecc71')
                ax2.set_xlabel('Time (s)', fontweight='bold')
                ax2.set_ylabel('Throughput (msgs/s)', fontweight='bold')
                ax2.set_title('Collective Flows - Throughput Over Time', fontweight='bold')
                ax2.grid(True, alpha=0.3)

        # Process low priority flows
        if low_prio_data:
            low_times = [float(row['arrival_time']) for row in low_prio_data if not row['dropped'] and row['arrival_time']]
            low_delays = [row['end_to_end_delay_ms'] for row in low_prio_data if not row['dropped'] and row['end_to_end_delay_ms']]

            # Plot 3: Low Priority Flow Delay Over Time
            ax3 = axes[1, 0]
            if low_times and low_delays:
                ax3.scatter(low_times, low_delays, alpha=0.5, s=10, color='#e67e22')
                ax3.set_xlabel('Time (s)', fontweight='bold')
                ax3.set_ylabel('Delay (ms)', fontweight='bold')
                ax3.set_title('Low Priority Flows - Delay Over Time', fontweight='bold')
                ax3.grid(True, alpha=0.3)

                # Add moving average
                window_size = max(1, len(low_delays) // 20)
                if len(low_delays) >= window_size:
                    moving_avg = []
                    moving_times = []
                    for i in range(len(low_delays) - window_size + 1):
                        moving_avg.append(sum(low_delays[i:i+window_size]) / window_size)
                        moving_times.append(low_times[i + window_size // 2])
                    ax3.plot(moving_times, moving_avg, color='red', linewidth=2, label='Moving Average')
                    ax3.legend()

            # Plot 4: Low Priority Flow Throughput Over Time
            ax4 = axes[1, 1]
            if low_times:
                # Bin messages into time windows
                time_bins = {}
                bin_width = 0.1  # 100ms bins
                for t in low_times:
                    bin_key = int(t / bin_width)
                    time_bins[bin_key] = time_bins.get(bin_key, 0) + 1

                bin_centers = [k * bin_width + bin_width/2 for k in sorted(time_bins.keys())]
                throughputs = [time_bins[k] / bin_width for k in sorted(time_bins.keys())]

                ax4.plot(bin_centers, throughputs, color='#9b59b6', linewidth=2)
                ax4.fill_between(bin_centers, throughputs, alpha=0.3, color='#9b59b6')
                ax4.set_xlabel('Time (s)', fontweight='bold')
                ax4.set_ylabel('Throughput (msgs/s)', fontweight='bold')
                ax4.set_title('Low Priority Flows - Throughput Over Time', fontweight='bold')
                ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Time series plot saved: {output_file}")
        plt.close()

    def print_summary(self, collective: str):
        """
        Print text summary of comparison.

        Args:
            collective: 'all-to-all' or 'all-reduce'
        """
        comparison = self.compare_modes(collective)

        if not comparison:
            return

        metrics_prot = comparison['protected']
        metrics_unprot = comparison['unprotected']
        low_prio_prot = comparison['low_prio_protected']
        low_prio_unprot = comparison['low_prio_unprotected']

        print("\n" + "="*70)
        print(f"{collective.upper()} PREEMPTION COMPARISON")
        print("="*70)

        # Collective Flows Summary
        print(f"\n{'COLLECTIVE FLOWS':^70}")
        print("-"*70)

        print(f"\nProtected Mode (Preemption ENABLED):")
        if metrics_prot:
            print(f"  Mean delay: {metrics_prot.get('mean_delay', 0):.3f} ms")
            print(f"  P50 delay: {metrics_prot.get('p50_delay', 0):.3f} ms")
            print(f"  P95 delay: {metrics_prot.get('p95_delay', 0):.3f} ms")
            print(f"  P99 delay: {metrics_prot.get('p99_delay', 0):.3f} ms")
            print(f"  Mean jitter: {metrics_prot.get('mean_jitter', 0):.3f} ms")
            print(f"  Drop rate: {metrics_prot.get('drop_rate', 0):.2f}%")
            print(f"  Messages delivered: {metrics_prot.get('total_delivered', 0)}")
        else:
            print("  No data available")

        print(f"\nUnprotected Mode (Preemption DISABLED):")
        if metrics_unprot:
            print(f"  Mean delay: {metrics_unprot.get('mean_delay', 0):.3f} ms")
            print(f"  P50 delay: {metrics_unprot.get('p50_delay', 0):.3f} ms")
            print(f"  P95 delay: {metrics_unprot.get('p95_delay', 0):.3f} ms")
            print(f"  P99 delay: {metrics_unprot.get('p99_delay', 0):.3f} ms")
            print(f"  Mean jitter: {metrics_unprot.get('mean_jitter', 0):.3f} ms")
            print(f"  Drop rate: {metrics_unprot.get('drop_rate', 0):.2f}%")
            print(f"  Messages delivered: {metrics_unprot.get('total_delivered', 0)}")
        else:
            print("  No data available")

        if metrics_prot and metrics_unprot:
            print(f"\nCollective Flows Impact (Protected vs Unprotected):")
            delay_diff = ((metrics_prot.get('mean_delay', 0) - metrics_unprot.get('mean_delay', 0)) /
                         metrics_unprot.get('mean_delay', 1) * 100) if metrics_unprot.get('mean_delay', 0) > 0 else 0
            p99_diff = ((metrics_prot.get('p99_delay', 0) - metrics_unprot.get('p99_delay', 0)) /
                       metrics_unprot.get('p99_delay', 1) * 100) if metrics_unprot.get('p99_delay', 0) > 0 else 0
            jitter_diff = ((metrics_prot.get('mean_jitter', 0) - metrics_unprot.get('mean_jitter', 0)) /
                          metrics_unprot.get('mean_jitter', 1) * 100) if metrics_unprot.get('mean_jitter', 0) > 0 else 0
            drop_diff = metrics_prot.get('drop_rate', 0) - metrics_unprot.get('drop_rate', 0)

            print(f"  Mean delay change: {delay_diff:+.2f}% " +
                  ("(BETTER)" if delay_diff < 0 else "(WORSE)" if delay_diff > 0 else "(SAME)"))
            print(f"  P99 tail latency change: {p99_diff:+.2f}% " +
                  ("(BETTER)" if p99_diff < 0 else "(WORSE)" if p99_diff > 0 else "(SAME)"))
            print(f"  Jitter change: {jitter_diff:+.2f}% " +
                  ("(BETTER)" if jitter_diff < 0 else "(WORSE)" if jitter_diff > 0 else "(SAME)"))
            print(f"  Drop rate difference: {drop_diff:+.2f}% " +
                  ("(BETTER)" if drop_diff < 0 else "(WORSE)" if drop_diff > 0 else "(SAME)"))

        # Low Priority Flows Summary
        print(f"\n{'LOW PRIORITY FLOWS':^70}")
        print("-"*70)

        print(f"\nProtected Mode (Preemption ENABLED):")
        if low_prio_prot:
            print(f"  Mean delay: {low_prio_prot.get('mean_delay', 0):.3f} ms")
            print(f"  P50 delay: {low_prio_prot.get('p50_delay', 0):.3f} ms")
            print(f"  P95 delay: {low_prio_prot.get('p95_delay', 0):.3f} ms")
            print(f"  P99 delay: {low_prio_prot.get('p99_delay', 0):.3f} ms")
            print(f"  Mean jitter: {low_prio_prot.get('mean_jitter', 0):.3f} ms")
            print(f"  Drop rate: {low_prio_prot.get('drop_rate', 0):.2f}%")
            print(f"  Messages delivered: {low_prio_prot.get('total_delivered', 0)}")
        else:
            print("  No data available")

        print(f"\nUnprotected Mode (Preemption DISABLED):")
        if low_prio_unprot:
            print(f"  Mean delay: {low_prio_unprot.get('mean_delay', 0):.3f} ms")
            print(f"  P50 delay: {low_prio_unprot.get('p50_delay', 0):.3f} ms")
            print(f"  P95 delay: {low_prio_unprot.get('p95_delay', 0):.3f} ms")
            print(f"  P99 delay: {low_prio_unprot.get('p99_delay', 0):.3f} ms")
            print(f"  Mean jitter: {low_prio_unprot.get('mean_jitter', 0):.3f} ms")
            print(f"  Drop rate: {low_prio_unprot.get('drop_rate', 0):.2f}%")
            print(f"  Messages delivered: {low_prio_unprot.get('total_delivered', 0)}")
        else:
            print("  No data available")

        if low_prio_prot and low_prio_unprot:
            print(f"\nLow Priority Flows Impact (Protected vs Unprotected):")
            delay_diff_low = ((low_prio_prot.get('mean_delay', 0) - low_prio_unprot.get('mean_delay', 0)) /
                             low_prio_unprot.get('mean_delay', 1) * 100) if low_prio_unprot.get('mean_delay', 0) > 0 else 0
            p99_diff_low = ((low_prio_prot.get('p99_delay', 0) - low_prio_unprot.get('p99_delay', 0)) /
                           low_prio_unprot.get('p99_delay', 1) * 100) if low_prio_unprot.get('p99_delay', 0) > 0 else 0
            jitter_diff_low = ((low_prio_prot.get('mean_jitter', 0) - low_prio_unprot.get('mean_jitter', 0)) /
                              low_prio_unprot.get('mean_jitter', 1) * 100) if low_prio_unprot.get('mean_jitter', 0) > 0 else 0
            drop_diff_low = low_prio_prot.get('drop_rate', 0) - low_prio_unprot.get('drop_rate', 0)

            print(f"  Mean delay change: {delay_diff_low:+.2f}% " +
                  ("(BETTER)" if delay_diff_low < 0 else "(WORSE)" if delay_diff_low > 0 else "(SAME)"))
            print(f"  P99 tail latency change: {p99_diff_low:+.2f}% " +
                  ("(BETTER)" if p99_diff_low < 0 else "(WORSE)" if p99_diff_low > 0 else "(SAME)"))
            print(f"  Jitter change: {jitter_diff_low:+.2f}% " +
                  ("(BETTER)" if jitter_diff_low < 0 else "(WORSE)" if jitter_diff_low > 0 else "(SAME)"))
            print(f"  Drop rate difference: {drop_diff_low:+.2f}% " +
                  ("(BETTER)" if drop_diff_low < 0 else "(WORSE)" if drop_diff_low > 0 else "(SAME)"))

        print("="*70 + "\n")


def main():
    """Analyze all preemption experiments and generate plots."""
    analyzer = PreemptionAnalyzer()

    plots_dir = "../plots"
    os.makedirs(plots_dir, exist_ok=True)

    print("\n" + "="*70)
    print("ANALYZING PREEMPTIVE EXPERIMENTS")
    print("="*70)

    collectives = ["all-to-all", "all-reduce"]

    for collective in collectives:
        # Print summary
        analyzer.print_summary(collective)

        # Generate comparison plot
        output_file = os.path.join(plots_dir, f"preemption_{collective}.png")
        analyzer.plot_comparison(collective, output_file)

        # Generate time series plots for both modes
        for mode in ['protected', 'unprotected']:
            ts_output_file = os.path.join(plots_dir, f"timeseries_{mode}_{collective}.png")
            analyzer.plot_time_series(mode, collective, ts_output_file)

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nPlots saved to: {plots_dir}/")


if __name__ == "__main__":
    main()
