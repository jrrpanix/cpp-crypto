# Python Code Quality - Quick Reference

## Daily Commands

```bash
# Format code
make py-format

# Lint code (auto-fix)
make py-lint

# Check (no changes - like CI)
make py-check

# Run tests
make py-test

# Do everything
make py-all
```

## Configuration

All settings in `pyproject.toml`:
- Line length: **100**
- Target: **Python 3.12**
- Excludes: `notebooks/`

## What Gets Checked

- ✅ Code formatting (Black)
- ✅ Import sorting (Ruff isort)
- ✅ Deprecated syntax (Ruff pyupgrade)
- ✅ Common bugs (Ruff bugbear)
- ✅ Comprehension issues (Ruff)
- ✅ Simplification opportunities (Ruff)

## CI Behavior

### Push/PR to main:
- Checks formatting ❌/✅
- Checks linting ❌/✅
- Runs tests ❌/✅

### PR Only:
- **Auto-formats** if checks fail
- **Auto-commits** to your PR

## Pre-commit (Optional)

```bash
# Inside dev container
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## Files Modified

- ✅ `pyproject.toml` - Config
- ✅ `.github/workflows/python-ci.yml` - CI
- ✅ `.pre-commit-config.yaml` - Hooks
- ✅ `Makefile` - Commands
- ✅ `docs/PYTHON_QUALITY.md` - Guide
