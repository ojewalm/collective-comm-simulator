# Contributing to Collective Communication Simulator

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/collective-comm-simulator.git
   cd collective-comm-simulator
   ```
3. **Set up the development environment** (see [SETUP.md](SETUP.md))
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Types of Contributions

We welcome several types of contributions:

### 1. New Network Topologies

Add new topology implementations to study different network designs.

**Steps:**
1. Create a new file in `src/topology/your_topology.py`
2. Implement the topology class following existing patterns:
   ```python
   class YourTopology:
       def __init__(self, network, **params):
           # Initialize parameters

       def build(self):
           # Create nodes, switches, links
           # Configure forwarding tables
           return self

       def get_node_names(self):
           # Return list of compute node names
   ```
3. Add simulation scripts in `simulations/your_topology/`
4. Update `run_simulation.py` to include your topology
5. Add documentation and tests

### 2. New Collective Patterns

Implement new collective communication patterns.

**Steps:**
1. Add methods to `src/collectives/patterns.py`:
   ```python
   def your_pattern(self, priority, message_size_bytes,
                   interval_sec, description):
       """Your collective pattern implementation."""
       streams = []
       # Create streams for your pattern
       return streams
   ```
2. Add examples showing how to use the pattern
3. Update documentation

### 3. Analysis and Visualization

Enhance analysis scripts with new metrics or visualizations.

**Examples:**
- New performance metrics (e.g., fairness, utilization)
- Additional plot types (e.g., heatmaps, CDFs)
- Statistical analysis tools
- Export formats (JSON, HDF5, etc.)

### 4. Documentation

Improve documentation:
- Fix typos or unclear explanations
- Add examples and tutorials
- Create video guides or screenshots
- Translate documentation

### 5. Bug Fixes

Fix bugs or issues:
1. Check existing issues on GitHub
2. Create a new issue if one doesn't exist
3. Reference the issue in your pull request

## Code Style Guidelines

### Python Style

Follow PEP 8 with these specifics:

```python
# Use descriptive names
def calculate_mean_delay(messages):  # Good
def cmd(m):  # Bad

# Add docstrings
def build_topology(network, num_nodes=8):
    """
    Build network topology.

    Args:
        network: Network simulator instance
        num_nodes: Number of compute nodes (default: 8)

    Returns:
        Configured topology instance
    """
    pass

# Use type hints
def process_results(data: List[Dict]) -> Dict[str, float]:
    pass

# Constants in UPPER_CASE
DEFAULT_BANDWIDTH_MBPS = 1000
MAX_QUEUE_SIZE = 100
```

### File Organization

```
new_topology/
├── __init__.py           # Empty or package exports
├── topology.py           # Topology implementation
├── README.md             # Topology-specific docs
└── tests/                # Unit tests
    └── test_topology.py
```

### Commit Messages

Write clear, descriptive commit messages:

```
Good:
"Add rail-optimized topology with 2-rack design"
"Fix: Correct priority queue ordering in switch"
"Docs: Add quickstart guide for new users"

Bad:
"update"
"fix bug"
"changes"
```

Format:
```
<type>: <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat: Add mesh topology implementation

Implements a 2D mesh topology with configurable dimensions.
Includes support for both torus and non-torus configurations.

Closes #123
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_topology.py

# Run with coverage
pytest --cov=src tests/
```

### Writing Tests

Add tests for new features:

```python
# tests/test_new_feature.py
import pytest
from topology.your_topology import YourTopology
from priority_stream_simulator import Network

def test_topology_creation():
    """Test that topology builds correctly."""
    network = Network(sim_duration=1.0)
    topology = YourTopology(network).build()

    assert len(topology.nodes) == 8
    assert len(topology.switches) > 0
    assert topology.get_node_names() == [f"N{i}" for i in range(8)]

def test_topology_forwarding():
    """Test that forwarding tables are configured."""
    network = Network(sim_duration=1.0)
    topology = YourTopology(network).build()

    # Add assertions for forwarding table correctness
    pass
```

## Pull Request Process

1. **Update documentation** for any changed functionality
2. **Add tests** for new features
3. **Run the test suite** and ensure all tests pass
4. **Update CHANGELOG.md** if applicable
5. **Create a pull request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots (if UI/visualization changes)
   - Test results

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] All existing tests pass
- [ ] Added new tests for new features
- [ ] Manually tested with: [describe test scenarios]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] No breaking changes (or documented if necessary)

## Related Issues
Fixes #123
```

## Code Review Process

All submissions require review:

1. **Automated checks** must pass (if configured)
2. **At least one maintainer** must approve
3. **Address review comments** promptly
4. **Squash commits** if requested
5. **Rebase on main** before merging

## Development Workflow

### Setting Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest black flake8 mypy
```

### Before Committing

```bash
# Format code
black src/ simulations/ tests/

# Check style
flake8 src/ simulations/ tests/

# Type check
mypy src/

# Run tests
pytest tests/
```

### Working with Large Changes

For significant changes:

1. **Open an issue first** to discuss the approach
2. **Break into smaller PRs** when possible
3. **Keep PRs focused** on a single concern
4. **Update documentation** incrementally

## Reporting Bugs

Use GitHub Issues with this template:

```markdown
## Bug Description
Clear description of the bug

## To Reproduce
Steps to reproduce:
1. Run command '...'
2. See error

## Expected Behavior
What you expected to happen

## Actual Behavior
What actually happened

## Environment
- OS: [e.g., macOS 12.0, Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- Simulator version: [e.g., 1.0.0]

## Additional Context
Error messages, screenshots, etc.
```

## Requesting Features

Use GitHub Issues with this template:

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed?

## Proposed Solution
How you envision this working

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Examples, mockups, references
```

## Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Give credit where due
- Follow the Code of Conduct

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

## Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open a GitHub Issue
- **Security issues**: Email mubarak.ojewale@kaust.edu.sa privately
- **Direct contact**: mubarak.ojewale@kaust.edu.sa

Thank you for contributing! 🎉
