#!/usr/bin/env python3
"""
Collective Communication Simulator - Master Runner Script

This script provides a unified interface to run all simulation experiments.

Usage:
    python run_simulation.py --topology <topology> --mode <mode> [--analyze]

Examples:
    # Run tree topology scenario experiments
    python run_simulation.py --topology tree --mode scenarios

    # Run rail-optimized preemptive experiments with analysis
    python run_simulation.py --topology rail_optimized --mode preemptive --analyze

    # Run all experiments for ring topology
    python run_simulation.py --topology ring --mode all --analyze
"""

import argparse
import os
import sys
import subprocess

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# Add priority stream simulator to path (assuming it's in parent directory)
SIMULATOR_PATH = os.path.dirname(PROJECT_ROOT)
if os.path.exists(os.path.join(SIMULATOR_PATH, 'priority_stream_simulator')):
    sys.path.insert(0, SIMULATOR_PATH)


TOPOLOGIES = ['tree', 'ring', 'rail_optimized']
MODES = ['scenarios', 'preemptive', 'all']


def run_command(cmd, cwd):
    """Run a command and return the result."""
    print(f"\n{'='*70}")
    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {cwd}")
    print(f"{'='*70}\n")

    result = subprocess.run(cmd, cwd=cwd, capture_output=False, text=True)

    if result.returncode != 0:
        print(f"\n[ERROR] Command failed with exit code {result.returncode}")
        return False
    return True


def run_scenarios(topology_dir, analyze=False):
    """Run scenario experiments (Protected vs Unprotected)."""
    scenarios_dir = os.path.join(topology_dir, 'scenarios')

    if not os.path.exists(scenarios_dir):
        print(f"[WARNING] Scenarios directory not found: {scenarios_dir}")
        return False

    # Run experiments
    success = run_command(['python3', 'run_experiment.py'], scenarios_dir)

    # Run analysis if requested
    if analyze and success:
        print("\nRunning analysis...")
        run_command(['python3', 'analyze_results.py'], scenarios_dir)

    return success


def run_preemptive(topology_dir, analyze=False):
    """Run preemptive experiments."""
    preemptive_dir = os.path.join(topology_dir, 'preemptive')

    if not os.path.exists(preemptive_dir):
        print(f"[WARNING] Preemptive directory not found: {preemptive_dir}")
        return False

    # Run experiments
    success = run_command(['python3', 'run_preemptive_experiments.py'], preemptive_dir)

    # Run analysis if requested
    if analyze and success:
        print("\nRunning analysis...")
        run_command(['python3', 'analyze_preemption.py'], preemptive_dir)

    return success


def main():
    parser = argparse.ArgumentParser(
        description='Run collective communication simulation experiments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Topologies:
  tree           - Tree topology (3-level: Root, 2 Aggregation, 8 compute nodes)
  ring           - Ring topology (4 switches in a ring, 8 compute nodes)
  rail_optimized - Rail-optimized (2 ToR switches, 8 compute nodes)

Modes:
  scenarios      - Run priority scenarios (Protected vs Unprotected)
  preemptive     - Run preemption experiments (Enabled vs Disabled)
  all            - Run both scenarios and preemptive experiments

Examples:
  python run_simulation.py --topology tree --mode scenarios
  python run_simulation.py --topology rail_optimized --mode all --analyze
  python run_simulation.py --topology ring --mode preemptive --analyze
        """
    )

    parser.add_argument(
        '--topology', '-t',
        required=True,
        choices=TOPOLOGIES,
        help='Network topology to use'
    )

    parser.add_argument(
        '--mode', '-m',
        required=True,
        choices=MODES,
        help='Experiment mode to run'
    )

    parser.add_argument(
        '--analyze', '-a',
        action='store_true',
        help='Run analysis and generate plots after experiments'
    )

    args = parser.parse_args()

    # Construct topology directory path
    topology_name = f"{args.topology}_topology" if args.topology != 'rail_optimized' else 'rail_optimized'
    topology_dir = os.path.join(PROJECT_ROOT, 'simulations', topology_name)

    if not os.path.exists(topology_dir):
        print(f"[ERROR] Topology directory not found: {topology_dir}")
        sys.exit(1)

    print(f"\n{'#'*70}")
    print(f"# COLLECTIVE COMMUNICATION SIMULATOR")
    print(f"# Topology: {args.topology.upper()}")
    print(f"# Mode: {args.mode.upper()}")
    print(f"# Analysis: {'ENABLED' if args.analyze else 'DISABLED'}")
    print(f"{'#'*70}\n")

    # Run requested experiments
    success = True

    if args.mode == 'scenarios' or args.mode == 'all':
        success = run_scenarios(topology_dir, args.analyze) and success

    if args.mode == 'preemptive' or args.mode == 'all':
        success = run_preemptive(topology_dir, args.analyze) and success

    if success:
        print(f"\n{'='*70}")
        print("ALL EXPERIMENTS COMPLETED SUCCESSFULLY")
        print(f"{'='*70}\n")

        # Show results location
        results_base = os.path.join(topology_dir, 'results')
        print(f"Results saved to:")
        if args.mode in ['scenarios', 'all']:
            print(f"  - {os.path.join(results_base, 'scenario_a')}")
            print(f"  - {os.path.join(results_base, 'scenario_b')}")
        if args.mode in ['preemptive', 'all']:
            print(f"  - {os.path.join(results_base, 'protected')}")
            print(f"  - {os.path.join(results_base, 'unprotected')}")

        if args.analyze:
            plots_dir = os.path.join(topology_dir, 'plots')
            print(f"\nPlots saved to: {plots_dir}")
    else:
        print(f"\n{'='*70}")
        print("[ERROR] Some experiments failed")
        print(f"{'='*70}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
