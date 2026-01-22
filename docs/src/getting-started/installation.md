# Installation

## Requirements

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Rust toolchain (optional, for performance extensions)

## Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/akira.git
cd akira

# Create virtual environment and install
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Development Install

For development with all optional dependencies:

```bash
uv pip install -e ".[dev]"
```

This includes:
- `pytest` - Testing
- `ruff` - Linting
- `mypy` - Type checking

## Rust Extensions (Optional)

Akira includes optional Rust extensions for performance-critical operations like fuzzing and pattern matching. These are not required but improve performance significantly.

```bash
# Install maturin
uv pip install maturin

# Build and install Rust extension
cd rust
maturin develop --release
cd ..
```

To verify Rust extensions are available:

```bash
python -c "import akira_core; print('Rust extensions loaded')"
```

## Verify Installation

```bash
# Check version
akira --version

# List available modules
akira list
```

You should see output like:

```
                               Available Modules
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name                      ┃ Category   ┃ Severity ┃ Description              ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ dos/magic_string          │ dos        │ high     │ Tests for Claude magic   │
│                           │            │          │ string DoS vulnerability │
...
```

## Troubleshooting

### `uv` not found

Install uv first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Module import errors

Ensure you're in the virtual environment:

```bash
source .venv/bin/activate
```

### Rust build fails

Make sure you have the Rust toolchain installed:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
