"""
Collective Communication Patterns

Implements common collective operations:
- All-to-All: Each node sends to every other node
- All-Reduce: Tree-based reduction then broadcast
"""

import sys
sys.path.append('/Users/mubarakojewale/Documents/MLSys-Experiments')

from priority_stream_simulator import Stream
from typing import List, Dict


class CollectivePatterns:
    """
    Generator for collective communication patterns.

    Each collective generates a set of streams representing
    the communication pattern.
    """

    def __init__(self, node_names: List[str], base_stream_id: int = 1000):
        """
        Initialize collective patterns.

        Args:
            node_names: List of participating node names (e.g., ['N0', 'N1', ...])
            base_stream_id: Starting stream ID for collective streams
        """
        self.node_names = node_names
        self.num_nodes = len(node_names)
        self.base_stream_id = base_stream_id
        self.next_stream_id = base_stream_id

    def _get_stream_id(self) -> int:
        """Get next unique stream ID."""
        sid = self.next_stream_id
        self.next_stream_id += 1
        return sid

    def all_to_all(self,
                   priority: int,
                   message_size_bytes: int = 1000,
                   interval_sec: float = 0.1,
                   description: str = "All-to-All") -> List[Stream]:
        """
        Generate All-to-All communication pattern.

        Each of N nodes sends to every other N-1 nodes.
        Total streams: N * (N-1)

        Args:
            priority: Priority level for all streams
            message_size_bytes: Size of each message
            interval_sec: Interval between messages
            description: Collective description

        Returns:
            List of Stream objects representing the pattern
        """
        streams = []

        for src in self.node_names:
            for dst in self.node_names:
                if src != dst:  # Don't send to self
                    stream = Stream(
                        stream_id=self._get_stream_id(),
                        priority=priority,
                        src_node=src,
                        dst_node=dst,
                        message_interval_sec=interval_sec,
                        message_size_bytes=message_size_bytes,
                        description=f"{description}: {src}->{dst}"
                    )
                    streams.append(stream)

        print(f"All-to-All: Generated {len(streams)} streams "
              f"({self.num_nodes} nodes * {self.num_nodes-1} destinations)")
        return streams

    def all_reduce(self,
                   priority: int,
                   message_size_bytes: int = 1000,
                   interval_sec: float = 0.1,
                   description: str = "All-Reduce") -> List[Stream]:
        """
        Generate All-Reduce communication pattern.

        Implements tree-based all-reduce:
        1. Reduce phase: Data flows up the tree to root
        2. Broadcast phase: Result flows down from root to all nodes

        For 8 nodes (N0-N7) in a binary tree:
        - Reduce: Leaves send to parents, parents aggregate and send up
        - Broadcast: Root sends to children, children forward down

        Simplified model:
        - Bottom level (N0-N7) sends to aggregation level
        - Aggregation level reduces and sends to root
        - Root broadcasts back through aggregation to all nodes

        Args:
            priority: Priority level for all streams
            message_size_bytes: Size of each message
            interval_sec: Interval between messages
            description: Collective description

        Returns:
            List of Stream objects representing the pattern
        """
        streams = []

        # Phase 1: REDUCE - All nodes send to root (N0 chosen as logical root)
        # In practice, this goes through the network topology
        root = self.node_names[0]

        for src in self.node_names:
            if src != root:
                stream = Stream(
                    stream_id=self._get_stream_id(),
                    priority=priority,
                    src_node=src,
                    dst_node=root,
                    message_interval_sec=interval_sec,
                    message_size_bytes=message_size_bytes,
                    description=f"{description}-Reduce: {src}->{root}"
                )
                streams.append(stream)

        # Phase 2: BROADCAST - Root sends to all other nodes
        for dst in self.node_names:
            if dst != root:
                stream = Stream(
                    stream_id=self._get_stream_id(),
                    priority=priority,
                    src_node=root,
                    dst_node=dst,
                    message_interval_sec=interval_sec,
                    message_size_bytes=message_size_bytes,
                    description=f"{description}-Broadcast: {root}->{dst}"
                )
                streams.append(stream)

        print(f"All-Reduce: Generated {len(streams)} streams "
              f"({self.num_nodes-1} reduce + {self.num_nodes-1} broadcast)")
        return streams

    def hierarchical_all_to_all(self,
                                 priority: int,
                                 message_size_bytes: int = 1000,
                                 interval_sec: float = 0.1,
                                 description: str = "Hierarchical-All-to-All",
                                 nodes_per_rack: int = 4) -> List[Stream]:
        """
        Generate Hierarchical All-to-All communication pattern.

        Optimized for rack-based topologies:
        1. Intra-rack: All-to-all within each rack
        2. Inter-rack: Each rack representative talks to other rack representatives
        3. Distribution: Representatives distribute remote rack data locally

        For 8 nodes with 2 racks (N0-N3 in Rack0, N4-N7 in Rack1):
        - Phase 1: N0-N3 all-to-all, N4-N7 all-to-all (local)
        - Phase 2: N0 ↔ N4 (rack representatives exchange)
        - Phase 3: Representatives distribute to local nodes

        Args:
            priority: Priority level for all streams
            message_size_bytes: Size of each message
            interval_sec: Interval between messages
            description: Collective description
            nodes_per_rack: Number of nodes per rack

        Returns:
            List of Stream objects representing the hierarchical pattern
        """
        streams = []
        num_racks = self.num_nodes // nodes_per_rack

        # Organize nodes into racks
        racks = []
        for rack_id in range(num_racks):
            start_idx = rack_id * nodes_per_rack
            end_idx = start_idx + nodes_per_rack
            rack_nodes = self.node_names[start_idx:end_idx]
            racks.append(rack_nodes)

        # Phase 1: Intra-rack all-to-all
        for rack_id, rack_nodes in enumerate(racks):
            for src in rack_nodes:
                for dst in rack_nodes:
                    if src != dst:
                        stream = Stream(
                            stream_id=self._get_stream_id(),
                            priority=priority,
                            src_node=src,
                            dst_node=dst,
                            message_interval_sec=interval_sec,
                            message_size_bytes=message_size_bytes,
                            description=f"{description}-IntraRack{rack_id}: {src}->{dst}"
                        )
                        streams.append(stream)

        # Phase 2: Inter-rack communication (representatives)
        # Use first node of each rack as representative
        representatives = [rack[0] for rack in racks]

        for src_rep in representatives:
            for dst_rep in representatives:
                if src_rep != dst_rep:
                    stream = Stream(
                        stream_id=self._get_stream_id(),
                        priority=priority,
                        src_node=src_rep,
                        dst_node=dst_rep,
                        message_interval_sec=interval_sec,
                        message_size_bytes=message_size_bytes,
                        description=f"{description}-InterRack: {src_rep}->{dst_rep}"
                    )
                    streams.append(stream)

        # Phase 3: Local distribution from representatives
        for rack_id, rack_nodes in enumerate(racks):
            representative = rack_nodes[0]
            for dst in rack_nodes[1:]:  # Skip representative itself
                stream = Stream(
                    stream_id=self._get_stream_id(),
                    priority=priority,
                    src_node=representative,
                    dst_node=dst,
                    message_interval_sec=interval_sec,
                    message_size_bytes=message_size_bytes,
                    description=f"{description}-LocalDist{rack_id}: {representative}->{dst}"
                )
                streams.append(stream)

        print(f"Hierarchical All-to-All: Generated {len(streams)} streams "
              f"({num_racks} racks, {nodes_per_rack} nodes/rack)")
        return streams

    def hierarchical_all_reduce(self,
                                 priority: int,
                                 message_size_bytes: int = 1000,
                                 interval_sec: float = 0.1,
                                 description: str = "Hierarchical-All-Reduce",
                                 nodes_per_rack: int = 4) -> List[Stream]:
        """
        Generate Hierarchical All-Reduce communication pattern.

        Optimized for rack-based topologies:
        1. Local reduce: Nodes reduce within each rack
        2. Global reduce: Rack representatives perform cross-rack reduce
        3. Global broadcast: Result sent to all rack representatives
        4. Local broadcast: Representatives broadcast to local nodes

        For 8 nodes with 2 racks (N0-N3 in Rack0, N4-N7 in Rack1):
        - Phase 1: N1,N2,N3 → N0 (local reduce to rack0 rep)
                   N5,N6,N7 → N4 (local reduce to rack1 rep)
        - Phase 2: N4 → N0 (global reduce at root representative)
        - Phase 3: N0 → N4 (broadcast to other representatives)
        - Phase 4: N0 → N1,N2,N3 and N4 → N5,N6,N7 (local broadcast)

        Args:
            priority: Priority level for all streams
            message_size_bytes: Size of each message
            interval_sec: Interval between messages
            description: Collective description
            nodes_per_rack: Number of nodes per rack

        Returns:
            List of Stream objects representing the hierarchical pattern
        """
        streams = []
        num_racks = self.num_nodes // nodes_per_rack

        # Organize nodes into racks
        racks = []
        for rack_id in range(num_racks):
            start_idx = rack_id * nodes_per_rack
            end_idx = start_idx + nodes_per_rack
            rack_nodes = self.node_names[start_idx:end_idx]
            racks.append(rack_nodes)

        # Phase 1: Local reduce within each rack
        # All nodes in rack send to rack representative (first node)
        for rack_id, rack_nodes in enumerate(racks):
            representative = rack_nodes[0]
            for src in rack_nodes[1:]:  # Other nodes in rack
                stream = Stream(
                    stream_id=self._get_stream_id(),
                    priority=priority,
                    src_node=src,
                    dst_node=representative,
                    message_interval_sec=interval_sec,
                    message_size_bytes=message_size_bytes,
                    description=f"{description}-LocalReduce{rack_id}: {src}->{representative}"
                )
                streams.append(stream)

        # Phase 2: Global reduce across racks
        # All rack representatives send to global root (first rack's representative)
        global_root = racks[0][0]
        for rack_id in range(1, num_racks):
            representative = racks[rack_id][0]
            stream = Stream(
                stream_id=self._get_stream_id(),
                priority=priority,
                src_node=representative,
                dst_node=global_root,
                message_interval_sec=interval_sec,
                message_size_bytes=message_size_bytes,
                description=f"{description}-GlobalReduce: {representative}->{global_root}"
            )
            streams.append(stream)

        # Phase 3: Global broadcast to all rack representatives
        for rack_id in range(1, num_racks):
            representative = racks[rack_id][0]
            stream = Stream(
                stream_id=self._get_stream_id(),
                priority=priority,
                src_node=global_root,
                dst_node=representative,
                message_interval_sec=interval_sec,
                message_size_bytes=message_size_bytes,
                description=f"{description}-GlobalBcast: {global_root}->{representative}"
            )
            streams.append(stream)

        # Phase 4: Local broadcast within each rack
        for rack_id, rack_nodes in enumerate(racks):
            representative = rack_nodes[0]
            for dst in rack_nodes[1:]:  # Other nodes in rack
                stream = Stream(
                    stream_id=self._get_stream_id(),
                    priority=priority,
                    src_node=representative,
                    dst_node=dst,
                    message_interval_sec=interval_sec,
                    message_size_bytes=message_size_bytes,
                    description=f"{description}-LocalBcast{rack_id}: {representative}->{dst}"
                )
                streams.append(stream)

        phase1 = (nodes_per_rack - 1) * num_racks  # Local reduces
        phase2 = num_racks - 1  # Global reduce
        phase3 = num_racks - 1  # Global broadcast
        phase4 = (nodes_per_rack - 1) * num_racks  # Local broadcasts

        print(f"Hierarchical All-Reduce: Generated {len(streams)} streams "
              f"(LocalRed:{phase1} + GlobalRed:{phase2} + GlobalBcast:{phase3} + LocalBcast:{phase4})")
        return streams

    def get_stream_info(self, streams: List[Stream]) -> Dict:
        """Get summary information about a set of streams."""
        if not streams:
            return {}

        total_msgs = len(streams)
        priorities = set(s.priority for s in streams)
        src_nodes = set(s.src_node for s in streams)
        dst_nodes = set(s.dst_node for s in streams)

        return {
            'total_streams': total_msgs,
            'priorities': sorted(priorities),
            'participating_nodes': len(src_nodes.union(dst_nodes)),
            'message_size': streams[0].message_size_bytes if streams else 0,
            'interval': streams[0].message_interval_sec if streams else 0
        }


def test_collectives():
    """Test collective pattern generation."""
    nodes = [f"N{i}" for i in range(8)]
    patterns = CollectivePatterns(nodes)

    print("\n" + "="*70)
    print("COLLECTIVE COMMUNICATION PATTERNS TEST")
    print("="*70 + "\n")

    # Test All-to-All
    print("1. ALL-TO-ALL PATTERN")
    print("-" * 70)
    a2a_streams = patterns.all_to_all(priority=7, message_size_bytes=1000)
    info = patterns.get_stream_info(a2a_streams)
    print(f"   Total streams: {info['total_streams']}")
    print(f"   Priorities: {info['priorities']}")
    print(f"   Expected: 8 * 7 = 56 streams")
    print()

    # Reset stream IDs for next pattern
    patterns.next_stream_id = 2000

    # Test All-Reduce
    print("2. ALL-REDUCE PATTERN")
    print("-" * 70)
    ar_streams = patterns.all_reduce(priority=7, message_size_bytes=1000)
    info = patterns.get_stream_info(ar_streams)
    print(f"   Total streams: {info['total_streams']}")
    print(f"   Priorities: {info['priorities']}")
    print(f"   Expected: 7 reduce + 7 broadcast = 14 streams")
    print()

    # Show sample streams
    print("3. SAMPLE STREAMS")
    print("-" * 70)
    print("All-to-All (first 5):")
    for stream in a2a_streams[:5]:
        print(f"   Stream {stream.stream_id}: {stream.src_node} -> {stream.dst_node}")
    print()

    print("All-Reduce (all):")
    for stream in ar_streams:
        phase = "Reduce" if stream.dst_node == "N0" else "Broadcast"
        print(f"   Stream {stream.stream_id}: {stream.src_node} -> {stream.dst_node} ({phase})")

    print("\n" + "="*70)


if __name__ == "__main__":
    test_collectives()
