# Project Overview

## Collective Communication Simulator

A professional, open-source discrete-event network simulator for studying collective communication patterns in distributed ML/HPC systems.

## What's Included

### Documentation (6 files)

1. **README.md** - Comprehensive project documentation
   - Features and capabilities
   - Usage examples
   - Topology descriptions
   - Analysis tools

2. **QUICKSTART.md** - Get started in 5 minutes
   - Step-by-step setup
   - First experiments
   - Common commands

3. **SETUP.md** - Installation and configuration
   - Prerequisites
   - Dependency installation
   - Troubleshooting guide

4. **COMMANDS.md** - Complete command reference
   - All simulation commands
   - Batch execution
   - Customization options

5. **CONTRIBUTING.md** - Contribution guidelines
   - How to contribute
   - Code style
   - Development workflow

6. **LICENSE** - MIT License for open source use

### Core Source Code

Located in `src/` directory:

**Topologies** (`src/topology/`)
- `tree_topology.py` - 3-level hierarchical tree
- `ring_topology.py` - 4-switch bidirectional ring
- `rail_optimized_topology.py` - 2-rack with direct ToR connection

**Collective Patterns** (`src/collectives/`)
- `patterns.py` - All-to-All and All-Reduce implementations

**Switch Implementations** (`src/switch/`)
- `preemptive_switch.py` - Frame preemption support

### Simulations

Located in `simulations/` directory:

**Three Network Topologies:**
1. Tree Topology
2. Ring Topology
3. Rail-Optimized Topology

**Each topology includes:**

**Scenarios/** - Priority comparison experiments
- `run_experiment.py` - Run scenario A (protected) vs B (unprotected)
- `analyze_results.py` - Generate comparison plots and time series

**Preemptive/** - Frame preemption experiments
- `run_preemptive_experiments.py` - Run with/without preemption
- `analyze_preemption.py` - Analyze preemption impact

**Total: 12 experiment scripts** (3 topologies × 2 modes × 2 scripts)

### Utilities

- `run_simulation.py` - Master simulation runner
- `setup.py` - Python package setup
- `requirements.txt` - Dependencies
- `.gitignore` - Git ignore rules

### Outputs (Generated)

When you run experiments, the simulator creates:

**Results/** - CSV files with raw event data
- Scenario A and B results
- Protected and unprotected mode results

**Plots/** - PNG visualizations
- Comparison plots (2×3 subplots)
- Time series plots (2×2 subplots)

## Key Features

### 1. Multiple Network Topologies

- **Tree**: Traditional hierarchical design
- **Ring**: Fault-tolerant ring structure
- **Rail-Optimized**: Modern 2-rack datacenter design

### 2. Realistic Traffic Patterns

- **All-to-All**: 56 streams (8 nodes × 7 destinations)
- **All-Reduce**: 14 streams (reduce + broadcast phases)
- **Background Traffic**: Continuous cross-rack traffic

### 3. Priority Scheduling

- **Scenario A**: Priority 7 (collective) vs Priority 1 (background)
- **Scenario B**: Priority 3 (both) - no protection
- Compares protected vs unprotected collectives

### 4. Frame Preemption

- **Protected Mode**: High-priority can interrupt low-priority
- **Unprotected Mode**: No mid-transmission interruption
- Evaluates preemption impact on latency

### 5. Comprehensive Analysis

- Mean delay and jitter
- Drop rates
- Tail latency (P95, P99)
- Throughput over time
- Automated plotting

## Project Statistics

- **Lines of Code**: ~3,000+ (Python)
- **Topologies**: 3
- **Collective Patterns**: 2
- **Experiment Scripts**: 12
- **Documentation Files**: 6
- **Total Files**: 30+

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run a quick test
python3 run_simulation.py --topology rail_optimized --mode scenarios

# 3. Run with analysis
python3 run_simulation.py --topology rail_optimized --mode scenarios --analyze

# 4. Complete evaluation
python3 run_simulation.py --topology rail_optimized --mode all --analyze
```

## Typical Results

**10-second simulation:**
- Events processed: 65,000+
- Messages delivered: 12,000+
- Execution time: < 1 second
- Mean delay: ~1.6-2.1 ms
- Drop rate: 0% (low congestion)

## Use Cases

### Research
- Evaluate network designs for ML training
- Study priority scheduling mechanisms
- Analyze preemption strategies
- Compare topology performance

### Education
- Learn discrete-event simulation
- Understand network protocols
- Study distributed systems
- Practice performance analysis

### Development
- Test new topologies
- Prototype scheduling algorithms
- Validate network designs
- Benchmark communication patterns

## Extensibility

Easy to extend:

1. **Add Topologies**: Implement new network designs
2. **New Patterns**: Add collective communication patterns
3. **Custom Metrics**: Extend analysis scripts
4. **Different Workloads**: Modify traffic patterns

## Technology Stack

- **Language**: Python 3.7+
- **Dependencies**: NumPy, Matplotlib, Pandas
- **Simulator**: Priority Stream Simulator (discrete-event)
- **Visualization**: Matplotlib with 2×3 and 2×2 subplots

## Project Structure

```
collective-comm-simulator/
├── README.md                    # Main documentation
├── QUICKSTART.md                # Quick start guide
├── SETUP.md                     # Setup instructions
├── COMMANDS.md                  # Command reference
├── CONTRIBUTING.md              # Contribution guide
├── LICENSE                      # MIT License
├── requirements.txt             # Dependencies
├── setup.py                     # Package setup
├── run_simulation.py            # Master runner
├── .gitignore                   # Git ignore rules
│
├── src/                         # Source code
│   ├── topology/                # Network topologies
│   │   ├── tree_topology.py
│   │   ├── ring_topology.py
│   │   └── rail_optimized_topology.py
│   ├── collectives/             # Collective patterns
│   │   └── patterns.py
│   └── switch/                  # Switch implementations
│       └── preemptive_switch.py
│
└── simulations/                 # Experiment scripts
    ├── tree_topology/
    │   ├── scenarios/
    │   │   ├── run_experiment.py
    │   │   └── analyze_results.py
    │   └── preemptive/
    │       ├── run_preemptive_experiments.py
    │       └── analyze_preemption.py
    ├── ring_topology/
    │   └── (same structure)
    └── rail_optimized/
        └── (same structure)
```

## Getting Help

1. **Quick Questions**: See [QUICKSTART.md](QUICKSTART.md)
2. **Setup Issues**: Check [SETUP.md](SETUP.md)
3. **Command Help**: Review [COMMANDS.md](COMMANDS.md)
4. **Full Docs**: Read [README.md](README.md)
5. **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## Next Steps

### For New Users
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run your first experiment
3. Explore different topologies
4. Customize parameters

### For Researchers
1. Review [README.md](README.md) thoroughly
2. Understand the topologies
3. Run complete evaluations
4. Modify for your research needs

### For Contributors
1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Set up development environment
3. Add new features or topologies
4. Submit pull requests

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Citation

If you use this simulator in your research, please cite:

```bibtex
@misc{collective_comm_simulator,
  title = {Collective Communication Simulator},
  author = {Mubarak Ojewale},
  year = {2025},
  url = {https://github.com/ojewalm/collective-comm-simulator.git}
}
```

