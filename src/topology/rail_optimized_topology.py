"""
Rail-Optimized Topology Builder for Collective Communication Experiments

Builds a 2-rack topology with direct inter-rack connectivity:
- 8 compute nodes (4 per rack)
- 2 ToR (Top of Rack) switches
- Direct link between ToR switches (rail-optimized)

Topology Structure:
    N0  N1  N2  N3        N4  N5  N6  N7
     \  |   |  /          \  |   |  /
      \  \ /  /            \  \ /  /
         ToR0 ------------- ToR1
       (Rack 0)           (Rack 1)
"""

import sys
sys.path.append('/Users/mubarakojewale/Documents/MLSys-Experiments')

from priority_stream_simulator import Network, Link
from typing import Dict, List


class RailOptimizedTopology:
    """
    Rail-optimized topology for collective communication experiments.

    Structure:
    - 8 compute nodes split into 2 racks (4 nodes each)
    - 2 ToR switches (one per rack)
    - Direct high-bandwidth link between ToR switches
    - Total: 8 nodes, 2 switches, 10 links
    """

    def __init__(self,
                 network: Network,
                 access_bw_mbps: float = 1000,      # Node <-> ToR
                 inter_rack_bw_mbps: float = 2000,  # ToR <-> ToR
                 access_delay_ms: float = 0.5,
                 inter_rack_delay_ms: float = 1.0,
                 switch_queue_size: int = 100):
        """
        Initialize rail-optimized topology.

        Args:
            network: Network simulator instance
            access_bw_mbps: Bandwidth for access links (node to ToR)
            inter_rack_bw_mbps: Bandwidth for inter-rack link (ToR to ToR)
            access_delay_ms: Delay for access links
            inter_rack_delay_ms: Delay for inter-rack link
            switch_queue_size: Queue size for each switch
        """
        self.network = network
        self.access_bw = access_bw_mbps
        self.inter_rack_bw = inter_rack_bw_mbps
        self.access_delay = access_delay_ms
        self.inter_rack_delay = inter_rack_delay_ms
        self.queue_size = switch_queue_size

        # Topology elements
        self.nodes: Dict[str, object] = {}
        self.switches: Dict[str, object] = {}
        self.links: Dict[str, Link] = {}

    def build(self):
        """Build the rail-optimized topology."""
        print("Building rail-optimized topology...")
        print(f"  - 8 compute nodes (2 racks, 4 nodes each)")
        print(f"  - 2 ToR switches")
        print(f"  - Access links: {self.access_bw} Mbps, {self.access_delay} ms")
        print(f"  - Inter-rack link: {self.inter_rack_bw} Mbps, {self.inter_rack_delay} ms")

        # Create 2 ToR switches
        self.switches['ToR0'] = self.network.add_switch('ToR0', self.queue_size)
        self.switches['ToR1'] = self.network.add_switch('ToR1', self.queue_size)

        # Create 8 compute nodes (N0-N7)
        for i in range(8):
            node_name = f"N{i}"
            self.nodes[node_name] = self.network.add_node(node_name)

        # Create inter-rack link between ToR switches
        self._create_inter_rack_links()

        # Create access links (nodes to ToR switches)
        self._create_access_links()

        # Configure forwarding tables
        self._configure_forwarding()

        print("Topology built successfully!")
        return self

    def _create_inter_rack_links(self):
        """Create bidirectional link between ToR switches."""
        # ToR0 <-> ToR1
        self.links['ToR0->ToR1'] = Link('ToR0->ToR1',
                                        bandwidth_mbps=self.inter_rack_bw,
                                        delay_ms=self.inter_rack_delay)
        self.links['ToR1->ToR0'] = Link('ToR1->ToR0',
                                        bandwidth_mbps=self.inter_rack_bw,
                                        delay_ms=self.inter_rack_delay)

        # Configure inter-rack switch ports
        self.switches['ToR0'].add_link('ToR1', self.links['ToR0->ToR1'])
        self.switches['ToR1'].add_link('ToR0', self.links['ToR1->ToR0'])

    def _create_access_links(self):
        """Create links between nodes and ToR switches."""
        # N0-N3 connect to ToR0 (Rack 0)
        for i in range(4):
            node_name = f"N{i}"

            # Node -> ToR0
            link_up = Link(f'{node_name}->ToR0',
                          bandwidth_mbps=self.access_bw,
                          delay_ms=self.access_delay)
            self.links[f'{node_name}->ToR0'] = link_up
            self.nodes[node_name].set_output_link(link_up)
            self.nodes[node_name].set_next_hop('ToR0')

            # ToR0 -> Node
            link_down = Link(f'ToR0->{node_name}',
                            bandwidth_mbps=self.access_bw,
                            delay_ms=self.access_delay)
            self.links[f'ToR0->{node_name}'] = link_down
            self.switches['ToR0'].add_link(node_name, link_down)

        # N4-N7 connect to ToR1 (Rack 1)
        for i in range(4, 8):
            node_name = f"N{i}"

            # Node -> ToR1
            link_up = Link(f'{node_name}->ToR1',
                          bandwidth_mbps=self.access_bw,
                          delay_ms=self.access_delay)
            self.links[f'{node_name}->ToR1'] = link_up
            self.nodes[node_name].set_output_link(link_up)
            self.nodes[node_name].set_next_hop('ToR1')

            # ToR1 -> Node
            link_down = Link(f'ToR1->{node_name}',
                            bandwidth_mbps=self.access_bw,
                            delay_ms=self.access_delay)
            self.links[f'ToR1->{node_name}'] = link_down
            self.switches['ToR1'].add_link(node_name, link_down)

    def _configure_forwarding(self):
        """Configure forwarding tables for all switches."""
        # ToR0 forwarding
        # N0-N3 are directly connected
        for i in range(4):
            self.switches['ToR0'].set_forwarding_entry(f"N{i}", f"N{i}")
        # N4-N7 go through ToR1
        for i in range(4, 8):
            self.switches['ToR0'].set_forwarding_entry(f"N{i}", 'ToR1')

        # ToR1 forwarding
        # N4-N7 are directly connected
        for i in range(4, 8):
            self.switches['ToR1'].set_forwarding_entry(f"N{i}", f"N{i}")
        # N0-N3 go through ToR0
        for i in range(4):
            self.switches['ToR1'].set_forwarding_entry(f"N{i}", 'ToR0')

    def get_node_names(self) -> List[str]:
        """Get list of all compute node names."""
        return [f"N{i}" for i in range(8)]

    def print_topology(self):
        """Print topology structure."""
        print("\n" + "="*70)
        print("RAIL-OPTIMIZED TOPOLOGY STRUCTURE")
        print("="*70)
        print("\n    N0  N1  N2  N3        N4  N5  N6  N7")
        print("     \\  |   |  /          \\  |   |  /")
        print("      \\  \\ /  /            \\  \\ /  /")
        print("         ToR0 ------------- ToR1")
        print("       (Rack 0)           (Rack 1)")
        print("\n" + "="*70)
        print(f"Total nodes: {len(self.nodes)}")
        print(f"Total switches: {len(self.switches)}")
        print(f"Total links: {len(self.links)}")
        print("="*70 + "\n")


def test_topology():
    """Test the rail-optimized topology."""
    from priority_stream_simulator import Network

    network = Network(sim_duration=1.0)
    topology = RailOptimizedTopology(network)
    topology.build()
    topology.print_topology()


if __name__ == "__main__":
    test_topology()
