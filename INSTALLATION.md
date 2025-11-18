# Installation Guide

## Quick Start (For This Setup)

### 1. Install Dependencies

```bash
cd collective-comm-simulator
pip install -r requirements.txt
```

This installs:
- numpy
- matplotlib
- pandas

### 2. Verify Installation

```bash
# Test that the simulator can be imported
python3 -c "import sys; sys.path.insert(0, '..'); from priority_stream_simulator import Network; print('✓ Simulator found!')"
```

Expected output: `✓ Simulator found!`

### 3. Run Your First Experiment

```bash
# Run tree topology scenario experiments
python3 run_simulation.py --topology tree --mode scenarios
```

You should see output like:
```
Building tree topology...
  - 8 compute nodes
  - 3 switches (1 root + 2 aggregation)
  ...
Starting simulation (duration: 5.0s)...
Simulation completed: 40600 events in 0.230s
```

### 4. Run with Analysis

```bash
# Run with automatic plot generation
python3 run_simulation.py --topology tree --mode scenarios --analyze
```

This generates plots in `simulations/tree_topology/scenarios/plots/`

## Current Directory Structure

Your setup:
```
MLSys-Experiments/
├── priority_stream_simulator.py      # ← Simulator is here
└── collective-comm-simulator/         # ← Project is here
    ├── run_simulation.py
    ├── src/
    └── simulations/
```

The import paths are already configured to find the simulator in the parent directory!

## Common Commands

```bash
# Quick test
python3 run_simulation.py -t tree -m scenarios

# With analysis
python3 run_simulation.py -t tree -m scenarios -a

# Different topologies
python3 run_simulation.py -t ring -m scenarios -a
python3 run_simulation.py -t rail_optimized -m scenarios -a

# Preemptive experiments
python3 run_simulation.py -t tree -m preemptive -a

# Complete evaluation (all experiments)
python3 run_simulation.py -t tree -m all -a
```

## Run All Experiments

```bash
# Run everything for all topologies
for topo in tree ring rail_optimized; do
    python3 run_simulation.py -t $topo -m all -a
done
```

## Troubleshooting

### Issue: ModuleNotFoundError

If you still get `ModuleNotFoundError: No module named 'priority_stream_simulator'`:

**Solution**: The import paths have been fixed. Make sure you're running from the project root:

```bash
cd /Users/mubarakojewale/Documents/MLSys-Experiments/collective-comm-simulator
python3 run_simulation.py --topology tree --mode scenarios
```

### Issue: Missing Dependencies

```bash
# Install all dependencies
pip install numpy matplotlib pandas

# Or use requirements file
pip install -r requirements.txt
```

### Issue: Permission Denied

```bash
# Make scripts executable (optional)
chmod +x run_simulation.py
```

## What Gets Generated

After running experiments, you'll see:

**Results** (CSV files):
```
simulations/<topology>/scenarios/results/
├── scenario_a/
│   ├── scenario_a_all-to-all.csv
│   └── scenario_a_all-reduce.csv
└── scenario_b/
    ├── scenario_b_all-to-all.csv
    └── scenario_b_all-reduce.csv
```

**Plots** (PNG files - only with `--analyze`):
```
simulations/<topology>/scenarios/plots/
├── comparison_all-to-all.png
├── comparison_all-reduce.png
├── timeseries_scenario_a_all-to-all.png
├── timeseries_scenario_b_all-to-all.png
├── timeseries_scenario_a_all-reduce.png
└── timeseries_scenario_b_all-reduce.png
```

## Expected Results

For a 5-second simulation:
- **Events**: ~40,000-65,000 processed
- **Messages**: ~6,000-12,000 delivered
- **Execution time**: < 1 second
- **Mean delay**: 1.6-3.0 ms
- **Drop rate**: 0% (with current parameters)

## Next Steps

1. ✅ **You're ready!** Try the commands above
2. 📖 **Read** [README.md](README.md) for full documentation
3. 🚀 **Customize** parameters in experiment files
4. 📊 **Analyze** results and plots

