#!/usr/bin/env python3
"""
Script to update import paths in all simulation files.
"""

import os
import re

IMPORT_HEADER = """import sys
import os

# Add project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# Add priority stream simulator (assuming it's in parent of project root)
SIMULATOR_PATH = os.path.dirname(PROJECT_ROOT)
if os.path.exists(os.path.join(SIMULATOR_PATH, 'priority_stream_simulator')):
    sys.path.insert(0, SIMULATOR_PATH)
"""

PREEMPTIVE_IMPORT_HEADER = """import sys
import os

# Add project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# Add priority stream simulator and preemptive experiments
SIMULATOR_PATH = os.path.dirname(PROJECT_ROOT)
if os.path.exists(os.path.join(SIMULATOR_PATH, 'priority_stream_simulator')):
    sys.path.insert(0, SIMULATOR_PATH)
"""


def update_file(filepath, is_preemptive=False):
    """Update import paths in a single file."""
    print(f"Updating: {filepath}")

    with open(filepath, 'r') as f:
        content = f.read()

    # Find the docstring
    docstring_match = re.search(r'^"""[\s\S]*?"""', content, re.MULTILINE)
    if not docstring_match:
        print(f"  WARNING: No docstring found, skipping")
        return False

    docstring = docstring_match.group(0)

    # Remove old import section
    pattern = r'import sys\nsys\.path\.append\([^\)]+\)[^\n]*\n(?:sys\.path\.append\([^\)]+\)[^\n]*\n)*'
    content_after_docstring = content[docstring_match.end():]
    content_after_docstring = re.sub(pattern, '', content_after_docstring)

    # Build new content
    header = PREEMPTIVE_IMPORT_HEADER if is_preemptive else IMPORT_HEADER
    new_content = docstring + "\n\n" + header + "\n" + content_after_docstring.lstrip()

    # Write back
    with open(filepath, 'w') as f:
        f.write(new_content)

    print(f"  ✓ Updated successfully")
    return True


def main():
    """Update all simulation files."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    simulations_dir = os.path.join(project_root, 'simulations')

    files_to_update = []

    # Find all run_experiment.py and analyze files
    for topology in os.listdir(simulations_dir):
        topology_dir = os.path.join(simulations_dir, topology)
        if not os.path.isdir(topology_dir):
            continue

        # Scenarios
        scenarios_dir = os.path.join(topology_dir, 'scenarios')
        if os.path.exists(scenarios_dir):
            run_file = os.path.join(scenarios_dir, 'run_experiment.py')
            analyze_file = os.path.join(scenarios_dir, 'analyze_results.py')
            if os.path.exists(run_file) and run_file.endswith('run_experiment.py'):
                files_to_update.append((run_file, False))
            if os.path.exists(analyze_file):
                files_to_update.append((analyze_file, False))

        # Preemptive
        preemptive_dir = os.path.join(topology_dir, 'preemptive')
        if os.path.exists(preemptive_dir):
            run_file = os.path.join(preemptive_dir, 'run_preemptive_experiments.py')
            analyze_file = os.path.join(preemptive_dir, 'analyze_preemption.py')
            if os.path.exists(run_file):
                files_to_update.append((run_file, True))
            if os.path.exists(analyze_file):
                files_to_update.append((analyze_file, True))

    print(f"Found {len(files_to_update)} files to update\n")

    success_count = 0
    for filepath, is_preemptive in files_to_update:
        if update_file(filepath, is_preemptive):
            success_count += 1
        print()

    print(f"\nCompleted: {success_count}/{len(files_to_update)} files updated successfully")


if __name__ == '__main__':
    main()
