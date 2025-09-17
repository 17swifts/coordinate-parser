# GitHub Actions Workflows

This repository uses a simple 3-workflow CI/CD pipeline:

## Workflows

### 1. **CI** (`ci.yml`)

- **Triggers:** Push to main, Pull Requests
- **Purpose:** Run tests, linting, and type checking
- Tests on Python 3.11, 3.12, 3.13
- Runs pytest, black, ruff, and mypy

### 2. **Build** (`build.yml`)

- **Triggers:** Push to main, version tags
- **Purpose:** Build and validate package distributions
- Creates wheel and source distributions
- Validates with twine

### 3. **Release** (`release.yml`)

- **Triggers:** GitHub Release creation
- **Purpose:** Publish to PyPI
- Uses trusted publishing (no API keys needed)

## Setup for PyPI Publishing

1. **Register on PyPI**: Go to https://pypi.org and create an account

2. **Set up Trusted Publishing**:

   - Go to PyPI → Account → Publishing
   - Add publisher with:
     - Owner: `17swifts`
     - Repository: `coordinate-parser`
     - Workflow: `release.yml`

3. **Create a Release**:
   - Update version in `pyproject.toml`
   - Create git tag: `git tag v0.2.0`
   - Push tag: `git push origin v0.2.0`
   - Create GitHub Release from the tag
   - Package will automatically publish to PyPI!

## Local Development

```bash
# Install dependencies
uv sync --extra dev

# Install pre-commit hooks (one-time setup)
uv run pre-commit install

# Run tests
uv run pytest

# Run linting manually (optional - pre-commit does this automatically)
uv run black src/ tests/
uv run ruff check src/ tests/

# Build package
uv build
```

## Pre-commit Hooks

Pre-commit hooks automatically run before each commit to ensure code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **Tests**: Run full test suite
- **General checks**: Trailing whitespace, YAML/TOML validation

```bash
# Install hooks (one-time)
uv run pre-commit install

# Run hooks manually on all files
uv run pre-commit run --all-files

# Skip hooks for a specific commit (use sparingly!)
git commit --no-verify -m "commit message"
```

That's it! Simple and focused. 🚀
