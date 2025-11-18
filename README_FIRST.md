# 🚀 START HERE - Quick Setup

## Your Project is Ready to Use!

Everything is already configured. Just follow these 2 steps:

### Step 1: Install Dependencies (30 seconds)

```bash
cd collective-comm-simulator
pip install -r requirements.txt
```

### Step 2: Run a Simulation (immediately)

```bash
python3 run_simulation.py --topology tree --mode scenarios
```

That's it! You should see simulation output.

---

## What Just Happened?

The import paths are **already configured** to find `priority_stream_simulator.py` in your parent directory (`MLSys-Experiments/`).

Your directory structure:
```
MLSys-Experiments/
├── priority_stream_simulator.py      # Already here ✓
└── collective-comm-simulator/         # You are here
    ├── run_simulation.py              # Master runner
    └── simulations/                   # All experiments
```

---

## Next: Try These Commands

```bash
# With analysis and plots
python3 run_simulation.py --topology tree --mode scenarios --analyze

# Different topology
python3 run_simulation.py --topology rail_optimized --mode scenarios --analyze

# Preemption experiments
python3 run_simulation.py --topology tree --mode preemptive --analyze

# Everything!
python3 run_simulation.py --topology tree --mode all --analyze
```

---

## Full Documentation

- **[INSTALLATION.md](INSTALLATION.md)** - Detailed setup guide
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute tutorial
- **[COMMANDS.md](COMMANDS.md)** - All available commands
- **[README.md](README.md)** - Complete documentation

---

## Quick Reference

**Topologies:** `tree`, `ring`, `rail_optimized`
**Modes:** `scenarios`, `preemptive`, `all`
**Flags:** `--analyze` (or `-a`) for plots

**Examples:**
```bash
python3 run_simulation.py -t tree -m scenarios -a
python3 run_simulation.py -t ring -m preemptive -a
python3 run_simulation.py -t rail_optimized -m all -a
```

---

## ✨ What You Get

- **3 Network Topologies** (Tree, Ring, Rail-Optimized)
- **2 Collective Patterns** (All-to-All, All-Reduce)
- **Priority Scheduling** (Protected vs Unprotected)
- **Frame Preemption** (Enabled vs Disabled)
- **Automated Analysis** (Plots and metrics)

---

## 🆘 Having Issues?

**Error: ModuleNotFoundError**
- Make sure you're in the `collective-comm-simulator` directory
- The import paths are already fixed!

**Need Help?**
- Check [INSTALLATION.md](INSTALLATION.md) for troubleshooting
- See [README.md](README.md) for full docs

---

**Ready?** Run this now:
```bash
python3 run_simulation.py --topology tree --mode scenarios --analyze
```

Then check `simulations/tree_topology/scenarios/plots/` for your first results! 🎉
