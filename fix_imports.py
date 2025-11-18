#!/usr/bin/env python3
"""
Fix import paths to correctly locate priority_stream_simulator.
"""

import os
import re

NEW_IMPORT_BLOCK = """import sys
import os

# Add project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# Add priority stream simulator (in parent directory)
SIMULATOR_PATH = os.path.dirname(PROJECT_ROOT)
sys.path.insert(0, SIMULATOR_PATH)
"""

NEW_PREEMPTIVE_IMPORT_BLOCK = """import sys
import os

# Add project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# Add priority stream simulator (in parent directory)
SIMULATOR_PATH = os.path.dirname(PROJECT_ROOT)
sys.path.insert(0, SIMULATOR_PATH)
"""


def fix_file(filepath, is_preemptive=False):
    """Fix imports in a file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Find the docstring
    docstring_match = re.search(r'^"""[\s\S]*?"""', content, re.MULTILINE)
    if not docstring_match:
        print(f"  WARNING: No docstring in {filepath}")
        return False

    docstring_end = docstring_match.end()

    # Find where imports start (after docstring)
    remaining = content[docstring_end:]

    # Find the first "from" import (this is where actual imports begin)
    from_match = re.search(r'^from ', remaining, re.MULTILINE)
    if not from_match:
        print(f"  WARNING: No 'from' imports found in {filepath}")
        return False

    # Replace everything between docstring and first 'from' import
    new_content = (
        content[:docstring_end] +
        "\n\n" +
        (NEW_PREEMPTIVE_IMPORT_BLOCK if is_preemptive else NEW_IMPORT_BLOCK) +
        "\n" +
        remaining[from_match.start():]
    )

    with open(filepath, 'w') as f:
        f.write(new_content)

    return True


def main():
    """Fix all simulation files."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    simulations_dir = os.path.join(project_root, 'simulations')

    files_to_fix = []

    # Find all Python files
    for topology in os.listdir(simulations_dir):
        topology_dir = os.path.join(simulations_dir, topology)
        if not os.path.isdir(topology_dir):
            continue

        # Scenarios
        scenarios_dir = os.path.join(topology_dir, 'scenarios')
        if os.path.exists(scenarios_dir):
            for fname in ['run_experiment.py', 'analyze_results.py']:
                fpath = os.path.join(scenarios_dir, fname)
                if os.path.exists(fpath):
                    files_to_fix.append((fpath, False))

        # Preemptive
        preemptive_dir = os.path.join(topology_dir, 'preemptive')
        if os.path.exists(preemptive_dir):
            for fname in ['run_preemptive_experiments.py', 'analyze_preemption.py']:
                fpath = os.path.join(preemptive_dir, fname)
                if os.path.exists(fpath):
                    files_to_fix.append((fpath, True))

    print(f"Fixing {len(files_to_fix)} files...\n")

    fixed = 0
    for filepath, is_preemptive in files_to_fix:
        print(f"Fixing: {filepath}")
        if fix_file(filepath, is_preemptive):
            fixed += 1
            print(f"  ✓ Fixed")
        print()

    print(f"\n{'='*70}")
    print(f"Fixed {fixed}/{len(files_to_fix)} files")
    print(f"{'='*70}\n")

    # Test import
    print("Testing import...")
    test_file = os.path.join(simulations_dir, 'tree_topology/scenarios/run_experiment.py')
    if os.path.exists(test_file):
        os.system(f'cd {os.path.dirname(test_file)} && python3 -c "import run_experiment; print(\\"✓ Import successful!\\")" 2>&1 | head -5')


if __name__ == '__main__':
    main()
