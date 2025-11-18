"""
Ring Topology Builder for Collective Communication Experiments

Builds a hybrid ring topology:
- 8 compute nodes
- 4 ring switches forming a bidirectional ring
- Each switch connects to 2 compute nodes

Topology Structure:
    N0   N1         N2   N3
     \   /          \   /
      S0 ----------- S1
      |              |
      |              |
      S3 ----------- S2
     /   \          /   \
    N7   N6        N5   N4
"""

import sys
sys.path.append('/Users/mubarakojewale/Documents/MLSys-Experiments')

from priority_stream_simulator import Network, Link
from typing import Dict, List


class RingTopology:
    """
    Ring topology for collective communication experiments.

    Structure:
    - 8 compute nodes
    - 4 switches arranged in a ring
    - Each switch connects to 2 nodes
    - Total: 8 nodes, 4 switches, 16 links (8 access + 8 ring)
    """

    def __init__(self,
                 network: Network,
                 link_bw_mbps: float = 1000,
                 link_delay_ms: float = 0.5,
                 switch_queue_size: int = 100):
        """
        Initialize ring topology.

        Args:
            network: Network simulator instance
            link_bw_mbps: Bandwidth for ring links
            link_delay_ms: Delay for ring links
            switch_queue_size: Queue size for switches
        """
        self.network = network
        self.link_bw = link_bw_mbps
        self.link_delay = link_delay_ms
        self.queue_size = switch_queue_size

        # Topology elements
        self.nodes: Dict[str, object] = {}
        self.switches: Dict[str, object] = {}
        self.links: Dict[str, Link] = {}

    def build(self):
        """Build the ring topology."""
        print("Building ring topology...")
        print(f"  - 8 compute nodes")
        print(f"  - 4 ring switches")
        print(f"  - Ring links: {self.link_bw} Mbps, {self.link_delay} ms")

        # Create 4 switches in a ring
        for i in range(4):
            switch_name = f"S{i}"
            self.switches[switch_name] = self.network.add_switch(switch_name, self.queue_size)

        # Create 8 compute nodes (N0-N7)
        for i in range(8):
            node_name = f"N{i}"
            self.nodes[node_name] = self.network.add_node(node_name)

        # Create ring links between switches
        self._create_ring_links()

        # Create access links (nodes to switches)
        self._create_access_links()

        # Configure forwarding tables
        self._configure_forwarding()

        print("Topology built successfully!")
        return self

    def _create_ring_links(self):
        """Create bidirectional links between adjacent switches in the ring."""
        for i in range(4):
            current_sw = f"S{i}"
            next_sw = f"S{(i + 1) % 4}"  # Wrap around for ring

            # Link: current -> next (clockwise)
            link_cw = Link(f'{current_sw}->{next_sw}',
                          bandwidth_mbps=self.link_bw,
                          delay_ms=self.link_delay)
            self.links[f'{current_sw}->{next_sw}'] = link_cw
            self.switches[current_sw].add_link(next_sw, link_cw)

            # Link: next -> current (counterclockwise)
            link_ccw = Link(f'{next_sw}->{current_sw}',
                           bandwidth_mbps=self.link_bw,
                           delay_ms=self.link_delay)
            self.links[f'{next_sw}->{current_sw}'] = link_ccw
            self.switches[next_sw].add_link(current_sw, link_ccw)

    def _create_access_links(self):
        """Create links between nodes and switches."""
        # N0, N1 connect to S0
        # N2, N3 connect to S1
        # N4, N5 connect to S2
        # N6, N7 connect to S3
        for i in range(8):
            node_name = f"N{i}"
            switch_id = i // 2  # 0,1->S0; 2,3->S1; 4,5->S2; 6,7->S3
            switch_name = f"S{switch_id}"

            # Node -> Switch
            link_up = Link(f'{node_name}->{switch_name}',
                          bandwidth_mbps=self.link_bw,
                          delay_ms=self.link_delay)
            self.links[f'{node_name}->{switch_name}'] = link_up
            self.nodes[node_name].set_output_link(link_up)
            self.nodes[node_name].set_next_hop(switch_name)

            # Switch -> Node
            link_down = Link(f'{switch_name}->{node_name}',
                            bandwidth_mbps=self.link_bw,
                            delay_ms=self.link_delay)
            self.links[f'{switch_name}->{node_name}'] = link_down
            self.switches[switch_name].add_link(node_name, link_down)

    def _configure_forwarding(self):
        """Configure forwarding tables for shortest path routing in the ring."""
        # For each switch, configure forwarding to all nodes using shortest path

        for src_sw_id in range(4):
            src_sw = f"S{src_sw_id}"

            for dst_id in range(8):
                dst_node = f"N{dst_id}"
                dst_sw_id = dst_id // 2

                if src_sw_id == dst_sw_id:
                    # Destination node is directly connected
                    self.switches[src_sw].set_forwarding_entry(dst_node, dst_node)
                else:
                    # Forward to next switch on shortest path
                    # Calculate clockwise and counterclockwise distances
                    cw_distance = (dst_sw_id - src_sw_id) % 4
                    ccw_distance = (src_sw_id - dst_sw_id) % 4

                    if cw_distance <= ccw_distance:
                        # Go clockwise
                        next_hop = f"S{(src_sw_id + 1) % 4}"
                    else:
                        # Go counterclockwise
                        next_hop = f"S{(src_sw_id - 1) % 4}"

                    self.switches[src_sw].set_forwarding_entry(dst_node, next_hop)

    def get_node_names(self) -> List[str]:
        """Get list of all compute node names."""
        return [f"N{i}" for i in range(8)]

    def print_topology(self):
        """Print topology structure."""
        print("\n" + "="*70)
        print("RING TOPOLOGY STRUCTURE")
        print("="*70)
        print("\n    N0   N1         N2   N3")
        print("     \\   /          \\   /")
        print("      S0 ----------- S1")
        print("      |              |")
        print("      |              |")
        print("      S3 ----------- S2")
        print("     /   \\          /   \\")
        print("    N7   N6        N5   N4")
        print("\n" + "="*70)
        print(f"Total nodes: {len(self.nodes)}")
        print(f"Total switches: {len(self.switches)}")
        print(f"Total links: {len(self.links)}")
        print("="*70 + "\n")


def test_topology():
    """Test the ring topology."""
    from priority_stream_simulator import Network

    network = Network(sim_duration=1.0)
    topology = RingTopology(network)
    topology.build()
    topology.print_topology()


if __name__ == "__main__":
    test_topology()
