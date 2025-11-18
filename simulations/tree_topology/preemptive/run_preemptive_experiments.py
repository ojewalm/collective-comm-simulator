"""
Preemptive Collective Communication Experiment Runner

Runs experiments with frame preemption support:
- Protected mode: Preemption enabled (high-priority can interrupt low-priority)
- Unprotected mode: Preemption disabled (standard priority scheduling)

Compares frame preemption vs strict priority scheduling.
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

from priority_stream_simulator import Network, Link, Stream
from collectives.patterns import CollectivePatterns
from switch.preemptive_switch import PreemptiveSwitch
import os


class PreemptiveTreeTopology:
    """
    Tree topology using PreemptiveSwitch.

    Same structure as standard tree but with preemption capability.
    """

    def __init__(self,
                 network: Network,
                 preemption_enabled: bool = True,
                 access_bw_mbps: float = 1000,
                 aggregation_bw_mbps: float = 2000,
                 access_delay_ms: float = 0.5,
                 aggregation_delay_ms: float = 1.0,
                 switch_queue_size: int = 100):
        """
        Initialize preemptive tree topology.

        Args:
            network: Network simulator instance
            preemption_enabled: Enable frame preemption
            access_bw_mbps: Bandwidth for access links
            aggregation_bw_mbps: Bandwidth for aggregation links
            access_delay_ms: Delay for access links
            aggregation_delay_ms: Delay for aggregation links
            switch_queue_size: Queue size for each switch
        """
        self.network = network
        self.preemption_enabled = preemption_enabled
        self.access_bw = access_bw_mbps
        self.agg_bw = aggregation_bw_mbps
        self.access_delay = access_delay_ms
        self.agg_delay = aggregation_delay_ms
        self.queue_size = switch_queue_size

        self.nodes = {}
        self.switches = {}
        self.links = {}

    def build(self):
        """Build the tree topology with preemptive switches."""
        mode_str = "WITH PREEMPTION" if self.preemption_enabled else "WITHOUT PREEMPTION"
        print(f"Building tree topology {mode_str}...")
        print(f"  - 8 compute nodes")
        print(f"  - 3 preemptive switches")
        print(f"  - Preemption: {'ENABLED' if self.preemption_enabled else 'DISABLED'}")

        # Create preemptive switches and register with network
        self.switches['Root'] = PreemptiveSwitch('Root', self.network, self.queue_size, self.preemption_enabled)
        self.switches['Agg0'] = PreemptiveSwitch('Agg0', self.network, self.queue_size, self.preemption_enabled)
        self.switches['Agg1'] = PreemptiveSwitch('Agg1', self.network, self.queue_size, self.preemption_enabled)

        # Register switches with network so deliver_message works
        self.network.switches['Root'] = self.switches['Root']
        self.network.switches['Agg0'] = self.switches['Agg0']
        self.network.switches['Agg1'] = self.switches['Agg1']

        # Create 8 compute nodes
        for i in range(8):
            node_name = f"N{i}"
            self.nodes[node_name] = self.network.add_node(node_name)

        # Create links
        self._create_aggregation_links()
        self._create_access_links()
        self._configure_forwarding()

        print("Topology built successfully!")
        return self

    def _create_aggregation_links(self):
        """Create links between aggregation and root switches."""
        # Agg0 <-> Root
        self.links['Agg0->Root'] = Link('Agg0->Root', self.agg_bw, self.agg_delay)
        self.links['Root->Agg0'] = Link('Root->Agg0', self.agg_bw, self.agg_delay)

        # Agg1 <-> Root
        self.links['Agg1->Root'] = Link('Agg1->Root', self.agg_bw, self.agg_delay)
        self.links['Root->Agg1'] = Link('Root->Agg1', self.agg_bw, self.agg_delay)

        # Configure switch ports
        self.switches['Agg0'].add_link('Root', self.links['Agg0->Root'])
        self.switches['Agg1'].add_link('Root', self.links['Agg1->Root'])
        self.switches['Root'].add_link('Agg0', self.links['Root->Agg0'])
        self.switches['Root'].add_link('Agg1', self.links['Root->Agg1'])

    def _create_access_links(self):
        """Create links between nodes and aggregation switches."""
        # N0-N3 connect to Agg0
        for i in range(4):
            node_name = f"N{i}"
            link_up = Link(f'{node_name}->Agg0', self.access_bw, self.access_delay)
            link_down = Link(f'Agg0->{node_name}', self.access_bw, self.access_delay)

            self.links[f'{node_name}->Agg0'] = link_up
            self.links[f'Agg0->{node_name}'] = link_down

            self.nodes[node_name].set_output_link(link_up)
            self.nodes[node_name].set_next_hop('Agg0')
            self.switches['Agg0'].add_link(node_name, link_down)

        # N4-N7 connect to Agg1
        for i in range(4, 8):
            node_name = f"N{i}"
            link_up = Link(f'{node_name}->Agg1', self.access_bw, self.access_delay)
            link_down = Link(f'Agg1->{node_name}', self.access_bw, self.access_delay)

            self.links[f'{node_name}->Agg1'] = link_up
            self.links[f'Agg1->{node_name}'] = link_down

            self.nodes[node_name].set_output_link(link_up)
            self.nodes[node_name].set_next_hop('Agg1')
            self.switches['Agg1'].add_link(node_name, link_down)

    def _configure_forwarding(self):
        """Configure forwarding tables."""
        # Root switch
        for i in range(4):
            self.switches['Root'].set_forwarding_entry(f"N{i}", 'Agg0')
        for i in range(4, 8):
            self.switches['Root'].set_forwarding_entry(f"N{i}", 'Agg1')

        # Agg0 switch
        for i in range(4):
            self.switches['Agg0'].set_forwarding_entry(f"N{i}", f"N{i}")
        for i in range(4, 8):
            self.switches['Agg0'].set_forwarding_entry(f"N{i}", 'Root')

        # Agg1 switch
        for i in range(4, 8):
            self.switches['Agg1'].set_forwarding_entry(f"N{i}", f"N{i}")
        for i in range(4):
            self.switches['Agg1'].set_forwarding_entry(f"N{i}", 'Root')

    def get_node_names(self):
        """Get list of compute node names."""
        return [f"N{i}" for i in range(8)]


class PreemptiveExperiment:
    """
    Runs preemptive collective communication experiments.
    """

    def __init__(self,
                 sim_duration: float = 5.0,
                 collective_msg_size: int = 1000,
                 collective_interval: float = 0.05,
                 background_msg_size: int = 1500,
                 background_interval: float = 0.03):
        """Initialize experiment parameters."""
        self.sim_duration = sim_duration
        self.collective_msg_size = collective_msg_size
        self.collective_interval = collective_interval
        self.background_msg_size = background_msg_size
        self.background_interval = background_interval

    def _add_background_traffic(self, network, topology, priority, base_stream_id):
        """Add background traffic streams."""
        streams = []
        stream_id = base_stream_id

        # Cross-subtree traffic
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

    def run_protected(self, collective_type: str, output_dir: str):
        """
        Run Protected Mode: Preemption ENABLED.

        High-priority collectives can preempt low-priority background.
        """
        print("\n" + "="*70)
        print(f"PROTECTED MODE: {collective_type.upper()} WITH PREEMPTION")
        print("="*70)
        print("Collective priority: 7 (CAN PREEMPT)")
        print("Background priority: 1 (CAN BE PREEMPTED)")
        print("Preemption: ENABLED")
        print()

        # Create network with preemptive topology
        network = Network(sim_duration=self.sim_duration)
        topology = PreemptiveTreeTopology(
            network,
            preemption_enabled=True,  # PREEMPTION ON
            switch_queue_size=50
        ).build()

        # Generate collective pattern
        patterns = CollectivePatterns(topology.get_node_names(), base_stream_id=1000)

        if collective_type == "all-to-all":
            coll_streams = patterns.all_to_all(
                priority=7,  # HIGH - can preempt
                message_size_bytes=self.collective_msg_size,
                interval_sec=self.collective_interval,
                description="All-to-All-Preemptive"
            )
        elif collective_type == "all-reduce":
            coll_streams = patterns.all_reduce(
                priority=7,  # HIGH - can preempt
                message_size_bytes=self.collective_msg_size,
                interval_sec=self.collective_interval,
                description="All-Reduce-Preemptive"
            )
        else:
            raise ValueError(f"Unknown collective type: {collective_type}")

        # Add collective streams
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
        csv_file = os.path.join(output_dir, f"protected_{collective_type}.csv")
        network.export_to_csv(csv_file)

        print()
        self._print_results(network, topology, coll_streams, bg_streams)

        return network, topology, coll_streams, bg_streams

    def run_unprotected(self, collective_type: str, output_dir: str):
        """
        Run Unprotected Mode: Preemption DISABLED.

        Standard priority scheduling, no mid-transmission interruption.
        """
        print("\n" + "="*70)
        print(f"UNPROTECTED MODE: {collective_type.upper()} WITHOUT PREEMPTION")
        print("="*70)
        print("Collective priority: 7 (CANNOT PREEMPT)")
        print("Background priority: 1 (CANNOT BE PREEMPTED)")
        print("Preemption: DISABLED (standard priority scheduling)")
        print()

        # Create network with non-preemptive topology
        network = Network(sim_duration=self.sim_duration)
        topology = PreemptiveTreeTopology(
            network,
            preemption_enabled=False,  # PREEMPTION OFF
            switch_queue_size=50
        ).build()

        # Generate collective pattern
        patterns = CollectivePatterns(topology.get_node_names(), base_stream_id=1000)

        if collective_type == "all-to-all":
            coll_streams = patterns.all_to_all(
                priority=7,  # HIGH but can't preempt
                message_size_bytes=self.collective_msg_size,
                interval_sec=self.collective_interval,
                description="All-to-All-NonPreemptive"
            )
        elif collective_type == "all-reduce":
            coll_streams = patterns.all_reduce(
                priority=7,  # HIGH but can't preempt
                message_size_bytes=self.collective_msg_size,
                interval_sec=self.collective_interval,
                description="All-Reduce-NonPreemptive"
            )
        else:
            raise ValueError(f"Unknown collective type: {collective_type}")

        # Add collective streams
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
        csv_file = os.path.join(output_dir, f"unprotected_{collective_type}.csv")
        network.export_to_csv(csv_file)

        print()
        self._print_results(network, topology, coll_streams, bg_streams)

        return network, topology, coll_streams, bg_streams

    def _print_results(self, network, topology, coll_streams, bg_streams):
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

        # Preemption stats
        print(f"\nPreemption Statistics:")
        for name, switch in topology.switches.items():
            pstats = switch.get_preemption_statistics()
            print(f"  {name}:")
            print(f"    Preemption enabled: {pstats['preemption_enabled']}")
            print(f"    Total preemptions: {pstats['total_preemptions']}")
            if pstats['total_preemptions'] > 0:
                print(f"    Avg overhead per preemption: {pstats['avg_overhead_per_preemption_ms']:.3f} ms")

        print("="*70 + "\n")


def main():
    """Run all preemptive experiments."""
    # Create output directories
    results_dir = "../results"
    os.makedirs(f"{results_dir}/protected", exist_ok=True)
    os.makedirs(f"{results_dir}/unprotected", exist_ok=True)

    # Initialize experiment
    experiment = PreemptiveExperiment(
        sim_duration=5.0,
        collective_msg_size=1000,
        collective_interval=0.05,
        background_msg_size=1500,
        background_interval=0.03
    )

    # Run experiments
    collectives = ["all-to-all", "all-reduce"]

    for collective_type in collectives:
        print("\n" + "#"*70)
        print(f"# PREEMPTIVE EXPERIMENT: {collective_type.upper()}")
        print("#"*70)

        # Protected mode (preemption ON)
        experiment.run_protected(collective_type, f"{results_dir}/protected")

        # Unprotected mode (preemption OFF)
        experiment.run_unprotected(collective_type, f"{results_dir}/unprotected")

    print("\n" + "="*70)
    print("ALL PREEMPTIVE EXPERIMENTS COMPLETED")
    print("="*70)
    print(f"\nResults saved to:")
    print(f"  {results_dir}/protected/")
    print(f"  {results_dir}/unprotected/")


if __name__ == "__main__":
    main()
