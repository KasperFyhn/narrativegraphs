# Contributing

Contributions are welcome! This document explains how to set up a development environment and contribute to `narrativegraphs`.

## Development Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/kasperilarsen/narrativegraphs.git
   cd narrativegraphs
   ```

2. Install the package and dev tools with [uv](https://docs.astral.sh/uv/):

   ```bash
   uv sync
   ```

   This creates `.venv` from the committed `uv.lock`. Prefix commands with `uv run`
   (e.g. `uv run pytest`) or activate `.venv` yourself.

3. Install pre-commit hooks:

   ```bash
   uv run pre-commit install
   ```

## Running Tests

```bash
uv run ./tests/setup.sh  # once, downloads the spaCy model
uv run pytest
```

## Building Documentation

```bash
uv run --group docs mkdocs serve
```

The docs tooling lives in the `docs` dependency group, which `uv sync` does not install by default.

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
