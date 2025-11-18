"""
Analysis and Comparison of Collective Communication Experiments

Compares Scenario A (protected) vs Scenario B (unprotected) for:
- All-to-All collective
- All-Reduce collective

Generates comparison plots for:
- Delay
- Jitter
- Throughput
- Packet drops
"""

import sys
import os

# Add project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# Add priority stream simulator (in parent directory)
SIMULATOR_PATH = os.path.dirname(PROJECT_ROOT)
sys.path.insert(0, SIMULATOR_PATH)

from collections import defaultdict


class ResultsAnalyzer:
    """
    Analyzes and compares collective communication experiment results.
    """

    def __init__(self, results_dir: str = "../results"):
        """
        Initialize analyzer.

        Args:
            results_dir: Directory containing result files
        """
        self.results_dir = results_dir

    def load_results(self, scenario: str, collective: str):
        """
        Load results from CSV file.

        Args:
            scenario: 'a' or 'b'
            collective: 'all-to-all' or 'all-reduce'

        Returns:
            List of dictionaries with results
        """
        csv_file = os.path.join(self.results_dir, f"scenario_{scenario}",
                               f"scenario_{scenario}_{collective}.csv")

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
            Dictionary with metrics
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

        # Calculate statistics
        mean_delay = sum(all_delays) / len(all_delays) if all_delays else 0
        std_delay = (sum((x - mean_delay)**2 for x in all_delays) / len(all_delays))**0.5 if all_delays else 0
        min_delay = min(all_delays) if all_delays else 0
        max_delay = max(all_delays) if all_delays else 0
        mean_jitter = sum(all_jitters) / len(all_jitters) if all_jitters else 0

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
            'mean_jitter': mean_jitter,
            'num_streams': len(stream_metrics)
        }

    def analyze_collective(self, data, collective_stream_base: int = 1000):
        """
        Analyze collective traffic (filter out background).

        Args:
            data: List of dictionaries with results
            collective_stream_base: Base stream ID for collective streams

        Returns:
            Dictionary with metrics
        """
        # Filter for collective streams only (stream_id >= 1000 and < 5000)
        coll_data = [row for row in data if collective_stream_base <= row['stream_id'] < 5000]
        return self._compute_flow_metrics(coll_data)

    def analyze_low_priority(self, data, low_priority_stream_min: int = 5000):
        """
        Analyze low priority/background traffic.

        Args:
            data: List of dictionaries with results
            low_priority_stream_min: Minimum stream ID for low priority streams

        Returns:
            Dictionary with metrics
        """
        # Filter for low priority streams only (stream_id >= 5000)
        low_prio_data = [row for row in data if row['stream_id'] >= low_priority_stream_min]
        return self._compute_flow_metrics(low_prio_data)

    def compare_scenarios(self, collective: str):
        """
        Compare Scenario A vs B for a collective.

        Args:
            collective: 'all-to-all' or 'all-reduce'

        Returns:
            Dictionary with comparison data
        """
        # Load results
        data_a = self.load_results('a', collective)
        data_b = self.load_results('b', collective)

        if not data_a or not data_b:
            print(f"Warning: Missing data for {collective}")
            return {}

        # Analyze both scenarios for collective flows
        metrics_a = self.analyze_collective(data_a)
        metrics_b = self.analyze_collective(data_b)

        # Analyze low priority flows
        low_prio_a = self.analyze_low_priority(data_a)
        low_prio_b = self.analyze_low_priority(data_b)

        return {
            'scenario_a': metrics_a,
            'scenario_b': metrics_b,
            'low_prio_a': low_prio_a,
            'low_prio_b': low_prio_b,
            'collective': collective
        }

    def plot_comparison(self, collective: str, output_file: str):
        """
        Create comparison plots for a collective.

        Args:
            collective: 'all-to-all' or 'all-reduce'
            output_file: Output PNG file path
        """
        comparison = self.compare_scenarios(collective)

        if not comparison:
            print(f"No data to plot for {collective}")
            return

        metrics_a = comparison['scenario_a']
        metrics_b = comparison['scenario_b']
        low_prio_a = comparison['low_prio_a']
        low_prio_b = comparison['low_prio_b']

        # Create figure with 2x3 subplots
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle(f'{collective.replace("-", " ").title()} - Collective vs Low Priority Flows',
                    fontsize=16, fontweight='bold')

        scenarios = ['Protected', 'Unprotected']
        colors_coll = ['#2ecc71', '#e74c3c']  # Green for protected, red for unprotected
        colors_low = ['#3498db', '#e67e22']   # Blue for protected, orange for unprotected

        # Plot 1: Mean Delay - Collective
        ax1 = axes[0, 0]
        if metrics_a and metrics_b:
            delays_coll = [metrics_a.get('mean_delay', 0), metrics_b.get('mean_delay', 0)]
            bars1 = ax1.bar(scenarios, delays_coll, color=colors_coll, edgecolor='black', linewidth=2)
            ax1.set_ylabel('Mean Delay (ms)', fontweight='bold')
            ax1.set_title('Collective Flows - Mean Delay', fontweight='bold')
            ax1.grid(axis='y', alpha=0.3)
            for bar, val in zip(bars1, delays_coll):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Plot 2: Mean Delay - Low Priority
        ax2 = axes[0, 1]
        if low_prio_a and low_prio_b:
            delays_low = [low_prio_a.get('mean_delay', 0), low_prio_b.get('mean_delay', 0)]
            bars2 = ax2.bar(scenarios, delays_low, color=colors_low, edgecolor='black', linewidth=2)
            ax2.set_ylabel('Mean Delay (ms)', fontweight='bold')
            ax2.set_title('Low Priority Flows - Mean Delay', fontweight='bold')
            ax2.grid(axis='y', alpha=0.3)
            for bar, val in zip(bars2, delays_low):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Plot 3: Drop Rate Comparison
        ax3 = axes[0, 2]
        x_pos = [0, 1, 3, 4]
        drop_vals = [
            metrics_a.get('drop_rate', 0) if metrics_a else 0,
            metrics_b.get('drop_rate', 0) if metrics_b else 0,
            low_prio_a.get('drop_rate', 0) if low_prio_a else 0,
            low_prio_b.get('drop_rate', 0) if low_prio_b else 0
        ]
        bar_colors = [colors_coll[0], colors_coll[1], colors_low[0], colors_low[1]]
        bars3 = ax3.bar(x_pos, drop_vals, color=bar_colors, edgecolor='black', linewidth=2)
        ax3.set_ylabel('Drop Rate (%)', fontweight='bold')
        ax3.set_title('Drop Rate Comparison', fontweight='bold')
        ax3.set_xticks([0.5, 3.5])
        ax3.set_xticklabels(['Collective', 'Low Priority'])
        ax3.grid(axis='y', alpha=0.3)
        for i, (bar, val) in enumerate(zip(bars3, drop_vals)):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

        # Plot 4: Jitter - Collective
        ax4 = axes[1, 0]
        if metrics_a and metrics_b:
            jitter_coll = [metrics_a.get('mean_jitter', 0), metrics_b.get('mean_jitter', 0)]
            bars4 = ax4.bar(scenarios, jitter_coll, color=colors_coll, edgecolor='black', linewidth=2)
            ax4.set_ylabel('Mean Jitter (ms)', fontweight='bold')
            ax4.set_title('Collective Flows - Jitter', fontweight='bold')
            ax4.grid(axis='y', alpha=0.3)
            for bar, val in zip(bars4, jitter_coll):
                ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Plot 5: Jitter - Low Priority
        ax5 = axes[1, 1]
        if low_prio_a and low_prio_b:
            jitter_low = [low_prio_a.get('mean_jitter', 0), low_prio_b.get('mean_jitter', 0)]
            bars5 = ax5.bar(scenarios, jitter_low, color=colors_low, edgecolor='black', linewidth=2)
            ax5.set_ylabel('Mean Jitter (ms)', fontweight='bold')
            ax5.set_title('Low Priority Flows - Jitter', fontweight='bold')
            ax5.grid(axis='y', alpha=0.3)
            for bar, val in zip(bars5, jitter_low):
                ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Plot 6: Throughput Comparison
        ax6 = axes[1, 2]
        throughput_vals = [
            metrics_a.get('total_delivered', 0) if metrics_a else 0,
            metrics_b.get('total_delivered', 0) if metrics_b else 0,
            low_prio_a.get('total_delivered', 0) if low_prio_a else 0,
            low_prio_b.get('total_delivered', 0) if low_prio_b else 0
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
            Patch(facecolor=colors_coll[0], edgecolor='black', label='Collective - Protected (Prio 7)'),
            Patch(facecolor=colors_coll[1], edgecolor='black', label='Collective - Unprotected (Prio 3)'),
            Patch(facecolor=colors_low[0], edgecolor='black', label='Low Priority - Protected'),
            Patch(facecolor=colors_low[1], edgecolor='black', label='Low Priority - Unprotected')
        ]
        fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.97), ncol=4, fontsize=10)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Comparison plot saved: {output_file}")
        plt.close()

    def plot_time_series(self, scenario: str, collective: str, output_file: str):
        """
        Create time series plots showing metrics evolution over time.

        Args:
            scenario: 'a' or 'b'
            collective: 'all-to-all' or 'all-reduce'
            output_file: Output PNG file path
        """
        # Load data
        data = self.load_results(scenario, collective)

        if not data:
            print(f"No data to plot for scenario {scenario} {collective}")
            return

        # Separate collective and low priority flows
        coll_data = [row for row in data if 1000 <= row['stream_id'] < 5000]
        low_prio_data = [row for row in data if row['stream_id'] >= 5000]

        # Create figure with 2x2 subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        scenario_title = 'Protected (Priority 7)' if scenario == 'a' else 'Unprotected (Priority 3)'
        fig.suptitle(f'{collective.replace("-", " ").title()} - Time Series (Scenario {scenario.upper()}: {scenario_title})',
                    fontsize=16, fontweight='bold')

        # Process collective flows
        if coll_data:
            coll_times = [float(row['arrival_time']) for row in coll_data if not row['dropped'] and row['arrival_time']]
            coll_delays = [row['end_to_end_delay_ms'] for row in coll_data if not row['dropped'] and row['end_to_end_delay_ms']]

            # Plot 1: Collective Flow Delay Over Time
            ax1 = axes[0, 0]
            if coll_times and coll_delays:
                ax1.scatter(coll_times, coll_delays, alpha=0.5, s=10, color='#2ecc71' if scenario == 'a' else '#e74c3c')
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
                    ax1.plot(moving_times, moving_avg, color='darkred', linewidth=2, label='Moving Average')
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

                color = '#27ae60' if scenario == 'a' else '#c0392b'
                ax2.plot(bin_centers, throughputs, color=color, linewidth=2)
                ax2.fill_between(bin_centers, throughputs, alpha=0.3, color=color)
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
                ax3.scatter(low_times, low_delays, alpha=0.5, s=10, color='#3498db' if scenario == 'a' else '#e67e22')
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
                    ax3.plot(moving_times, moving_avg, color='darkred', linewidth=2, label='Moving Average')
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

                color = '#2980b9' if scenario == 'a' else '#d35400'
                ax4.plot(bin_centers, throughputs, color=color, linewidth=2)
                ax4.fill_between(bin_centers, throughputs, alpha=0.3, color=color)
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
        comparison = self.compare_scenarios(collective)

        if not comparison:
            return

        metrics_a = comparison['scenario_a']
        metrics_b = comparison['scenario_b']
        low_prio_a = comparison['low_prio_a']
        low_prio_b = comparison['low_prio_b']

        print("\n" + "="*70)
        print(f"{collective.upper()} COMPARISON SUMMARY")
        print("="*70)

        # Collective Flows Summary
        print(f"\n{'COLLECTIVE FLOWS':^70}")
        print("-"*70)

        print(f"\nScenario A (Protected - Priority 7):")
        if metrics_a:
            print(f"  Mean delay: {metrics_a.get('mean_delay', 0):.3f} ms")
            print(f"  Mean jitter: {metrics_a.get('mean_jitter', 0):.3f} ms")
            print(f"  Drop rate: {metrics_a.get('drop_rate', 0):.2f}%")
            print(f"  Messages delivered: {metrics_a.get('total_delivered', 0)}")
            print(f"  Messages dropped: {metrics_a.get('total_dropped', 0)}")
        else:
            print("  No data available")

        print(f"\nScenario B (Unprotected - Priority 3):")
        if metrics_b:
            print(f"  Mean delay: {metrics_b.get('mean_delay', 0):.3f} ms")
            print(f"  Mean jitter: {metrics_b.get('mean_jitter', 0):.3f} ms")
            print(f"  Drop rate: {metrics_b.get('drop_rate', 0):.2f}%")
            print(f"  Messages delivered: {metrics_b.get('total_delivered', 0)}")
            print(f"  Messages dropped: {metrics_b.get('total_dropped', 0)}")
        else:
            print("  No data available")

        if metrics_a and metrics_b:
            print(f"\nCollective Flows Comparison (A vs B):")
            delay_diff = ((metrics_b.get('mean_delay', 0) - metrics_a.get('mean_delay', 0)) /
                         metrics_a.get('mean_delay', 1) * 100) if metrics_a.get('mean_delay', 0) > 0 else 0
            jitter_diff = ((metrics_b.get('mean_jitter', 0) - metrics_a.get('mean_jitter', 0)) /
                          metrics_a.get('mean_jitter', 1) * 100) if metrics_a.get('mean_jitter', 0) > 0 else 0
            drop_diff = metrics_b.get('drop_rate', 0) - metrics_a.get('drop_rate', 0)

            print(f"  Delay difference: {delay_diff:+.1f}% " +
                  ("(WORSE)" if delay_diff > 0 else "(BETTER)"))
            print(f"  Jitter difference: {jitter_diff:+.1f}% " +
                  ("(WORSE)" if jitter_diff > 0 else "(BETTER)"))
            print(f"  Drop rate difference: {drop_diff:+.2f}% " +
                  ("(WORSE)" if drop_diff > 0 else "(BETTER)"))

        # Low Priority Flows Summary
        print(f"\n{'LOW PRIORITY FLOWS':^70}")
        print("-"*70)

        print(f"\nScenario A (Protected):")
        if low_prio_a:
            print(f"  Mean delay: {low_prio_a.get('mean_delay', 0):.3f} ms")
            print(f"  Mean jitter: {low_prio_a.get('mean_jitter', 0):.3f} ms")
            print(f"  Drop rate: {low_prio_a.get('drop_rate', 0):.2f}%")
            print(f"  Messages delivered: {low_prio_a.get('total_delivered', 0)}")
            print(f"  Messages dropped: {low_prio_a.get('total_dropped', 0)}")
        else:
            print("  No data available")

        print(f"\nScenario B (Unprotected):")
        if low_prio_b:
            print(f"  Mean delay: {low_prio_b.get('mean_delay', 0):.3f} ms")
            print(f"  Mean jitter: {low_prio_b.get('mean_jitter', 0):.3f} ms")
            print(f"  Drop rate: {low_prio_b.get('drop_rate', 0):.2f}%")
            print(f"  Messages delivered: {low_prio_b.get('total_delivered', 0)}")
            print(f"  Messages dropped: {low_prio_b.get('total_dropped', 0)}")
        else:
            print("  No data available")

        if low_prio_a and low_prio_b:
            print(f"\nLow Priority Flows Comparison (A vs B):")
            delay_diff_low = ((low_prio_b.get('mean_delay', 0) - low_prio_a.get('mean_delay', 0)) /
                             low_prio_a.get('mean_delay', 1) * 100) if low_prio_a.get('mean_delay', 0) > 0 else 0
            jitter_diff_low = ((low_prio_b.get('mean_jitter', 0) - low_prio_a.get('mean_jitter', 0)) /
                              low_prio_a.get('mean_jitter', 1) * 100) if low_prio_a.get('mean_jitter', 0) > 0 else 0
            drop_diff_low = low_prio_b.get('drop_rate', 0) - low_prio_a.get('drop_rate', 0)

            print(f"  Delay difference: {delay_diff_low:+.1f}% " +
                  ("(WORSE)" if delay_diff_low > 0 else "(BETTER)"))
            print(f"  Jitter difference: {jitter_diff_low:+.1f}% " +
                  ("(WORSE)" if jitter_diff_low > 0 else "(BETTER)"))
            print(f"  Drop rate difference: {drop_diff_low:+.2f}% " +
                  ("(WORSE)" if drop_diff_low > 0 else "(BETTER)"))

        print("="*70 + "\n")


def main():
    """Analyze all experiments and generate plots."""
    analyzer = ResultsAnalyzer()

    plots_dir = "../plots"
    os.makedirs(plots_dir, exist_ok=True)

    print("\n" + "="*70)
    print("ANALYZING COLLECTIVE COMMUNICATION EXPERIMENTS")
    print("="*70)

    collectives = ["all-to-all", "all-reduce"]

    for collective in collectives:
        # Print summary
        analyzer.print_summary(collective)

        # Generate comparison plot
        output_file = os.path.join(plots_dir, f"comparison_{collective}.png")
        analyzer.plot_comparison(collective, output_file)

        # Generate time series plots for both scenarios
        for scenario in ['a', 'b']:
            ts_output_file = os.path.join(plots_dir, f"timeseries_scenario_{scenario}_{collective}.png")
            analyzer.plot_time_series(scenario, collective, ts_output_file)

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nPlots saved to: {plots_dir}/")


if __name__ == "__main__":
    main()
