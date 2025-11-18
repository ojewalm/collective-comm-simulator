# Collective Communication Simulator

A discrete-event network simulator for studying collective communication patterns in distributed ML/HPC systems with support for priority-based scheduling and frame preemption.

## Overview

This simulator enables researchers and engineers to evaluate different network topologies, priority scheduling mechanisms, and frame preemption strategies for collective communication operations (All-to-All, All-Reduce) commonly used in distributed machine learning training.

### Key Features

- **Multiple Network Topologies**: Tree, Ring, and Rail-Optimized (2-rack) topologies
- **Priority-Based Scheduling**: Compare protected vs unprotected collective traffic
- **Frame Preemption**: Evaluate impact of mid-transmission interruption
- **Realistic Traffic Patterns**: Background traffic to simulate production workloads
- **Comprehensive Analysis**: Automated analysis scripts with visualization
- **Extensible Design**: Easy to add new topologies and collective patterns

## Installation

### Prerequisites

- Python 3.7+
- Required packages (see `requirements.txt`)

### Setup

1. Clone or download this repository:
```bash
git clone https://github.com/ojewalm/collective-comm-simulator.git
cd collective-comm-simulator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure the priority stream simulator is accessible:
```bash
# If the priority_stream_simulator is in the parent directory, it will be auto-detected
# Otherwise, add it to your PYTHONPATH:
export PYTHONPATH=/path/to/priority_stream_simulator:$PYTHONPATH
```

## Quick Start

### Run a Simple Experiment

```bash
# Run tree topology with scenario experiments
python run_simulation.py --topology tree --mode scenarios

# Run with automatic analysis and plot generation
python run_simulation.py --topology tree --mode scenarios --analyze
```

### Run All Experiments for a Topology

```bash
# Run all experiments (scenarios + preemptive) with analysis
python run_simulation.py --topology rail_optimized --mode all --analyze
```

## Usage

### Master Simulation Runner

The `run_simulation.py` script provides a unified interface to run all experiments:

```bash
python run_simulation.py --topology <topology> --mode <mode> [--analyze]
```

**Arguments:**
- `--topology, -t`: Network topology to use
  - `tree`: 3-level tree (Root + 2 Aggregation switches + 8 nodes)
  - `ring`: 4 switches in bidirectional ring + 8 nodes
  - `rail_optimized`: 2 ToR switches with direct connection + 8 nodes

- `--mode, -m`: Experiment mode
  - `scenarios`: Priority scenarios (Protected vs Unprotected)
  - `preemptive`: Frame preemption (Enabled vs Disabled)
  - `all`: Run both scenarios and preemptive experiments

- `--analyze, -a`: Generate plots and analysis after experiments

### Examples

```bash
# Tree topology: Compare priority scenarios
python run_simulation.py --topology tree --mode scenarios --analyze

# Ring topology: Evaluate frame preemption
python run_simulation.py --topology ring --mode preemptive --analyze

# Rail-optimized: Run complete evaluation
python run_simulation.py --topology rail_optimized --mode all --analyze
```

### Running Individual Simulations

You can also run experiments directly from simulation directories:

**Scenario Experiments (Protected vs Unprotected):**
```bash
cd simulations/tree_topology/scenarios
python run_experiment.py        # Run experiments
python analyze_results.py       # Generate plots
```

**Preemptive Experiments (Enabled vs Disabled):**
```bash
cd simulations/tree_topology/preemptive
python run_preemptive_experiments.py    # Run experiments
python analyze_preemption.py            # Generate plots
```

## Network Topologies

### Tree Topology
```
        Root
       /    \
    Agg0    Agg1
    / \      / \
  N0-N3    N4-N7
```
- **Switches**: 3 (1 Root, 2 Aggregation)
- **Nodes**: 8 compute nodes
- **Characteristics**: Traditional hierarchical design, potential bottleneck at root

### Ring Topology
```
  N0 N1      N2 N3
   \ /        \ /
    S0 ------ S1
    |          |
    S3 ------ S2
   / \        / \
  N7 N6      N5 N4
```
- **Switches**: 4 in bidirectional ring
- **Nodes**: 8 compute nodes (2 per switch)
- **Characteristics**: Multiple paths, improved fault tolerance

### Rail-Optimized Topology
```
  N0 N1 N2 N3      N4 N5 N6 N7
   \  |  |  /       \  |  |  /
      ToR0 --------- ToR1
    (Rack 0)       (Rack 1)
```
- **Switches**: 2 ToR switches with direct connection
- **Nodes**: 8 compute nodes (4 per rack)
- **Characteristics**: Simplified design, high inter-rack bandwidth (2x)

## Experiment Types

### Scenario Experiments: Priority Comparison

Compares two priority configurations:

**Scenario A (Protected):**
- Collective traffic: Priority 7 (High)
- Background traffic: Priority 1 (Low)
- **Goal**: Protect collective operations from interference

**Scenario B (Unprotected):**
- Collective traffic: Priority 3 (Medium)
- Background traffic: Priority 3 (Same)
- **Goal**: Baseline with no priority protection

**Metrics Compared:**
- Mean delay and jitter
- Drop rates
- Throughput
- Tail latency (P95, P99)

### Preemptive Experiments: Frame Preemption

Evaluates frame preemption mechanisms:

**Protected Mode (Preemption Enabled):**
- High-priority traffic can interrupt low-priority transmission
- Potential for reduced latency
- Small overhead per preemption

**Unprotected Mode (Preemption Disabled):**
- Standard priority scheduling
- No mid-transmission interruption
- Lower priority must wait for completion

**Metrics Compared:**
- Preemption count and overhead
- Impact on collective traffic performance
- Impact on background traffic

## Collective Patterns

### All-to-All
- Each node sends to all other nodes
- 56 streams total (8 nodes × 7 destinations)
- High network load, tests congestion handling

### All-Reduce
- Two-phase operation: Reduce + Broadcast
- 14 streams total (7 reduce + 7 broadcast)
- Common in distributed ML training

## Simulation Parameters

Default configuration (10-second simulation):

```python
sim_duration = 10.0              # Simulation time (seconds)
collective_msg_size = 1000       # Collective message size (bytes)
collective_interval = 0.05       # 50ms between messages
background_msg_size = 1500       # Background message size (bytes)
background_interval = 0.03       # 30ms between messages (higher rate)
```

**Network Parameters:**
- Access link bandwidth: 1000 Mbps
- Inter-rack bandwidth: 2000 Mbps (rail-optimized only)
- Link delay: 0.5ms (access), 1.0ms (inter-rack)
- Switch queue size: 50-100 packets

## Analysis and Visualization

### Automated Analysis

Each experiment generates:

1. **CSV files**: Raw event data for all messages
2. **Comparison plots**: Side-by-side metrics for both scenarios/modes
3. **Time series plots**: Delay and throughput evolution over time

### Output Plots

**Comparison Plots** (2×3 subplots):
- Mean delay (collective vs background)
- Jitter (collective vs background)
- Drop rate (collective vs background)

**Time Series Plots** (2×2 subplots):
- Collective traffic delay over time
- Collective traffic throughput over time
- Background traffic delay over time
- Background traffic throughput over time

### Results Directory Structure

```
simulations/<topology>/
├── results/
│   ├── scenario_a/          # Protected priority results
│   ├── scenario_b/          # Unprotected priority results
│   ├── protected/           # Preemption enabled results
│   └── unprotected/         # Preemption disabled results
└── plots/
    ├── comparison_*.png     # Comparison plots
    └── timeseries_*.png     # Time series plots
```

## Project Structure

```
collective-comm-simulator/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── run_simulation.py           # Master simulation runner
│
├── src/                        # Source code
│   ├── topology/              # Network topology implementations
│   │   ├── tree_topology.py
│   │   ├── ring_topology.py
│   │   └── rail_optimized_topology.py
│   ├── collectives/           # Collective communication patterns
│   │   └── patterns.py
│   └── switch/                # Switch implementations
│       └── preemptive_switch.py
│
├── simulations/               # Simulation experiments
│   ├── tree_topology/
│   │   ├── scenarios/        # Priority scenario experiments
│   │   └── preemptive/       # Preemption experiments
│   ├── ring_topology/
│   │   ├── scenarios/
│   │   └── preemptive/
│   └── rail_optimized/
│       ├── scenarios/
│       └── preemptive/
│
├── results/                   # Experiment results (auto-generated)
├── docs/                      # Additional documentation
└── examples/                  # Example configurations
```

## Extending the Simulator

### Adding a New Topology

1. Create topology class in `src/topology/`:
```python
from priority_stream_simulator import Network, Link

class MyTopology:
    def __init__(self, network, **params):
        self.network = network
        # Initialize parameters

    def build(self):
        # Create nodes and switches
        # Configure links
        # Set up forwarding tables
        return self

    def get_node_names(self):
        return [f"N{i}" for i in range(num_nodes)]
```

2. Create simulation scripts in `simulations/my_topology/`
3. Update `run_simulation.py` to include new topology

### Adding New Collective Patterns

Add methods to `src/collectives/patterns.py`:

```python
def my_pattern(self, priority, message_size_bytes, interval_sec, description):
    streams = []
    # Create stream objects
    return streams
```

## Performance Considerations

- **Simulation Speed**: ~50-100K events/second on modern hardware
- **Memory Usage**: Scales with simulation duration and traffic load
- **Recommended Duration**: 5-10 seconds for quick tests, 30-60s for detailed analysis

## Troubleshooting

### Import Errors

If you encounter import errors:
```python
ModuleNotFoundError: No module named 'priority_stream_simulator'
```

Ensure the simulator is in your path:
```bash
export PYTHONPATH=/path/to/priority_stream_simulator:$PYTHONPATH
```

### Path Issues

The simulation scripts automatically adjust paths. If you encounter issues:
- Run from project root: `python run_simulation.py ...`
- Or use absolute paths in configuration


## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


## Acknowledgments

The development is assisted significantly by AI.
