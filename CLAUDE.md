# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Akira is a Python-based CLI framework for LLM security testing, inspired by Metasploit/msfconsole. It tests AI/LLM deployments against known security attacks including prompt injection, jailbreaks, data extraction, and DoS vulnerabilities.

Key design principles:
- Metasploit-style interactive console with commands like `use`, `set`, `run`, `show modules`
- Library-first API for CI/CD integration and scripting
- Simple decorator-based API for contributing attacks
- Support for any LLM-powered endpoint (not just direct API providers)
- Rust components for performance-critical operations (optional)
- Minimal comments, clean code, colored CLI output

## Build Commands

```bash
# Create virtual environment and install
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Build Rust extension (optional, for performance features)
cd rust && maturin develop && cd ..

# Run linter
ruff check akira/

# Run type checker
mypy akira/

# Run tests
pytest tests/

# Run single test
pytest tests/test_module.py::test_function -v
```

## Usage

### Library API (Recommended for CI/CD)

```python
from akira import scan, create_target

target = create_target("anthropic", api_key="...", model="claude-sonnet-4-20250514")

# Scan with all attacks
result = await scan(target)

# Scan specific category
result = await scan(target, category="dos")

# Scan specific attacks
result = await scan(target, attacks=["magic_string", "prompt_leak"])

print(f"Found {result.vulnerable}/{result.total} vulnerabilities")
```

### CLI

```bash
# Interactive console
akira

# Scan target with all attacks
akira scan -t https://api.anthropic.com/v1 -T anthropic -k $KEY --all

# Scan specific category, output JSON
akira scan -t $URL -T anthropic --category dos --json

# Quiet mode for scripting
akira scan -t $URL -T api --all --quiet -o results.json

# Run single attack
akira run magic_string -t $URL -T anthropic -k $KEY

# Fingerprint target
akira fingerprint -t $URL -T api -k $KEY

# Generate report from scan results
akira report results.json -o report.html

# List available attacks
akira list
```

### Console Commands

| Command | Description |
|---------|-------------|
| `use <module>` | Select an attack module |
| `info` | Show current module details |
| `show modules` | List all attack modules |
| `show options` | Show module options |
| `search [term]` | Fuzzy search modules |
| `set <opt> <val>` | Set module option |
| `target <type> <url>` | Set target endpoint |
| `check` | Quick vulnerability probe |
| `run` | Execute attack |
| `back` | Deselect module |

## Architecture

### Core (`akira/core/`)
- `decorator.py` - `@attack` decorator and `Option` class for defining attacks
- `module.py` - Base `Module` class, `AttackCategory` enum, `Severity` enum, `AttackResult`
- `target.py` - Base `Target` class for LLM platforms
- `registry.py` - Module discovery and auto-registration
- `session.py` - Session state and attack history
- `storage.py` - SQLite storage for history and profiles

### Scanning (`akira/scan.py`)
High-level API: `scan()`, `scan_sync()`, `ScanResult`

### Targets (`akira/targets/`)
- `anthropic.py`, `openai.py` - Provider-specific APIs
- `api.py` - Generic API target for any LLM endpoint
- `huggingface.py` - HuggingFace Inference API
- `aws.py` - Bedrock and SageMaker
- `factory.py` - `create_target()` factory

### Attacks (`akira/attacks/`)
One .py file per attack using the `@attack` decorator.

**Categories:**
- `dos` - Denial of service
- `injection` - Prompt injection
- `jailbreak` - Safety bypass
- `extraction` - Data/prompt extraction
- `evasion` - Detection evasion
- `poisoning` - Training data poisoning
- `multiturn` - Multi-turn attacks
- `tool_abuse` - Function calling exploits
- `rag_poison` - RAG retrieval poisoning
- `agent_hijack` - Agentic workflow hijacking

### CLI (`akira/cli/`)
- `console.py` - Interactive msfconsole-style interface
- `main.py` - Click-based CLI commands

### Rust (`rust/`) - Optional
PyO3 extensions for performance. Gracefully falls back if not built.

## Adding New Attacks

Create `akira/attacks/<name>.py`:

```python
from akira import attack, Option
from akira.core.target import Target

@attack(
    name="my_attack",
    description="What this attack does",
    category="injection",
    severity="high",
    author="your_name",
    references=["https://..."],
    tags=["tag1"],
)
async def my_attack(
    target: Target,
    payload: Option("The payload to use", default="test") = None,
):
    response = await target.send(payload)
    return {
        "vulnerable": "leaked" in response,
        "confidence": 0.9,
        "response": response,
    }
```

See `CONTRIBUTING.md` for full guidelines.

## Adding New Targets

1. Create `akira/targets/<name>.py`
2. Subclass `Target`, implement `validate()`, `send()`, `send_batch()`
3. Add to `akira/targets/factory.py` TARGET_MAP

## CLI Styling

- Rich library for colors/tables
- Prefixes: `[+]` success (green), `[-]` error (red), `[*]` info (yellow), `[!]` warning
- Severity colors: CRITICAL=bold red, HIGH=red, MEDIUM=yellow, LOW=blue, INFO=dim

## Code Style

- Minimal comments
- Type hints throughout
- Async/await for I/O
- `ruff` for linting
- `mypy` for type checking
