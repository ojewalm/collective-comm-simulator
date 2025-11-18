"""
Tree Topology Builder for Collective Communication Experiments

Builds a hierarchical tree topology:
- 8 end nodes (compute nodes)
- 3 switches (1 root + 2 aggregation)
- Realistic hierarchical structure

Topology Structure:
                    Root Switch
                    /         \
        Aggregation SW0    Aggregation SW1
           /    |   \  \      /   |   \   \
        N0   N1  N2  N3    N4   N5  N6  N7
"""

import sys
sys.path.append('/Users/mubarakojewale/Documents/MLSys-Experiments')

from priority_stream_simulator import Network, Link
from typing import Dict, List


class TreeTopology:
    """
    Tree topology for collective communication experiments.

    Structure:
    - Root switch connects 2 aggregation switches
    - Each aggregation switch connects 4 end nodes
    - Total: 8 nodes, 3 switches
    """

    def __init__(self,
                 network: Network,
                 access_bw_mbps: float = 1000,     # Node <-> Agg switch
                 aggregation_bw_mbps: float = 2000, # Agg <-> Root switch
                 access_delay_ms: float = 0.5,
                 aggregation_delay_ms: float = 1.0,
                 switch_queue_size: int = 100):
        """
        Initialize tree topology.

        Args:
            network: Network simulator instance
            access_bw_mbps: Bandwidth for access links (node to agg switch)
            aggregation_bw_mbps: Bandwidth for aggregation links (agg to root)
            access_delay_ms: Delay for access links
            aggregation_delay_ms: Delay for aggregation links
            switch_queue_size: Queue size for each switch
        """
        self.network = network
        self.access_bw = access_bw_mbps
        self.agg_bw = aggregation_bw_mbps
        self.access_delay = access_delay_ms
        self.agg_delay = aggregation_delay_ms
        self.queue_size = switch_queue_size

        # Topology elements
        self.nodes: Dict[str, object] = {}
        self.switches: Dict[str, object] = {}
        self.links: Dict[str, Link] = {}

    def build(self):
        """Build the tree topology."""
        print("Building tree topology...")
        print(f"  - 8 compute nodes")
        print(f"  - 3 switches (1 root + 2 aggregation)")
        print(f"  - Access links: {self.access_bw} Mbps, {self.access_delay} ms")
        print(f"  - Aggregation links: {self.agg_bw} Mbps, {self.agg_delay} ms")

        # Create switches
        self.switches['Root'] = self.network.add_switch('Root', self.queue_size)
        self.switches['Agg0'] = self.network.add_switch('Agg0', self.queue_size)
        self.switches['Agg1'] = self.network.add_switch('Agg1', self.queue_size)

        # Create 8 compute nodes (N0-N7)
        for i in range(8):
            node_name = f"N{i}"
            self.nodes[node_name] = self.network.add_node(node_name)

        # Create links: Aggregation switches <-> Root
        self._create_aggregation_links()

        # Create links: Nodes <-> Aggregation switches
        self._create_access_links()

        # Configure forwarding tables
        self._configure_forwarding()

        print("Topology built successfully!")
        return self

    def _create_aggregation_links(self):
        """Create links between aggregation and root switches."""
        # Bidirectional links: Agg0 <-> Root
        self.links['Agg0->Root'] = Link('Agg0->Root',
                                         bandwidth_mbps=self.agg_bw,
                                         delay_ms=self.agg_delay)
        self.links['Root->Agg0'] = Link('Root->Agg0',
                                         bandwidth_mbps=self.agg_bw,
                                         delay_ms=self.agg_delay)

        # Bidirectional links: Agg1 <-> Root
        self.links['Agg1->Root'] = Link('Agg1->Root',
                                         bandwidth_mbps=self.agg_bw,
                                         delay_ms=self.agg_delay)
        self.links['Root->Agg1'] = Link('Root->Agg1',
                                         bandwidth_mbps=self.agg_bw,
                                         delay_ms=self.agg_delay)

        # Configure aggregation switch output ports
        self.switches['Agg0'].add_link('Root', self.links['Agg0->Root'])
        self.switches['Agg1'].add_link('Root', self.links['Agg1->Root'])
        self.switches['Root'].add_link('Agg0', self.links['Root->Agg0'])
        self.switches['Root'].add_link('Agg1', self.links['Root->Agg1'])

    def _create_access_links(self):
        """Create links between nodes and aggregation switches."""
        # N0-N3 connect to Agg0
        for i in range(4):
            node_name = f"N{i}"

            # Node -> Agg0
            link_up = Link(f'{node_name}->Agg0',
                          bandwidth_mbps=self.access_bw,
                          delay_ms=self.access_delay)
            self.links[f'{node_name}->Agg0'] = link_up
            self.nodes[node_name].set_output_link(link_up)
            self.nodes[node_name].set_next_hop('Agg0')

            # Agg0 -> Node
            link_down = Link(f'Agg0->{node_name}',
                            bandwidth_mbps=self.access_bw,
                            delay_ms=self.access_delay)
            self.links[f'Agg0->{node_name}'] = link_down
            self.switches['Agg0'].add_link(node_name, link_down)

        # N4-N7 connect to Agg1
        for i in range(4, 8):
            node_name = f"N{i}"

            # Node -> Agg1
            link_up = Link(f'{node_name}->Agg1',
                          bandwidth_mbps=self.access_bw,
                          delay_ms=self.access_delay)
            self.links[f'{node_name}->Agg1'] = link_up
            self.nodes[node_name].set_output_link(link_up)
            self.nodes[node_name].set_next_hop('Agg1')

            # Agg1 -> Node
            link_down = Link(f'Agg1->{node_name}',
                            bandwidth_mbps=self.access_bw,
                            delay_ms=self.access_delay)
            self.links[f'Agg1->{node_name}'] = link_down
            self.switches['Agg1'].add_link(node_name, link_down)

    def _configure_forwarding(self):
        """Configure forwarding tables for all switches."""
        # Root switch forwarding
        # N0-N3 go to Agg0
        for i in range(4):
            self.switches['Root'].set_forwarding_entry(f"N{i}", 'Agg0')
        # N4-N7 go to Agg1
        for i in range(4, 8):
            self.switches['Root'].set_forwarding_entry(f"N{i}", 'Agg1')

        # Agg0 forwarding
        # N0-N3 are directly connected
        for i in range(4):
            self.switches['Agg0'].set_forwarding_entry(f"N{i}", f"N{i}")
        # N4-N7 go through Root
        for i in range(4, 8):
            self.switches['Agg0'].set_forwarding_entry(f"N{i}", 'Root')

        # Agg1 forwarding
        # N4-N7 are directly connected
        for i in range(4, 8):
            self.switches['Agg1'].set_forwarding_entry(f"N{i}", f"N{i}")
        # N0-N3 go through Root
        for i in range(4):
            self.switches['Agg1'].set_forwarding_entry(f"N{i}", 'Root')

    def get_node_names(self) -> List[str]:
        """Get list of all compute node names."""
        return [f"N{i}" for i in range(8)]

    def print_topology(self):
        """Print topology structure."""
        print("\n" + "="*70)
        print("TREE TOPOLOGY STRUCTURE")
        print("="*70)
        print("\n                         Root")
        print("                       /      \\")
        print("                   Agg0        Agg1")
        print("                 / | \\ \\      / | \\ \\")
        print("                N0 N1 N2 N3  N4 N5 N6 N7")
        print("\n" + "="*70)
        print(f"Total nodes: {len(self.nodes)}")
        print(f"Total switches: {len(self.switches)}")
        print(f"Total links: {len(self.links)}")
        print("="*70 + "\n")


def test_topology():
    """Test the tree topology."""
    from priority_stream_simulator import Network

    network = Network(sim_duration=1.0)
    topology = TreeTopology(network)
    topology.build()
    topology.print_topology()


if __name__ == "__main__":
    test_topology()
