[project]
name = "binance-data-tools"
version = "0.1.0"
description = "Tools for downloading and processing Binance market data"
requires-python = ">=3.12"

dependencies = [
    "polars",
    "pandas",
    "matplotlib",
    "requests",
    "rich",
    "fastapi",
    "uvicorn[standard]",
    "plotly>=6.3.0",
    "kaleido>=1.0.0",
    "mplfinance>=0.12.10b0",
    "pyarrow>=21.0.0",
    "scipy>=1.16.2",
]

[project.optional-dependencies]
dev = [
    "black>=24.0.0",
    "ruff>=0.6.0",
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
]

[tool.black]
line-length = 100
target-version = ['py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
  | notebooks
)/
'''

[tool.ruff]
line-length = 100
target-version = "py312"

# Exclude a variety of commonly ignored directories
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "venv",
    "notebooks",
]

[tool.ruff.lint]
# Enable pycodestyle (`E`), Pyflakes (`F`), isort (`I`), and pyupgrade (`UP`)
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "SIM",  # flake8-simplify
]

ignore = [
    "E501",  # line too long (handled by black)
]

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py
"tests/**/*.py" = ["S101"]  # Allow assert in tests

[tool.ruff.lint.isort]
known-first-party = ["data_utils", "signal_utils"]

[tool.pytest.ini_options]
testpaths = ["src/research/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=src/research --cov-report=term-missing"


