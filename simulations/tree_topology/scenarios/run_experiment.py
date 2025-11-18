"""
Collective Communication Experiment Runner

Runs both scenarios:
- Scenario A: Protected collectives (priority 7, background priority 0-2)
- Scenario B: Unprotected collectives (same priority as background)
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

from priority_stream_simulator import Network, Stream
from topology.tree_topology import TreeTopology
from collectives.patterns import CollectivePatterns
import os


class CollectiveExperiment:
    """
    Runs collective communication experiments with different priority scenarios.
    """

    def __init__(self,
                 sim_duration: float = 5.0,
                 collective_msg_size: int = 1000,
                 collective_interval: float = 0.05,  # 50ms
                 background_msg_size: int = 1500,
                 background_interval: float = 0.03):  # 30ms (higher rate)
        """
        Initialize experiment parameters.

        Args:
            sim_duration: Simulation duration in seconds
            collective_msg_size: Message size for collective traffic
            collective_interval: Interval between collective messages
            background_msg_size: Message size for background traffic
            background_interval: Interval between background messages
        """
        self.sim_duration = sim_duration
        self.collective_msg_size = collective_msg_size
        self.collective_interval = collective_interval
        self.background_msg_size = background_msg_size
        self.background_interval = background_interval

    def _add_background_traffic(self, network: Network, topology: TreeTopology,
                                priority: int, base_stream_id: int):
        """
        Add background traffic to create congestion.

        Background traffic: Random node pairs sending continuously
        """
        streams = []
        stream_id = base_stream_id

        # Create background traffic between node pairs
        # N0 -> N4, N1 -> N5, N2 -> N6, N3 -> N7 (cross-subtree traffic)
        pairs = [(0, 4), (1, 5), (2, 6), (3, 7)]

        for src_id, dst_id in pairs:
            src = f"N{src_id}"
            dst = f"N{dst_id}"

            stream = Stream(
                stream_id=stream_id,
                priority=priority,
                src_node=src,
                dst_node=dst,
                message_interval_sec=self.background_interval,
                message_size_bytes=self.background_msg_size,
                description=f"Background: {src}->{dst}"
            )
            streams.append(stream)
            stream_id += 1

            network.add_stream(stream)
            topology.nodes[src].add_stream(stream, start_time=0.01)

        print(f"  Added {len(streams)} background traffic streams (priority {priority})")
        return streams

    def run_scenario_a(self, collective_type: str, output_dir: str):
        """
        Run Scenario A: Protected Collectives

        - Collective traffic: Priority 7 (highest)
        - Background traffic: Priority 1 (low)
        """
        print("\n" + "="*70)
        print(f"SCENARIO A: PROTECTED {collective_type.upper()}")
        print("="*70)
        print("Collective priority: 7 (PROTECTED)")
        print("Background priority: 1 (LOW)")
        print()

        # Create network and topology
        network = Network(sim_duration=self.sim_duration)
        topology = TreeTopology(network, switch_queue_size=50).build()

        # Generate collective pattern
        patterns = CollectivePatterns(topology.get_node_names(), base_stream_id=1000)

        if collective_type == "all-to-all":
            coll_streams = patterns.all_to_all(
                priority=7,  # PROTECTED
                message_size_bytes=self.collective_msg_size,
                interval_sec=self.collective_interval,
                description="All-to-All-Protected"
            )
        elif collective_type == "all-reduce":
            coll_streams = patterns.all_reduce(
                priority=7,  # PROTECTED
                message_size_bytes=self.collective_msg_size,
                interval_sec=self.collective_interval,
                description="All-Reduce-Protected"
            )
        else:
            raise ValueError(f"Unknown collective type: {collective_type}")

        # Add collective streams to network
        for stream in coll_streams:
            network.add_stream(stream)
            topology.nodes[stream.src_node].add_stream(stream, start_time=0.0)

        # Add background traffic (low priority)
        bg_streams = self._add_background_traffic(network, topology,
                                                  priority=1,  # LOW
                                                  base_stream_id=5000)

        # Run simulation
        print()
        network.run()

        # Save results
        csv_file = os.path.join(output_dir, f"scenario_a_{collective_type}.csv")
        network.export_to_csv(csv_file)

        print()
        self._print_results(network, coll_streams, bg_streams)

        return network, coll_streams, bg_streams

    def run_scenario_b(self, collective_type: str, output_dir: str):
        """
        Run Scenario B: Unprotected Collectives

        - Collective traffic: Priority 3 (medium)
        - Background traffic: Priority 3 (same as collective)
        """
        print("\n" + "="*70)
        print(f"SCENARIO B: UNPROTECTED {collective_type.upper()}")
        print("="*70)
        print("Collective priority: 3 (MEDIUM)")
        print("Background priority: 3 (SAME - NO PROTECTION)")
        print()

        # Create network and topology
        network = Network(sim_duration=self.sim_duration)
        topology = TreeTopology(network, switch_queue_size=50).build()

        # Generate collective pattern
        patterns = CollectivePatterns(topology.get_node_names(), base_stream_id=1000)

        if collective_type == "all-to-all":
            coll_streams = patterns.all_to_all(
                priority=3,  # UNPROTECTED - same as background
                message_size_bytes=self.collective_msg_size,
                interval_sec=self.collective_interval,
                description="All-to-All-Unprotected"
            )
        elif collective_type == "all-reduce":
            coll_streams = patterns.all_reduce(
                priority=3,  # UNPROTECTED - same as background
                message_size_bytes=self.collective_msg_size,
                interval_sec=self.collective_interval,
                description="All-Reduce-Unprotected"
            )
        else:
            raise ValueError(f"Unknown collective type: {collective_type}")

        # Add collective streams to network
        for stream in coll_streams:
            network.add_stream(stream)
            topology.nodes[stream.src_node].add_stream(stream, start_time=0.0)

        # Add background traffic (same priority)
        bg_streams = self._add_background_traffic(network, topology,
                                                  priority=3,  # SAME as collective
                                                  base_stream_id=5000)

        # Run simulation
        print()
        network.run()

        # Save results
        csv_file = os.path.join(output_dir, f"scenario_b_{collective_type}.csv")
        network.export_to_csv(csv_file)

        print()
        self._print_results(network, coll_streams, bg_streams)

        return network, coll_streams, bg_streams

    def _print_results(self, network, coll_streams, bg_streams):
        """Print summary results."""
        print("="*70)
        print("RESULTS SUMMARY")
        print("="*70)

        # Global stats
        global_stats = network.get_global_statistics()
        print(f"\nGlobal Statistics:")
        print(f"  Total delivered: {global_stats['total_messages_delivered']}")
        print(f"  Total dropped: {global_stats['total_messages_dropped']}")

        # Collective stats
        coll_stream_ids = [s.stream_id for s in coll_streams]
        coll_total = 0
        coll_dropped = 0
        coll_delays = []

        for sid in coll_stream_ids:
            stats = network.get_stream_statistics(sid)
            coll_total += stats['total_messages']
            coll_dropped += stats['dropped_messages']
            if stats['total_messages'] > 0:
                coll_delays.append(stats['mean_delay_ms'])

        coll_drop_rate = (coll_dropped / (coll_total + coll_dropped) * 100) if (coll_total + coll_dropped) > 0 else 0
        coll_mean_delay = sum(coll_delays) / len(coll_delays) if coll_delays else 0

        print(f"\nCollective Traffic:")
        print(f"  Streams: {len(coll_streams)}")
        print(f"  Messages delivered: {coll_total}")
        print(f"  Messages dropped: {coll_dropped}")
        print(f"  Drop rate: {coll_drop_rate:.2f}%")
        print(f"  Mean delay: {coll_mean_delay:.3f} ms")

        # Background stats
        bg_stream_ids = [s.stream_id for s in bg_streams]
        bg_total = 0
        bg_dropped = 0
        bg_delays = []

        for sid in bg_stream_ids:
            stats = network.get_stream_statistics(sid)
            bg_total += stats['total_messages']
            bg_dropped += stats['dropped_messages']
            if stats['total_messages'] > 0:
                bg_delays.append(stats['mean_delay_ms'])

        bg_drop_rate = (bg_dropped / (bg_total + bg_dropped) * 100) if (bg_total + bg_dropped) > 0 else 0
        bg_mean_delay = sum(bg_delays) / len(bg_delays) if bg_delays else 0

        print(f"\nBackground Traffic:")
        print(f"  Streams: {len(bg_streams)}")
        print(f"  Messages delivered: {bg_total}")
        print(f"  Messages dropped: {bg_dropped}")
        print(f"  Drop rate: {bg_drop_rate:.2f}%")
        print(f"  Mean delay: {bg_mean_delay:.3f} ms")

        print("="*70 + "\n")


def main():
    """Run all experiments."""
    # Create output directories
    results_dir = "../results"
    os.makedirs(f"{results_dir}/scenario_a", exist_ok=True)
    os.makedirs(f"{results_dir}/scenario_b", exist_ok=True)

    # Initialize experiment
    experiment = CollectiveExperiment(
        sim_duration=5.0,
        collective_msg_size=1000,
        collective_interval=0.05,
        background_msg_size=1500,
        background_interval=0.03
    )

    # Run experiments for each collective type
    collectives = ["all-to-all", "all-reduce"]

    for collective_type in collectives:
        print("\n" + "#"*70)
        print(f"# EXPERIMENT: {collective_type.upper()}")
        print("#"*70)

        # Scenario A: Protected
        experiment.run_scenario_a(collective_type, f"{results_dir}/scenario_a")

        # Scenario B: Unprotected
        experiment.run_scenario_b(collective_type, f"{results_dir}/scenario_b")

    print("\n" + "="*70)
    print("ALL EXPERIMENTS COMPLETED")
    print("="*70)
    print(f"\nResults saved to:")
    print(f"  {results_dir}/scenario_a/")
    print(f"  {results_dir}/scenario_b/")


if __name__ == "__main__":
    main()
