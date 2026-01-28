# Contributing

Contributions are welcome! This document explains how to set up a development environment and contribute to `narrativegraphs`.

## Development Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/kasperilarsen/narrativegraphs.git
    cd narrativegraphs
    ```

2. Create a virtual environment and install in editable mode:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -e ".[dev]"
    ```

3. Install pre-commit hooks:

    ```bash
    pre-commit install
    ```

## Running Tests

```bash
pytest
```

## Building Documentation

```bash
mkdocs serve
```

## Code Style

This project uses:

- `ruff` for linting and formatting Python code
- Type hints throughout (checked with `mypy`)
- Google-style docstrings
- `eslint` for linting React/TypeScript code and `prettier` for formatting 
- 

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with tests
4. Run the test suite and linters
5. Submit a pull request

## Questions?

Open an issue on GitHub or reach out directly.
