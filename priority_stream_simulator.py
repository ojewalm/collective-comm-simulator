"""
Priority-Based Stream Network Simulator

Extended discrete-event network simulator with:
- Stream-based traffic with priority levels (0-7)
- Strict priority scheduling at switches
- Per-stream metrics and visualization
"""

import heapq
import csv
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import deque, defaultdict
import time


@dataclass(order=True)
class Event:
    """
    Simulation event with priority ordering by time.

    Attributes:
        time: Event timestamp (simulation time in seconds)
        priority: Used to break ties when events have same time
        action: Callable to execute when event fires
        description: Human-readable event description
    """
    time: float
    priority: int = 0
    action: object = field(compare=False, default=None)
    description: str = field(compare=False, default="")


@dataclass
class Stream:
    """
    Traffic stream with priority.

    Attributes:
        stream_id: Unique stream identifier
        priority: Priority level (0-7, where 7 is highest)
        src_node: Source node
        dst_node: Destination node
        message_interval_sec: Time between messages
        message_size_bytes: Size of each message
        description: Human-readable stream description
    """
    stream_id: int
    priority: int  # 0-7, where 7 is highest
    src_node: str
    dst_node: str
    message_interval_sec: float
    message_size_bytes: int
    description: str = ""

    def __post_init__(self):
        """Validate priority level."""
        if not 0 <= self.priority <= 7:
            raise ValueError(f"Priority must be between 0 and 7, got {self.priority}")


@dataclass
class Message:
    """
    Network message/packet with stream and timing information.

    Attributes:
        msg_id: Unique message identifier
        stream_id: Stream this message belongs to
        seq_num: Sequence number within stream
        priority: Message priority (inherited from stream)
        src_node: Source node ID
        dst_node: Destination node ID
        size_bytes: Message size in bytes
        creation_time: Time when message was generated
        transmission_start_time: Time when transmission began
        arrival_time: Time when message arrived at destination
        dropped: Whether message was dropped
        drop_reason: Reason for drop (if any)
    """
    msg_id: int
    stream_id: int
    seq_num: int
    priority: int  # 0-7
    src_node: str
    dst_node: str
    size_bytes: int
    creation_time: float
    transmission_start_time: Optional[float] = None
    arrival_time: Optional[float] = None
    dropped: bool = False
    drop_reason: str = ""

    def get_end_to_end_delay(self) -> Optional[float]:
        """Calculate total delay from creation to arrival."""
        if self.arrival_time is not None and not self.dropped:
            return self.arrival_time - self.creation_time
        return None


class Link:
    """
    Network link with bandwidth and propagation delay.

    Models a point-to-point connection between two network elements
    with realistic bandwidth constraints and propagation delay.
    """

    def __init__(self, name: str, bandwidth_mbps: float, delay_ms: float):
        """
        Initialize a network link.

        Args:
            name: Link identifier
            bandwidth_mbps: Link bandwidth in Mbps
            delay_ms: Propagation delay in milliseconds
        """
        self.name = name
        self.bandwidth_bps = bandwidth_mbps * 1_000_000  # Convert to bps
        self.delay_sec = delay_ms / 1000.0  # Convert to seconds
        self.busy_until = 0.0  # Time when link becomes available

    def get_transmission_time(self, size_bytes: int) -> float:
        """Calculate time to transmit a message of given size."""
        size_bits = size_bytes * 8
        return size_bits / self.bandwidth_bps

    def is_busy(self, current_time: float) -> bool:
        """Check if link is currently transmitting."""
        return current_time < self.busy_until

    def start_transmission(self, current_time: float, size_bytes: int) -> float:
        """
        Start transmitting a message.

        Returns:
            Time when message will arrive at other end of link
        """
        # Wait if link is busy
        start_time = max(current_time, self.busy_until)
        transmission_time = self.get_transmission_time(size_bytes)
        self.busy_until = start_time + transmission_time

        # Total time = transmission + propagation delay
        arrival_time = self.busy_until + self.delay_sec
        return arrival_time


class PriorityQueue:
    """
    Priority queue manager with 8 priority levels (0-7).

    Implements strict priority scheduling: always serve highest
    priority non-empty queue first, FIFO within each priority.

    Supports priority-aware dropping: when full, can drop lowest
    priority message to make room for higher priority arrivals.
    """

    def __init__(self):
        """Initialize 8 priority queues."""
        self.queues: Dict[int, deque] = {i: deque() for i in range(8)}
        self.total_size = 0

    def enqueue(self, message: Message, output_port: str):
        """Add message to appropriate priority queue."""
        priority = message.priority
        self.queues[priority].append((message, output_port))
        self.total_size += 1

    def dequeue(self) -> Optional[Tuple[Message, str]]:
        """
        Remove and return highest priority message.

        Returns:
            (message, output_port) tuple, or None if all queues empty
        """
        # Check from highest priority (7) to lowest (0)
        for priority in range(7, -1, -1):
            if self.queues[priority]:
                self.total_size -= 1
                return self.queues[priority].popleft()
        return None

    def get_lowest_priority_message(self) -> Optional[Tuple[int, Message, str]]:
        """
        Find and return the lowest priority message in the queue.

        Returns:
            (priority, message, output_port) tuple, or None if queue empty
        """
        # Check from lowest priority (0) to highest (7)
        for priority in range(0, 8):
            if self.queues[priority]:
                # Return but don't remove
                message, output_port = self.queues[priority][-1]  # Get last (oldest in this priority)
                return (priority, message, output_port)
        return None

    def drop_lowest_priority_message(self) -> Optional[Message]:
        """
        Remove and return the lowest priority message.
        Used for priority-based preemption when queue is full.

        Returns:
            Dropped message, or None if queue empty
        """
        # Check from lowest priority (0) to highest (7)
        for priority in range(0, 8):
            if self.queues[priority]:
                message, _ = self.queues[priority].pop()  # Remove last (FIFO tail drop)
                self.total_size -= 1
                return message
        return None

    def is_empty(self) -> bool:
        """Check if all priority queues are empty."""
        return self.total_size == 0

    def get_queue_lengths(self) -> Dict[int, int]:
        """Get length of each priority queue."""
        return {i: len(self.queues[i]) for i in range(8)}


class Switch:
    """
    Network switch with priority-based FIFO queuing and forwarding.

    Maintains 8 separate queues per output port (one per priority level).
    Uses strict priority scheduling: always serves highest priority queue first.
    """

    def __init__(self, name: str, network: 'Network', max_queue_size: Optional[int] = None):
        """
        Initialize a network switch.

        Args:
            name: Switch identifier
            network: Reference to the network for event scheduling
            max_queue_size: Maximum total queue size (None = unlimited)
        """
        self.name = name
        self.network = network
        self.max_queue_size = max_queue_size
        self.priority_queue = PriorityQueue()
        self.forwarding_table: Dict[str, str] = {}  # dst_node -> output_port
        self.output_links: Dict[str, Link] = {}  # port_name -> Link
        self.is_transmitting = False

        # Statistics
        self.messages_received = 0
        self.messages_forwarded = 0
        self.messages_dropped = 0
        self.drops_by_priority: Dict[int, int] = defaultdict(int)

    def add_link(self, port_name: str, link: Link):
        """Add an output link to a port."""
        self.output_links[port_name] = link

    def set_forwarding_entry(self, dst_node: str, output_port: str):
        """Configure forwarding table entry."""
        self.forwarding_table[dst_node] = output_port

    def receive_message(self, message: Message, current_time: float):
        """
        Receive a message at the switch.

        Enqueues the message in appropriate priority queue and triggers
        forwarding if not busy.
        """
        self.messages_received += 1

        # Determine output port
        output_port = self.forwarding_table.get(message.dst_node)
        if output_port is None:
            print(f"Warning: No forwarding entry for {message.dst_node}")
            message.dropped = True
            message.drop_reason = "No forwarding entry"
            self.messages_dropped += 1
            self.network.track_dropped_message(message)
            return

        # Check queue capacity
        if self.max_queue_size is not None:
            if self.priority_queue.total_size >= self.max_queue_size:
                # Queue is full - use priority-aware dropping
                lowest = self.priority_queue.get_lowest_priority_message()

                if lowest is not None:
                    lowest_priority, lowest_msg, _ = lowest

                    # If incoming message has higher priority than lowest in queue,
                    # drop the lowest and accept the new message
                    if message.priority > lowest_priority:
                        dropped_msg = self.priority_queue.drop_lowest_priority_message()
                        if dropped_msg:
                            dropped_msg.dropped = True
                            dropped_msg.drop_reason = "Preempted by higher priority"
                            self.messages_dropped += 1
                            self.drops_by_priority[dropped_msg.priority] += 1
                            self.network.track_dropped_message(dropped_msg)
                            # Continue to enqueue the new higher-priority message
                    else:
                        # Incoming message has equal or lower priority - drop it
                        message.dropped = True
                        message.drop_reason = "Buffer overflow (tail drop)"
                        self.messages_dropped += 1
                        self.drops_by_priority[message.priority] += 1
                        self.network.track_dropped_message(message)
                        return
                else:
                    # Queue full but no message found (shouldn't happen)
                    message.dropped = True
                    message.drop_reason = "Buffer overflow"
                    self.messages_dropped += 1
                    self.drops_by_priority[message.priority] += 1
                    self.network.track_dropped_message(message)
                    return

        # Enqueue message in appropriate priority queue
        self.priority_queue.enqueue(message, output_port)

        # Try to forward if not currently transmitting
        if not self.is_transmitting:
            self.forward_next_message(current_time)

    def forward_next_message(self, current_time: float):
        """Forward the next highest-priority message in the queue."""
        if self.priority_queue.is_empty():
            self.is_transmitting = False
            return

        self.is_transmitting = True
        result = self.priority_queue.dequeue()

        if result is None:
            self.is_transmitting = False
            return

        message, output_port = result

        # Get the output link
        link = self.output_links.get(output_port)
        if link is None:
            print(f"Warning: No link on port {output_port}")
            self.is_transmitting = False
            return

        # Start transmission on the link
        arrival_time = link.start_transmission(current_time, message.size_bytes)
        self.messages_forwarded += 1

        # Schedule message arrival at destination
        self.network.schedule_event(
            arrival_time,
            lambda: self.network.deliver_message(message, output_port),
            f"Message {message.msg_id} (stream {message.stream_id}, pri {message.priority}) arrives at {output_port}"
        )

        # Schedule next forwarding attempt
        self.network.schedule_event(
            link.busy_until,
            lambda: self.forward_next_message(link.busy_until),
            f"Switch {self.name} ready for next message"
        )

    def get_queue_statistics(self) -> Dict:
        """Get current queue statistics."""
        return {
            'total_queued': self.priority_queue.total_size,
            'by_priority': self.priority_queue.get_queue_lengths(),
            'total_received': self.messages_received,
            'total_forwarded': self.messages_forwarded,
            'total_dropped': self.messages_dropped,
            'drops_by_priority': dict(self.drops_by_priority)
        }


class Node:
    """
    Network node that generates and receives stream-based messages.

    Can manage multiple traffic streams with different priorities.
    """

    def __init__(self, name: str, network: 'Network'):
        """
        Initialize a network node.

        Args:
            name: Node identifier
            network: Reference to the network for event scheduling
        """
        self.name = name
        self.network = network
        self.output_link: Optional[Link] = None

        # Stream management
        self.streams: Dict[int, Stream] = {}
        self.stream_seq_nums: Dict[int, int] = defaultdict(int)

        # Statistics
        self.messages_sent = 0
        self.messages_sent_by_stream: Dict[int, int] = defaultdict(int)
        self.messages_received: List[Message] = []
        self.messages_received_by_stream: Dict[int, List[Message]] = defaultdict(list)

    def set_output_link(self, link: Link):
        """Configure output link."""
        self.output_link = link

    def add_stream(self, stream: Stream, start_time: float = 0.0):
        """
        Add a traffic stream to this node.

        Args:
            stream: Stream configuration
            start_time: When to start generating traffic
        """
        if stream.src_node != self.name:
            raise ValueError(f"Stream source {stream.src_node} doesn't match node {self.name}")

        self.streams[stream.stream_id] = stream
        self.stream_seq_nums[stream.stream_id] = 0

        # Schedule first message
        self.network.schedule_event(
            start_time,
            lambda sid=stream.stream_id: self.generate_message(sid, start_time),
            f"Node {self.name} generates first message for stream {stream.stream_id}"
        )

    def generate_message(self, stream_id: int, current_time: float):
        """Generate and send a message for a specific stream."""
        if self.output_link is None:
            return

        stream = self.streams.get(stream_id)
        if stream is None:
            return

        # Create message
        seq_num = self.stream_seq_nums[stream_id]
        message = Message(
            msg_id=self.network.get_next_message_id(),
            stream_id=stream_id,
            seq_num=seq_num,
            priority=stream.priority,
            src_node=self.name,
            dst_node=stream.dst_node,
            size_bytes=stream.message_size_bytes,
            creation_time=current_time
        )
        self.stream_seq_nums[stream_id] += 1
        self.messages_sent += 1
        self.messages_sent_by_stream[stream_id] += 1

        # Send on output link
        arrival_time = self.output_link.start_transmission(
            current_time, message.size_bytes
        )
        message.transmission_start_time = max(
            current_time,
            self.output_link.busy_until - self.output_link.get_transmission_time(message.size_bytes)
        )

        # Schedule arrival at next hop
        # We need to determine the destination (switch or node)
        destination = stream.dst_node
        # If there's a switch in between, route to switch first
        if hasattr(self, '_next_hop'):
            destination = self._next_hop

        self.network.schedule_event(
            arrival_time,
            lambda: self.network.deliver_message(message, destination),
            f"Message {message.msg_id} from stream {stream_id} arrives at {destination}"
        )

        # Schedule next message generation
        next_time = current_time + stream.message_interval_sec
        if next_time < self.network.sim_duration:
            self.network.schedule_event(
                next_time,
                lambda sid=stream_id: self.generate_message(sid, next_time),
                f"Node {self.name} generates message for stream {stream_id}"
            )

    def receive_message(self, message: Message, current_time: float):
        """Receive a message at this node."""
        message.arrival_time = current_time
        self.messages_received.append(message)
        self.messages_received_by_stream[message.stream_id].append(message)

    def set_next_hop(self, next_hop: str):
        """Set the next hop for routing (typically a switch)."""
        self._next_hop = next_hop


class Network:
    """
    Network simulator that orchestrates discrete events.

    Manages the event queue, network topology, streams, and simulation execution.
    """

    def __init__(self, sim_duration: float):
        """
        Initialize the network simulator.

        Args:
            sim_duration: Total simulation time in seconds
        """
        self.sim_duration = sim_duration
        self.current_time = 0.0
        self.event_queue: List[Event] = []
        self.event_counter = 0  # For event priority ordering
        self.message_id_counter = 0

        # Network elements
        self.nodes: Dict[str, Node] = {}
        self.switches: Dict[str, Switch] = {}
        self.streams: Dict[int, Stream] = {}

        # Collected messages for logging
        self.completed_messages: List[Message] = []
        self.dropped_messages: List[Message] = []
        self.completed_by_stream: Dict[int, List[Message]] = defaultdict(list)

    def get_next_message_id(self) -> int:
        """Get next unique message ID."""
        msg_id = self.message_id_counter
        self.message_id_counter += 1
        return msg_id

    def add_node(self, name: str) -> Node:
        """Create and add a node to the network."""
        node = Node(name, self)
        self.nodes[name] = node
        return node

    def add_switch(self, name: str, max_queue_size: Optional[int] = None) -> Switch:
        """Create and add a switch to the network."""
        switch = Switch(name, self, max_queue_size)
        self.switches[name] = switch
        return switch

    def add_stream(self, stream: Stream):
        """Register a stream in the network."""
        self.streams[stream.stream_id] = stream

    def schedule_event(self, time: float, action, description: str = ""):
        """Schedule a new event."""
        event = Event(
            time=time,
            priority=self.event_counter,
            action=action,
            description=description
        )
        self.event_counter += 1
        heapq.heappush(self.event_queue, event)

    def deliver_message(self, message: Message, destination: str):
        """Deliver a message to its destination (node or switch)."""
        if destination in self.switches:
            # Message arrives at switch
            self.switches[destination].receive_message(message, self.current_time)
        elif destination in self.nodes:
            # Message arrives at destination node
            self.nodes[destination].receive_message(message, self.current_time)
            self.completed_messages.append(message)
            self.completed_by_stream[message.stream_id].append(message)
        else:
            print(f"Warning: Unknown destination {destination}")

    def track_dropped_message(self, message: Message):
        """Track a dropped message."""
        self.dropped_messages.append(message)

    def run(self):
        """Execute the simulation."""
        print(f"Starting simulation (duration: {self.sim_duration}s)...")
        start_wall_time = time.time()

        events_processed = 0
        while self.event_queue and self.current_time < self.sim_duration:
            event = heapq.heappop(self.event_queue)

            if event.time > self.sim_duration:
                break

            self.current_time = event.time

            # Execute event action
            if event.action is not None:
                event.action()

            events_processed += 1

        wall_time = time.time() - start_wall_time
        print(f"Simulation completed: {events_processed} events in {wall_time:.3f}s")
        print(f"Final simulation time: {self.current_time:.6f}s")

    def get_stream_statistics(self, stream_id: int) -> Dict:
        """Calculate statistics for a specific stream."""
        messages = self.completed_by_stream.get(stream_id, [])

        if not messages:
            return {
                'stream_id': stream_id,
                'priority': self.streams[stream_id].priority if stream_id in self.streams else None,
                'total_messages': 0,
                'dropped_messages': 0
            }

        delays = [msg.get_end_to_end_delay() for msg in messages]
        delays = [d for d in delays if d is not None]

        if not delays:
            return {
                'stream_id': stream_id,
                'priority': self.streams[stream_id].priority,
                'total_messages': len(messages),
                'dropped_messages': 0
            }

        # Calculate jitter
        jitter_values = []
        for i in range(1, len(delays)):
            jitter = abs(delays[i] - delays[i-1])
            jitter_values.append(jitter)

        # Calculate throughput (bytes/sec)
        if messages:
            time_span = messages[-1].arrival_time - messages[0].creation_time
            total_bytes = sum(msg.size_bytes for msg in messages)
            throughput_mbps = (total_bytes * 8 / time_span / 1_000_000) if time_span > 0 else 0
        else:
            throughput_mbps = 0

        # Count drops for this stream
        drops = sum(1 for msg in self.dropped_messages if msg.stream_id == stream_id)

        stats = {
            'stream_id': stream_id,
            'priority': self.streams[stream_id].priority,
            'total_messages': len(messages),
            'dropped_messages': drops,
            'mean_delay_ms': sum(delays) / len(delays) * 1000,
            'min_delay_ms': min(delays) * 1000,
            'max_delay_ms': max(delays) * 1000,
            'mean_jitter_ms': (sum(jitter_values) / len(jitter_values) * 1000) if jitter_values else 0,
            'throughput_mbps': throughput_mbps
        }

        return stats

    def get_global_statistics(self) -> Dict:
        """Calculate global network statistics."""
        all_delays = []
        for messages in self.completed_by_stream.values():
            delays = [msg.get_end_to_end_delay() for msg in messages]
            all_delays.extend([d for d in delays if d is not None])

        if not all_delays:
            return {}

        stats = {
            'total_messages_delivered': len(self.completed_messages),
            'total_messages_dropped': len(self.dropped_messages),
            'total_streams': len(self.streams),
            'mean_delay_ms': sum(all_delays) / len(all_delays) * 1000,
            'min_delay_ms': min(all_delays) * 1000,
            'max_delay_ms': max(all_delays) * 1000,
        }

        return stats

    def export_to_csv(self, filename: str):
        """Export per-message metrics to CSV."""
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'msg_id', 'stream_id', 'seq_num', 'priority',
                'src_node', 'dst_node', 'size_bytes',
                'creation_time', 'arrival_time', 'end_to_end_delay_ms',
                'dropped', 'drop_reason'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            # Write completed messages
            for msg in self.completed_messages:
                delay = msg.get_end_to_end_delay()
                writer.writerow({
                    'msg_id': msg.msg_id,
                    'stream_id': msg.stream_id,
                    'seq_num': msg.seq_num,
                    'priority': msg.priority,
                    'src_node': msg.src_node,
                    'dst_node': msg.dst_node,
                    'size_bytes': msg.size_bytes,
                    'creation_time': msg.creation_time,
                    'arrival_time': msg.arrival_time,
                    'end_to_end_delay_ms': delay * 1000 if delay else None,
                    'dropped': msg.dropped,
                    'drop_reason': msg.drop_reason
                })

            # Write dropped messages
            for msg in self.dropped_messages:
                writer.writerow({
                    'msg_id': msg.msg_id,
                    'stream_id': msg.stream_id,
                    'seq_num': msg.seq_num,
                    'priority': msg.priority,
                    'src_node': msg.src_node,
                    'dst_node': msg.dst_node,
                    'size_bytes': msg.size_bytes,
                    'creation_time': msg.creation_time,
                    'arrival_time': None,
                    'end_to_end_delay_ms': None,
                    'dropped': True,
                    'drop_reason': msg.drop_reason
                })

        print(f"Exported {len(self.completed_messages) + len(self.dropped_messages)} messages to {filename}")

    def visualize_per_stream(self, output_file: str = 'stream_metrics.png'):
        """Generate per-stream visualization of delay, throughput, jitter, and drops."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Warning: matplotlib not available, skipping visualization")
            return

        if not self.completed_messages:
            print("No messages to visualize")
            return

        # Sort streams by priority (highest first)
        sorted_streams = sorted(
            self.streams.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )

        num_streams = len(sorted_streams)
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Prepare data for each stream
        stream_ids = []
        stream_labels = []
        delays = []
        jitters = []
        throughputs = []
        drops = []

        for stream_id, stream in sorted_streams:
            stats = self.get_stream_statistics(stream_id)
            if stats['total_messages'] == 0:
                continue

            stream_ids.append(stream_id)
            stream_labels.append(f"S{stream_id}\nP{stream.priority}")
            delays.append(stats['mean_delay_ms'])
            jitters.append(stats['mean_jitter_ms'])
            throughputs.append(stats['throughput_mbps'])
            drops.append(stats['dropped_messages'])

        if not stream_ids:
            print("No stream data to visualize")
            return

        # Color map by priority
        colors = []
        for stream_id, _ in sorted_streams:
            if stream_id in stream_ids:
                priority = self.streams[stream_id].priority
                colors.append(plt.cm.RdYlGn(priority / 7.0))

        # Plot 1: Mean Delay
        ax1 = axes[0, 0]
        bars1 = ax1.bar(range(len(stream_ids)), delays, color=colors, edgecolor='black', linewidth=1.5)
        ax1.set_xlabel('Stream (Priority)', fontweight='bold')
        ax1.set_ylabel('Mean Delay (ms)', fontweight='bold')
        ax1.set_title('Mean End-to-End Delay per Stream', fontweight='bold')
        ax1.set_xticks(range(len(stream_ids)))
        ax1.set_xticklabels(stream_labels)
        ax1.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars1, delays)):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.2f}', ha='center', va='bottom', fontsize=9)

        # Plot 2: Mean Jitter
        ax2 = axes[0, 1]
        bars2 = ax2.bar(range(len(stream_ids)), jitters, color=colors, edgecolor='black', linewidth=1.5)
        ax2.set_xlabel('Stream (Priority)', fontweight='bold')
        ax2.set_ylabel('Mean Jitter (ms)', fontweight='bold')
        ax2.set_title('Mean Jitter per Stream', fontweight='bold')
        ax2.set_xticks(range(len(stream_ids)))
        ax2.set_xticklabels(stream_labels)
        ax2.grid(axis='y', alpha=0.3)

        for i, (bar, val) in enumerate(zip(bars2, jitters)):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.2f}', ha='center', va='bottom', fontsize=9)

        # Plot 3: Throughput
        ax3 = axes[1, 0]
        bars3 = ax3.bar(range(len(stream_ids)), throughputs, color=colors, edgecolor='black', linewidth=1.5)
        ax3.set_xlabel('Stream (Priority)', fontweight='bold')
        ax3.set_ylabel('Throughput (Mbps)', fontweight='bold')
        ax3.set_title('Throughput per Stream', fontweight='bold')
        ax3.set_xticks(range(len(stream_ids)))
        ax3.set_xticklabels(stream_labels)
        ax3.grid(axis='y', alpha=0.3)

        for i, (bar, val) in enumerate(zip(bars3, throughputs)):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.2f}', ha='center', va='bottom', fontsize=9)

        # Plot 4: Packet Drops
        ax4 = axes[1, 1]
        bars4 = ax4.bar(range(len(stream_ids)), drops, color=colors, edgecolor='black', linewidth=1.5)
        ax4.set_xlabel('Stream (Priority)', fontweight='bold')
        ax4.set_ylabel('Dropped Messages', fontweight='bold')
        ax4.set_title('Message Drops per Stream', fontweight='bold')
        ax4.set_xticks(range(len(stream_ids)))
        ax4.set_xticklabels(stream_labels)
        ax4.grid(axis='y', alpha=0.3)

        for i, (bar, val) in enumerate(zip(bars4, drops)):
            if val > 0:
                ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{int(val)}', ha='center', va='bottom', fontsize=9, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Per-stream visualization saved to {output_file}")
        plt.close()

    def visualize_delay_timeseries(self, output_file: str = 'delay_timeseries.png'):
        """Generate time-series plot of delays for each stream."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Warning: matplotlib not available, skipping visualization")
            return

        if not self.completed_messages:
            print("No messages to visualize")
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        # Sort streams by priority for legend ordering
        sorted_streams = sorted(
            self.streams.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )

        for stream_id, stream in sorted_streams:
            messages = self.completed_by_stream.get(stream_id, [])
            if not messages:
                continue

            times = [msg.creation_time for msg in messages]
            delays = [msg.get_end_to_end_delay() * 1000 for msg in messages]

            # Color based on priority
            color = plt.cm.RdYlGn(stream.priority / 7.0)
            ax.plot(times, delays, marker='o', markersize=3, linewidth=1.5,
                   label=f"Stream {stream_id} (P{stream.priority})", color=color, alpha=0.7)

        ax.set_xlabel('Simulation Time (s)', fontweight='bold')
        ax.set_ylabel('End-to-End Delay (ms)', fontweight='bold')
        ax.set_title('End-to-End Delay Over Time (Per Stream)', fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Delay time-series visualization saved to {output_file}")
        plt.close()


def main():
    """Run a priority-based stream simulation scenario."""
    # Simulation parameters
    SIM_DURATION = 10.0  # seconds

    # Create network
    network = Network(sim_duration=SIM_DURATION)

    print("Building priority-based stream network...")

    # Create topology: 3 nodes -> 1 switch (star topology)
    node1 = network.add_node("Node1")
    node2 = network.add_node("Node2")
    node3 = network.add_node("Node3")

    # Create switch with limited queue (to demonstrate drops)
    switch = network.add_switch("Switch1", max_queue_size=50)

    # Create links (100 Mbps, 1ms delay)
    link_n1_sw = Link("Node1->Switch", bandwidth_mbps=100, delay_ms=1)
    link_n2_sw = Link("Node2->Switch", bandwidth_mbps=100, delay_ms=1)
    link_n3_sw = Link("Node3->Switch", bandwidth_mbps=100, delay_ms=1)
    link_sw_n1 = Link("Switch->Node1", bandwidth_mbps=100, delay_ms=1)
    link_sw_n2 = Link("Switch->Node2", bandwidth_mbps=100, delay_ms=1)
    link_sw_n3 = Link("Switch->Node3", bandwidth_mbps=100, delay_ms=1)

    # Configure nodes
    node1.set_output_link(link_n1_sw)
    node1.set_next_hop("Switch1")
    node2.set_output_link(link_n2_sw)
    node2.set_next_hop("Switch1")
    node3.set_output_link(link_n3_sw)
    node3.set_next_hop("Switch1")

    # Configure switch
    switch.add_link("Node1", link_sw_n1)
    switch.add_link("Node2", link_sw_n2)
    switch.add_link("Node3", link_sw_n3)
    switch.set_forwarding_entry("Node1", "Node1")
    switch.set_forwarding_entry("Node2", "Node2")
    switch.set_forwarding_entry("Node3", "Node3")

    # Create streams with different priorities
    # High priority stream (Node1 -> Node2)
    stream1 = Stream(
        stream_id=1,
        priority=7,  # Highest priority
        src_node="Node1",
        dst_node="Node2",
        message_interval_sec=0.1,  # 100ms
        message_size_bytes=1500,
        description="High priority critical traffic"
    )

    # Medium priority stream (Node2 -> Node3)
    stream2 = Stream(
        stream_id=2,
        priority=4,  # Medium priority
        src_node="Node2",
        dst_node="Node3",
        message_interval_sec=0.08,  # 80ms
        message_size_bytes=1200,
        description="Medium priority business traffic"
    )

    # Low priority stream (Node3 -> Node1)
    stream3 = Stream(
        stream_id=3,
        priority=1,  # Low priority
        src_node="Node3",
        dst_node="Node1",
        message_interval_sec=0.05,  # 50ms (more frequent)
        message_size_bytes=2000,  # Larger messages
        description="Low priority bulk transfer"
    )

    # Additional low priority stream for congestion
    stream4 = Stream(
        stream_id=4,
        priority=0,  # Lowest priority
        src_node="Node1",
        dst_node="Node3",
        message_interval_sec=0.03,  # 30ms (very frequent)
        message_size_bytes=1800,
        description="Background traffic"
    )

    # Add streams to network
    network.add_stream(stream1)
    network.add_stream(stream2)
    network.add_stream(stream3)
    network.add_stream(stream4)

    # Start streams on nodes
    node1.add_stream(stream1, start_time=0.0)
    node2.add_stream(stream2, start_time=0.02)
    node3.add_stream(stream3, start_time=0.04)
    node1.add_stream(stream4, start_time=0.06)

    print(f"\nConfiguration:")
    print(f"  - 3 nodes connected to 1 switch (star topology)")
    print(f"  - Link bandwidth: 100 Mbps, delay: 1 ms")
    print(f"  - Switch queue size: 50 messages")
    print(f"  - 4 streams with priorities: 7, 4, 1, 0")
    print(f"  - Simulation duration: {SIM_DURATION} s")
    print()

    # Run simulation
    network.run()

    print()
    print("=" * 70)
    print("SIMULATION RESULTS")
    print("=" * 70)

    # Global statistics
    global_stats = network.get_global_statistics()
    if global_stats:
        print(f"\nGlobal Statistics:")
        print(f"  Total messages delivered: {global_stats['total_messages_delivered']}")
        print(f"  Total messages dropped: {global_stats['total_messages_dropped']}")
        print(f"  Total streams: {global_stats['total_streams']}")
        print(f"  Overall mean delay: {global_stats['mean_delay_ms']:.3f} ms")

    # Per-stream statistics
    print(f"\nPer-Stream Statistics:")
    print(f"{'Stream':<8} {'Priority':<10} {'Delivered':<12} {'Dropped':<10} {'Mean Delay':<12} {'Mean Jitter':<12} {'Throughput':<12}")
    print("-" * 86)

    for stream_id in sorted(network.streams.keys()):
        stats = network.get_stream_statistics(stream_id)
        if stats['total_messages'] > 0:
            print(f"{stream_id:<8} {stats['priority']:<10} {stats['total_messages']:<12} "
                  f"{stats['dropped_messages']:<10} {stats['mean_delay_ms']:<12.3f} "
                  f"{stats['mean_jitter_ms']:<12.3f} {stats['throughput_mbps']:<12.3f}")

    # Switch statistics
    print(f"\nSwitch Statistics:")
    for name, sw in network.switches.items():
        queue_stats = sw.get_queue_statistics()
        print(f"  {name}:")
        print(f"    Messages received: {queue_stats['total_received']}")
        print(f"    Messages forwarded: {queue_stats['total_forwarded']}")
        print(f"    Messages dropped: {queue_stats['total_dropped']}")
        if queue_stats['drops_by_priority']:
            print(f"    Drops by priority: {queue_stats['drops_by_priority']}")

    # Export results
    print()
    network.export_to_csv('priority_stream_simulation.csv')
    network.visualize_per_stream('stream_metrics.png')
    network.visualize_delay_timeseries('delay_timeseries.png')

    print()
    print("Simulation complete!")


if __name__ == "__main__":
    main()
