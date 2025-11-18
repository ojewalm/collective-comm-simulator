# Setup Instructions

## Installation and Configuration

### 1. Prerequisites

Ensure you have Python 3.7 or later:
```bash
python3 --version
```

### 2. Clone/Download the Repository

```bash
# If using git
git clone https://github.com/ojewalm/collective-comm-simulator.git
cd collective-comm-simulator

# Or extract from archive
unzip collective-comm-simulator.zip
cd collective-comm-simulator
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- numpy (numerical computing)
- matplotlib (plotting)
- pandas (data analysis)

### 4. Setup Priority Stream Simulator

**Option A: Simulator in Parent Directory (Recommended)**

If the `priority_stream_simulator` module is in the parent directory of this project:

```
MLSys-Experiments/
├── priority_stream_simulator/     # Simulator here
└── collective-comm-simulator/     # This project
```

No additional configuration needed - the scripts will auto-detect it!

**Option B: Simulator Elsewhere**

If the simulator is in a different location, set the PYTHONPATH:

```bash
# Linux/Mac
export PYTHONPATH=/path/to/parent/of/simulator:$PYTHONPATH

# Windows (PowerShell)
$env:PYTHONPATH = "C:\path\to\parent\of\simulator;$env:PYTHONPATH"

# Add to .bashrc or .zshrc for persistence
echo 'export PYTHONPATH=/path/to/parent/of/simulator:$PYTHONPATH' >> ~/.bashrc
```

**Option C: Install as Package**

```bash
# If priority_stream_simulator has a setup.py
cd /path/to/priority_stream_simulator
pip install -e .
```

### 5. Verify Installation

Test that everything is configured correctly:

```bash
# Test imports
python3 -c "
import sys
sys.path.insert(0, 'src')
from topology.tree_topology import TreeTopology
from collectives.patterns import CollectivePatterns
print('✓ Project modules loaded successfully')
"

# Try to import the simulator (may fail if not in path)
python3 -c "from priority_stream_simulator import Network; print('✓ Simulator found')"
```

Expected output:
```
✓ Project modules loaded successfully
✓ Simulator found
```

### 6. Run a Test Experiment

```bash
# Quick test with rail-optimized topology
python3 run_simulation.py --topology rail_optimized --mode scenarios
```

If you see "Building rail-optimized topology..." and simulation progress, you're ready to go!

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'priority_stream_simulator'`

**Solution 1**: Check simulator location
```bash
# Find where the simulator is
find ~ -name "priority_stream_simulator" -type d 2>/dev/null
```

**Solution 2**: Set PYTHONPATH
```bash
export PYTHONPATH=/path/to/parent/directory:$PYTHONPATH
python3 run_simulation.py --topology tree --mode scenarios
```

**Solution 3**: Modify run scripts manually
Edit `simulations/*/scenarios/run_experiment.py` and add:
```python
sys.path.insert(0, '/absolute/path/to/parent/directory')
```

### Issue: `ModuleNotFoundError: No module named 'numpy'` (or matplotlib/pandas)

**Solution**:
```bash
pip install numpy matplotlib pandas
# or
pip install -r requirements.txt
```

### Issue: Permission denied

**Solution**:
```bash
chmod +x run_simulation.py
# Then run with:
./run_simulation.py --topology tree --mode scenarios
```

### Issue: Plots not generating

**Solution**: Ensure matplotlib backend is configured:
```bash
# If using a headless server
export MPLBACKEND=Agg

# Test matplotlib
python3 -c "import matplotlib.pyplot as plt; print('✓ Matplotlib OK')"
```

## Project Structure After Setup

```
collective-comm-simulator/
├── README.md              # Main documentation
├── QUICKSTART.md          # Quick start guide
├── SETUP.md               # This file
├── requirements.txt       # Dependencies
├── setup.py              # Package setup
├── run_simulation.py     # Main runner script
│
├── src/                  # Source code
│   ├── topology/         # Network topologies
│   ├── collectives/      # Collective patterns
│   └── switch/           # Switch implementations
│
├── simulations/          # Experiment scripts
│   ├── tree_topology/
│   ├── ring_topology/
│   └── rail_optimized/
│
├── results/              # Generated after running experiments
└── docs/                 # Additional documentation
```

## Next Steps

Once setup is complete:

1. **Quick Start**: Read [QUICKSTART.md](QUICKSTART.md) for basic usage
2. **Full Documentation**: See [README.md](README.md) for comprehensive guide
3. **Run Experiments**: Try different topologies and modes
4. **Customize**: Modify parameters in simulation scripts
5. **Contribute**: See CONTRIBUTING.md (if available)

## Getting Help

If you encounter issues not covered here:

1. Check the [README.md](README.md) troubleshooting section
2. Verify your Python version: `python3 --version`
3. Check installed packages: `pip list | grep -E "numpy|matplotlib|pandas"`
4. Open an issue on GitHub with:
   - Your operating system
   - Python version
   - Complete error message
   - Steps to reproduce

## Development Setup

For contributors wanting to modify the simulator:

```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest black flake8

# Run tests (if available)
pytest tests/

# Format code
black src/ simulations/

# Lint code
flake8 src/ simulations/
```
