# Python Code Quality Guide

This project uses professional Python code quality tools to maintain clean, consistent code.

## Tools Used

- **Black**: Automatic code formatter (line length: 100)
- **Ruff**: Fast Python linter with auto-fix capabilities
- **pytest**: Testing framework with coverage reporting

## Quick Start

### Using Make (Recommended)

```bash
# Format code with Black
make py-format

# Lint code with Ruff (and auto-fix)
make py-lint

# Check formatting and linting (no changes)
make py-check

# Run tests
make py-test

# Do everything
make py-all
```

### Manual Commands (Inside Docker)

```bash
# Enter the dev container
make shell-dev

# Format code
black src/research server

# Lint code
ruff check --fix src/research server

# Check without making changes
black --check src/research server
ruff check src/research server

# Run tests
pytest src/research/tests
```

## CI/CD Integration

### Automated Checks

The Python CI pipeline runs on every push and pull request:

1. **Formatting Check**: Ensures code is formatted with Black
2. **Linting**: Checks code quality with Ruff
3. **Tests**: Runs pytest suite

### Auto-formatting (Pull Requests Only)

On pull requests, if formatting/linting issues are found, the CI will:
- Automatically format code with Black
- Auto-fix issues with Ruff
- Commit the changes back to the PR

## Configuration

All configuration is in `pyproject.toml`:

- **Black**: Line length 100, excludes notebooks
- **Ruff**: Comprehensive rule set (pycodestyle, pyflakes, isort, pyupgrade, bugbear, etc.)
- **pytest**: Test discovery and coverage reporting

## Pre-commit Hooks (Optional)

To run quality checks automatically before each commit:

```bash
# Inside dev container
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## IDE Integration

### VS Code

Add to `.vscode/settings.json`:

```json
{
  "python.formatting.provider": "black",
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### PyCharm

1. Install Black plugin
2. Install Ruff plugin
3. Enable "Format on Save"

## Excluded Directories

The following are excluded from formatting/linting:
- `notebooks/` - Jupyter notebooks (use nbqa if needed)
- `.venv/`, `build/`, `dist/` - Build artifacts
- `.git/`, `.mypy_cache/`, `.ruff_cache/` - Tool directories

## Writing Tests

Place tests in `src/research/tests/`:

```python
# test_example.py
def test_something():
    result = my_function()
    assert result == expected_value
```

Run with:
```bash
make py-test
```
