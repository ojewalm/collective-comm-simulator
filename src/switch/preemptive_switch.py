"""
Preemptive Switch Implementation

Extends the basic priority switch with frame preemption capabilities.

Frame Preemption:
- High-priority frames can interrupt (preempt) lower-priority frames mid-transmission
- Paused frames are resumed after the preempting frame completes
- Tracks partial transmission state for proper resumption
"""

import sys
sys.path.append('/Users/mubarakojewale/Documents/MLSys-Experiments')

from priority_stream_simulator import Switch as BaseSwitch, Link, Message
from typing import Optional, Tuple
from collections import defaultdict, deque


class PreemptiveSwitch(BaseSwitch):
    """
    Switch with frame preemption support.

    Extends basic priority switch to support mid-transmission interruption
    of lower-priority frames by higher-priority frames.

    Modes:
    - Preemption enabled: High-priority can interrupt low-priority
    - Preemption disabled: Behaves like standard priority switch
    """

    def __init__(self, name: str, network, max_queue_size: Optional[int] = None,
                 preemption_enabled: bool = True):
        """
        Initialize preemptive switch.

        Args:
            name: Switch identifier
            network: Reference to network for event scheduling
            max_queue_size: Maximum queue size
            preemption_enabled: Enable frame preemption (default: True)
        """
        super().__init__(name, network, max_queue_size)

        # Preemption configuration
        self.preemption_enabled = preemption_enabled
        self.min_preemption_interval = 0.001  # 1ms minimum between preemptions
        self.last_preemption_time = 0.0

        # Current transmission state
        self.current_transmission: Optional[dict] = None
        # Contains: {
        #   'message': Message,
        #   'output_port': str,
        #   'link': Link,
        #   'start_time': float,
        #   'bytes_transmitted': int,
        #   'bytes_remaining': int,
        #   'completion_time': float,
        #   'completion_event': event handle,
        #   'slot_event': event handle
        # }

        # Paused transmissions queue (FIX BUG #2: Use queue instead of single slot)
        self.paused_transmissions: deque = deque()

        # Statistics
        self.preemptions_count = 0
        self.preemptions_by_priority: dict = defaultdict(int)
        self.total_preemption_overhead_ms = 0.0

    def receive_message(self, message: Message, current_time: float):
        """
        Receive a message at the switch.

        With preemption enabled, may interrupt current transmission
        if incoming message has higher priority.

        Args:
            message: Incoming message
            current_time: Current simulation time
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

        # Check if we should preempt current transmission
        # FIX BUG #4: Limit preemption frequency to reduce overhead
        if self.preemption_enabled and self.current_transmission is not None:
            current_msg = self.current_transmission['message']

            # Only preempt if:
            # 1. Higher priority
            # 2. Enough time since last preemption
            # 3. Significant priority difference (>= 2 levels)
            time_since_last = current_time - self.last_preemption_time
            priority_diff = message.priority - current_msg.priority

            if (priority_diff >= 2 and
                time_since_last >= self.min_preemption_interval):
                self._preempt_current_transmission(current_time)
                self.last_preemption_time = current_time

        # Standard queue capacity check
        if self.max_queue_size is not None:
            if self.priority_queue.total_size >= self.max_queue_size:
                # Queue full - use priority-aware dropping
                lowest = self.priority_queue.get_lowest_priority_message()

                if lowest is not None:
                    lowest_priority, lowest_msg, _ = lowest

                    if message.priority > lowest_priority:
                        dropped_msg = self.priority_queue.drop_lowest_priority_message()
                        if dropped_msg:
                            dropped_msg.dropped = True
                            dropped_msg.drop_reason = "Preempted by higher priority"
                            self.messages_dropped += 1
                            self.drops_by_priority[dropped_msg.priority] += 1
                            self.network.track_dropped_message(dropped_msg)
                    else:
                        message.dropped = True
                        message.drop_reason = "Buffer overflow (tail drop)"
                        self.messages_dropped += 1
                        self.drops_by_priority[message.priority] += 1
                        self.network.track_dropped_message(message)
                        return
                else:
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

    def _preempt_current_transmission(self, current_time: float):
        """
        Preempt (pause) the current transmission.

        Saves the partial transmission state and cancels the completion event.

        Args:
            current_time: Current simulation time
        """
        if self.current_transmission is None:
            return

        trans = self.current_transmission
        message = trans['message']
        link = trans['link']

        # FIX BUG #1 & #5: Cancel scheduled events before preempting
        if 'completion_event' in trans and trans['completion_event'] is not None:
            self.network.cancel_event(trans['completion_event'])
        if 'slot_event' in trans and trans['slot_event'] is not None:
            self.network.cancel_event(trans['slot_event'])

        # Calculate how much has been transmitted
        time_elapsed = current_time - trans['start_time']
        transmission_rate = link.bandwidth_bps / 8  # bytes per second
        bytes_transmitted = int(time_elapsed * transmission_rate)

        # Ensure we don't exceed message size
        bytes_transmitted = min(bytes_transmitted, message.size_bytes)
        bytes_remaining = message.size_bytes - bytes_transmitted

        # FIX BUG #3: Reset link state when preempting
        link.busy_until = current_time

        # FIX BUG #2: Add to paused queue (don't overwrite previous paused transmissions)
        self.paused_transmissions.append({
            'message': message,
            'output_port': trans['output_port'],
            'link': link,
            'bytes_transmitted': bytes_transmitted,
            'bytes_remaining': bytes_remaining,
            'paused_at': current_time
        })

        # Update statistics
        self.preemptions_count += 1
        self.preemptions_by_priority[message.priority] += 1

        # Clear current transmission (will be resumed later)
        self.current_transmission = None
        self.is_transmitting = False

    def forward_next_message(self, current_time: float):
        """
        Forward the next message.

        Checks for paused transmissions first (resume highest priority), then queue.

        Args:
            current_time: Current simulation time
        """
        # Priority 1: Resume highest-priority paused transmission if exists
        if self.paused_transmissions:
            # Sort paused transmissions by priority (highest first)
            self.paused_transmissions = deque(
                sorted(self.paused_transmissions,
                       key=lambda x: x['message'].priority,
                       reverse=True)
            )
            self._resume_paused_transmission(current_time)
            return

        # Priority 2: Forward from queue
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

        # Start fresh transmission
        self._start_transmission(message, output_port, link, current_time)

    def _start_transmission(self, message: Message, output_port: str,
                           link: Link, current_time: float):
        """
        Start transmitting a message (fresh, not resumed).

        Args:
            message: Message to transmit
            output_port: Output port name
            link: Output link
            current_time: Current simulation time
        """
        # Calculate transmission time
        transmission_time = link.get_transmission_time(message.size_bytes)

        # Wait if link is busy
        start_time = max(current_time, link.busy_until)
        completion_time = start_time + transmission_time + link.delay_sec
        link.busy_until = start_time + transmission_time

        self.messages_forwarded += 1

        # FIX BUG #1 & #5: Store event handles for cancellation
        # Schedule message arrival at destination
        completion_event = self.network.schedule_event(
            completion_time,
            lambda: self._complete_transmission(message, output_port, completion_time),
            f"Message {message.msg_id} (stream {message.stream_id}, pri {message.priority}) arrives at {output_port}"
        )

        # Schedule next forwarding attempt
        slot_event = self.network.schedule_event(
            link.busy_until,
            lambda: self._transmission_slot_available(link.busy_until),
            f"Switch {self.name} transmission slot available"
        )

        # Track current transmission with event handles
        self.current_transmission = {
            'message': message,
            'output_port': output_port,
            'link': link,
            'start_time': start_time,
            'bytes_transmitted': 0,
            'bytes_remaining': message.size_bytes,
            'completion_time': completion_time,
            'completion_event': completion_event,
            'slot_event': slot_event
        }

    def _resume_paused_transmission(self, current_time: float):
        """
        Resume a previously paused (preempted) transmission.

        Args:
            current_time: Current simulation time
        """
        if not self.paused_transmissions:
            return

        # Pop highest priority paused transmission (already sorted in forward_next_message)
        paused = self.paused_transmissions.popleft()
        message = paused['message']
        link = paused['link']
        output_port = paused['output_port']
        bytes_remaining = paused['bytes_remaining']

        # Calculate time to transmit remaining bytes
        transmission_rate = link.bandwidth_bps / 8  # bytes per second
        remaining_time = bytes_remaining / transmission_rate

        # Wait if link is busy
        start_time = max(current_time, link.busy_until)
        completion_time = start_time + remaining_time + link.delay_sec
        link.busy_until = start_time + remaining_time

        # Track preemption overhead
        preemption_overhead = current_time - paused['paused_at']
        self.total_preemption_overhead_ms += preemption_overhead * 1000

        self.is_transmitting = True

        # FIX BUG #1 & #5: Store event handles for cancellation
        # Schedule message arrival (after resumption completes)
        completion_event = self.network.schedule_event(
            completion_time,
            lambda: self._complete_transmission(message, output_port, completion_time),
            f"Message {message.msg_id} (resumed) arrives at {output_port}"
        )

        # Schedule next forwarding opportunity
        slot_event = self.network.schedule_event(
            link.busy_until,
            lambda: self._transmission_slot_available(link.busy_until),
            f"Switch {self.name} transmission slot available (after resume)"
        )

        # Update current transmission (resuming) with event handles
        self.current_transmission = {
            'message': message,
            'output_port': output_port,
            'link': link,
            'start_time': start_time,
            'bytes_transmitted': paused['bytes_transmitted'],
            'bytes_remaining': bytes_remaining,
            'completion_time': completion_time,
            'resumed': True,
            'completion_event': completion_event,
            'slot_event': slot_event
        }

    def _complete_transmission(self, message: Message, output_port: str,
                              completion_time: float):
        """
        Handle transmission completion.

        Args:
            message: Message that completed
            output_port: Destination port
            completion_time: When transmission completed
        """
        # Clear current transmission
        if self.current_transmission and self.current_transmission['message'] == message:
            self.current_transmission = None

        # Deliver message
        self.network.deliver_message(message, output_port)

    def _transmission_slot_available(self, current_time: float):
        """
        Called when transmission slot becomes available.

        Args:
            current_time: Current simulation time
        """
        # Mark as not transmitting and try to forward next
        self.current_transmission = None
        self.is_transmitting = False
        self.forward_next_message(current_time)

    def get_preemption_statistics(self) -> dict:
        """Get preemption-specific statistics."""
        return {
            'preemption_enabled': self.preemption_enabled,
            'total_preemptions': self.preemptions_count,
            'preemptions_by_priority': dict(self.preemptions_by_priority),
            'total_overhead_ms': self.total_preemption_overhead_ms,
            'avg_overhead_per_preemption_ms': (
                self.total_preemption_overhead_ms / self.preemptions_count
                if self.preemptions_count > 0 else 0
            )
        }


def test_preemptive_switch():
    """Test the preemptive switch implementation."""
    from priority_stream_simulator import Network, Message

    print("="*70)
    print("PREEMPTIVE SWITCH TEST")
    print("="*70)

    # Create network
    network = Network(sim_duration=1.0)

    # Create preemptive switch
    switch = PreemptiveSwitch("TestSwitch", network, preemption_enabled=True)

    print(f"\nSwitch created: {switch.name}")
    print(f"Preemption enabled: {switch.preemption_enabled}")

    # Create mock link
    link = Link("TestLink", bandwidth_mbps=100, delay_ms=1)
    switch.add_link("Output", link)
    switch.set_forwarding_entry("Dest", "Output")

    # Test message
    msg1 = Message(
        msg_id=1, stream_id=100, seq_num=0, priority=1,
        src_node="Src", dst_node="Dest", size_bytes=1500,
        creation_time=0.0
    )

    msg2 = Message(
        msg_id=2, stream_id=200, seq_num=0, priority=7,
        src_node="Src", dst_node="Dest", size_bytes=1000,
        creation_time=0.0001
    )

    print(f"\nTest messages created:")
    print(f"  Message 1: Priority {msg1.priority}, {msg1.size_bytes} bytes")
    print(f"  Message 2: Priority {msg2.priority}, {msg2.size_bytes} bytes")

    print("\nPreemptive switch ready for testing!")
    print("="*70)


if __name__ == "__main__":
    test_preemptive_switch()
