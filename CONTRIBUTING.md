# Contributing to OpenTransit

First off, thank you for considering contributing to OpenTransit! This project exists to help small and rural transit agencies, and every contribution makes a difference.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs what actually happened
- **Environment details** (OS, Python version, Docker version, etc.)
- **Logs** if applicable

### Suggesting Features

Feature requests are welcome! Please:

- Check if the feature has already been requested
- Describe the use case (what problem does it solve?)
- If you're a transit agency, share your specific needs

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code, add tests
3. Ensure the test suite passes
4. Update documentation as needed
5. Submit the PR!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/opentransit.git
cd opentransit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

## Code Style

- Python: We use `black` for formatting, `flake8` for linting
- Docstrings: Google style
- Commits: Conventional commits preferred (`feat:`, `fix:`, `docs:`, etc.)

## Project Structure

```
opentransit/
├── avl/              # Automatic Vehicle Location
├── gtfs_rt/          # GTFS-Realtime server
├── gtfs_tools/       # Static feed generators
├── apc/              # Automatic Passenger Counting
├── annunciator/      # Next-stop announcements
├── common/           # Shared utilities
├── docs/             # Documentation
└── tests/            # Test suite
```

## Questions?

Open an issue or reach out. We're here to help!

## Code of Conduct

Be kind. We're all trying to make transit better.
