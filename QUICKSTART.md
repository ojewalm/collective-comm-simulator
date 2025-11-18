# Quick Start Guide

This guide will get you running experiments in under 5 minutes.

## Step 1: Installation

```bash
# Navigate to the project directory
cd collective-comm-simulator

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Run Your First Experiment

```bash
# Run a simple tree topology experiment
python run_simulation.py --topology tree --mode scenarios
```

This will:
- Simulate collective communication (All-to-All and All-Reduce patterns)
- Compare protected (priority 7) vs unprotected (priority 3) scenarios
- Generate CSV results in `simulations/tree_topology/results/`

## Step 3: Generate Visualizations

```bash
# Run the same experiment with automatic analysis
python run_simulation.py --topology tree --mode scenarios --analyze
```

This will:
- Run the experiments
- Analyze the results
- Generate comparison plots and time series visualizations
- Save plots to `simulations/tree_topology/plots/`

## Step 4: Explore Different Topologies

```bash
# Try the rail-optimized topology (2-rack design)
python run_simulation.py --topology rail_optimized --mode scenarios --analyze

# Try the ring topology
python run_simulation.py --topology ring --mode scenarios --analyze
```

## Step 5: Evaluate Frame Preemption

```bash
# Run preemptive experiments (enabled vs disabled)
python run_simulation.py --topology rail_optimized --mode preemptive --analyze
```

## Step 6: Run Complete Evaluation

```bash
# Run all experiments for a topology
python run_simulation.py --topology rail_optimized --mode all --analyze
```

This runs:
- Scenario experiments (Protected vs Unprotected)
- Preemptive experiments (Enabled vs Disabled)
- Analysis and visualization for both

## Understanding the Results

### Console Output

During simulation, you'll see:
```
Building rail-optimized topology...
  - 8 compute nodes (2 racks, 4 nodes each)
  - 2 ToR switches
  ...

Starting simulation (duration: 10.0s)...
Simulation completed: 65596 events in 0.343s

RESULTS SUMMARY
===============
Collective Traffic:
  Messages delivered: 11200
  Drop rate: 0.00%
  Mean delay: 1.685 ms
```

### Generated Files

**CSV Files** (`results/` directory):
- Raw event data for all delivered messages
- Columns: stream_id, src, dst, priority, size, arrival_time, delay, etc.

**Plot Files** (`plots/` directory):
- `comparison_*.png`: Side-by-side comparison of scenarios
- `timeseries_*.png`: Delay and throughput evolution over time

## Common Commands Reference

```bash
# Scenarios only
python run_simulation.py -t tree -m scenarios -a
python run_simulation.py -t ring -m scenarios -a
python run_simulation.py -t rail_optimized -m scenarios -a

# Preemptive only
python run_simulation.py -t tree -m preemptive -a
python run_simulation.py -t ring -m preemptive -a
python run_simulation.py -t rail_optimized -m preemptive -a

# Complete evaluation
python run_simulation.py -t tree -m all -a
python run_simulation.py -t ring -m all -a
python run_simulation.py -t rail_optimized -m all -a
```

## Customizing Experiments

To modify simulation parameters, edit the experiment files directly:

**Simulation Duration:**
```python
# In simulations/<topology>/scenarios/run_experiment.py
experiment = CollectiveExperiment(
    sim_duration=10.0,  # Change this value
    ...
)
```

**Traffic Parameters:**
```python
experiment = CollectiveExperiment(
    collective_msg_size=1000,      # Collective message size (bytes)
    collective_interval=0.05,      # Time between messages (seconds)
    background_msg_size=1500,      # Background message size
    background_interval=0.03,      # Background interval
)
```

## Next Steps

- Review the main [README.md](README.md) for detailed documentation
- Explore the `src/` directory to understand topology implementations
- Check `docs/` for additional guides
- Modify parameters to suit your research needs

## Troubleshooting

**Problem**: Import errors for `priority_stream_simulator`

**Solution**: Ensure the simulator is in your Python path:
```bash
export PYTHONPATH=/path/to/parent/directory:$PYTHONPATH
```

**Problem**: No plots generated

**Solution**: Ensure matplotlib is installed:
```bash
pip install matplotlib
```

**Problem**: Permission errors

**Solution**: Make the run script executable:
```bash
chmod +x run_simulation.py
```

## Getting Help

- Check the [README.md](README.md) for comprehensive documentation
- Open an issue on GitHub
- Review the example configurations in `examples/`
