#!/usr/bin/env python3
"""Fix duplicate import blocks."""

import os
import re

def fix_file(filepath):
    """Remove duplicate import blocks."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Pattern to match the full import header block
    import_pattern = r'(import sys\nimport os\n\n# Add project paths\nPROJECT_ROOT.*?sys\.path\.insert\(0, SIMULATOR_PATH\)\n)'

    # Find all matches
    matches = list(re.finditer(import_pattern, content, re.DOTALL))

    if len(matches) > 1:
        print(f"Fixing: {filepath}")
        # Keep only the first match, remove others
        for match in reversed(matches[1:]):
            content = content[:match.start()] + content[match.end():]

        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    simulations_dir = os.path.join(project_root, 'simulations')

    fixed = 0
    for root, dirs, files in os.walk(simulations_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixed += 1

    print(f"\nFixed {fixed} files")

if __name__ == '__main__':
    main()
