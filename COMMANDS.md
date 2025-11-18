# Command Reference

Quick reference for all simulation commands.

## Master Simulation Runner

The `run_simulation.py` script provides a unified interface for all experiments.

### Basic Syntax

```bash
python3 run_simulation.py --topology <TOPOLOGY> --mode <MODE> [--analyze]
```

### Topologies

- `tree`: 3-level tree topology (Root + 2 Aggregation + 8 nodes)
- `ring`: Ring topology (4 switches + 8 nodes)
- `rail_optimized`: 2-rack topology (2 ToR switches + 8 nodes)

### Modes

- `scenarios`: Priority comparison (Protected vs Unprotected)
- `preemptive`: Frame preemption (Enabled vs Disabled)
- `all`: Run both scenarios and preemptive experiments

### Flags

- `--analyze`, `-a`: Generate plots and analysis after experiments
- `--help`, `-h`: Show help message

## Complete Command Matrix

### Tree Topology

```bash
# Scenarios only (no analysis)
python3 run_simulation.py -t tree -m scenarios

# Scenarios with analysis and plots
python3 run_simulation.py -t tree -m scenarios -a

# Preemptive experiments only
python3 run_simulation.py -t tree -m preemptive

# Preemptive with analysis
python3 run_simulation.py -t tree -m preemptive -a

# Complete evaluation (both modes + analysis)
python3 run_simulation.py -t tree -m all -a
```

### Ring Topology

```bash
# Scenarios only
python3 run_simulation.py -t ring -m scenarios

# Scenarios with analysis
python3 run_simulation.py -t ring -m scenarios -a

# Preemptive only
python3 run_simulation.py -t ring -m preemptive

# Preemptive with analysis
python3 run_simulation.py -t ring -m preemptive -a

# Complete evaluation
python3 run_simulation.py -t ring -m all -a
```

### Rail-Optimized Topology

```bash
# Scenarios only
python3 run_simulation.py -t rail_optimized -m scenarios

# Scenarios with analysis
python3 run_simulation.py -t rail_optimized -m scenarios -a

# Preemptive only
python3 run_simulation.py -t rail_optimized -m preemptive

# Preemptive with analysis
python3 run_simulation.py -t rail_optimized -m preemptive -a

# Complete evaluation
python3 run_simulation.py -t rail_optimized -m all -a
```

## Direct Script Execution

You can also run experiments directly from their directories.

### Scenario Experiments

```bash
# Tree topology scenarios
cd simulations/tree_topology/scenarios
python3 run_experiment.py
python3 analyze_results.py

# Ring topology scenarios
cd simulations/ring_topology/scenarios
python3 run_experiment.py
python3 analyze_results.py

# Rail-optimized scenarios
cd simulations/rail_optimized/scenarios
python3 run_experiment.py
python3 analyze_results.py
```

### Preemptive Experiments

```bash
# Tree topology preemptive
cd simulations/tree_topology/preemptive
python3 run_preemptive_experiments.py
python3 analyze_preemption.py

# Ring topology preemptive
cd simulations/ring_topology/preemptive
python3 run_preemptive_experiments.py
python3 analyze_preemption.py

# Rail-optimized preemptive
cd simulations/rail_optimized/preemptive
python3 run_preemptive_experiments.py
python3 analyze_preemption.py
```

## Output Locations

### Results (CSV files)

**Scenarios:**
- `simulations/<topology>/scenarios/results/scenario_a/`
- `simulations/<topology>/scenarios/results/scenario_b/`

**Preemptive:**
- `simulations/<topology>/preemptive/results/protected/`
- `simulations/<topology>/preemptive/results/unprotected/`

### Plots (PNG files)

**Scenarios:**
- `simulations/<topology>/scenarios/plots/`
  - `comparison_all-to-all.png`
  - `comparison_all-reduce.png`
  - `timeseries_scenario_a_all-to-all.png`
  - `timeseries_scenario_b_all-to-all.png`
  - `timeseries_scenario_a_all-reduce.png`
  - `timeseries_scenario_b_all-reduce.png`

**Preemptive:**
- `simulations/<topology>/preemptive/plots/`
  - `preemption_all-to-all.png`
  - `preemption_all-reduce.png`
  - `timeseries_protected_all-to-all.png`
  - `timeseries_unprotected_all-to-all.png`
  - `timeseries_protected_all-reduce.png`
  - `timeseries_unprotected_all-reduce.png`

## Batch Execution

### Run All Topologies (One Mode)

```bash
# Run scenarios for all topologies with analysis
for topo in tree ring rail_optimized; do
    python3 run_simulation.py -t $topo -m scenarios -a
done

# Run preemptive for all topologies
for topo in tree ring rail_optimized; do
    python3 run_simulation.py -t $topo -m preemptive -a
done
```

### Complete Evaluation

```bash
# Run everything
for topo in tree ring rail_optimized; do
    python3 run_simulation.py -t $topo -m all -a
done
```

### Generate Only Plots (After Running Experiments)

```bash
# If you already ran experiments and just want to regenerate plots
cd simulations/tree_topology/scenarios
python3 analyze_results.py

cd ../preemptive
python3 analyze_preemption.py
```

## Customization

### Modify Simulation Parameters

Edit the experiment files directly:

```python
# In simulations/<topology>/scenarios/run_experiment.py or
# simulations/<topology>/preemptive/run_preemptive_experiments.py

experiment = CollectiveExperiment(
    sim_duration=10.0,           # Simulation time in seconds
    collective_msg_size=1000,     # Collective message size (bytes)
    collective_interval=0.05,     # Time between collective messages (seconds)
    background_msg_size=1500,     # Background message size (bytes)
    background_interval=0.03,     # Time between background messages (seconds)
)
```

### Modify Topology Parameters

Edit topology files in `src/topology/`:

```python
# Example: src/topology/tree_topology.py
topology = TreeTopology(
    network,
    access_bw_mbps=1000,          # Access link bandwidth
    aggregation_bw_mbps=2000,     # Aggregation link bandwidth
    access_delay_ms=0.5,          # Access link delay
    aggregation_delay_ms=1.0,     # Aggregation link delay
    switch_queue_size=100         # Switch queue size
).build()
```

## Debugging

### Verbose Output

```bash
# Run with Python unbuffered output
python3 -u run_simulation.py -t tree -m scenarios -a

# Capture output to file
python3 run_simulation.py -t tree -m all -a 2>&1 | tee experiment.log
```

### Check Module Imports

```bash
# Verify all modules can be imported
python3 -c "
import sys
sys.path.insert(0, 'src')
from topology.tree_topology import TreeTopology
from topology.ring_topology import RingTopology
from topology.rail_optimized_topology import RailOptimizedTopology
from collectives.patterns import CollectivePatterns
from switch.preemptive_switch import PreemptiveSwitch
print('✓ All modules imported successfully')
"
```

### Test Individual Components

```bash
# Test topology creation
python3 -c "
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '..')
from priority_stream_simulator import Network
from topology.rail_optimized_topology import RailOptimizedTopology

network = Network(sim_duration=1.0)
topology = RailOptimizedTopology(network).build()
print(f'Created topology with {len(topology.nodes)} nodes')
"
```

## Performance Tips

### Faster Execution

```bash
# Use shorter simulation duration for quick tests
# Edit experiment files and set:
sim_duration=1.0  # Instead of 10.0
```

### Parallel Execution

```bash
# Run different topologies in parallel (Linux/Mac)
python3 run_simulation.py -t tree -m all -a &
python3 run_simulation.py -t ring -m all -a &
python3 run_simulation.py -t rail_optimized -m all -a &
wait
```

## Common Workflows

### Quick Test

```bash
# Fast test to verify everything works
python3 run_simulation.py -t rail_optimized -m scenarios
```

### Full Evaluation

```bash
# Complete study with all topologies and modes
for topo in tree ring rail_optimized; do
    echo "Running $topo..."
    python3 run_simulation.py -t $topo -m all -a
done
echo "All experiments complete!"
```

### Regenerate All Plots

```bash
# If you have CSV results and want to regenerate plots
for dir in simulations/*/scenarios; do
    (cd "$dir" && python3 analyze_results.py)
done

for dir in simulations/*/preemptive; do
    (cd "$dir" && python3 analyze_preemption.py)
done
```

## See Also

- [README.md](README.md) - Complete documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [SETUP.md](SETUP.md) - Installation and setup
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributing guidelines
