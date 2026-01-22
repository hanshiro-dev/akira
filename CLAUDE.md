# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Akira is a Python-based CLI framework for LLM security testing, inspired by Metasploit/msfconsole. It tests AI/LLM deployments against known security attacks including prompt injection, jailbreaks, data extraction, and DoS vulnerabilities.

Key design principles:
- Metasploit-style interactive console with commands like `use`, `set`, `run`, `show modules`
- Support for any LLM-powered endpoint (not just direct API providers)
- Simple decorator-based API for contributing attacks
- Rust components for performance-critical operations
- Minimal comments, clean code, colored CLI output

## Build Commands

```bash
# Create virtual environment and install (use uv, not pip)
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

# Run single test file or test function
pytest tests/test_module.py
pytest tests/test_module.py::test_specific_function -v
```

## Running Akira

```bash
# Interactive console (msfconsole-style)
akira

# Run specific module directly
akira run magic_string -t https://api.anthropic.com/v1 -T anthropic -k $ANTHROPIC_API_KEY

# List available modules
akira list
```

### Console Commands

| Command | Description |
|---------|-------------|
| `use <module>` | Select an attack module |
| `info` | Show current module details |
| `show modules` | List all attack modules |
| `show options` | Show module options |
| `search [term]` | Fuzzy search (interactive if no term) |
| `set <opt> <val>` | Set module option |
| `target <type> <url>` | Set target endpoint |
| `profile <action> <name>` | Save/load/delete target profiles |
| `profiles` | List saved target profiles |
| `check` | Quick vulnerability probe |
| `run` | Execute attack |
| `back` | Deselect module |
| `history` | Show attack history |
| `stats` | Show session and database stats |

## Architecture

### Core (`akira/core/`)
- `decorator.py` - `@attack` decorator and `Option` class for defining attacks
- `module.py` - Base `Module` class, `AttackCategory` enum, `Severity` enum, `AttackResult` dataclass
- `target.py` - Base `Target` class for LLM platforms
- `registry.py` - Module discovery and auto-registration
- `session.py` - Session state and attack history
- `storage.py` - SQLite storage for history and target profiles

### Targets (`akira/targets/`)
Implementations for different LLM platforms:
- `api.py` - **Generic API target** for any LLM-powered endpoint with flexible request/response templates
- `openai.py`, `anthropic.py` - Provider-specific APIs
- `huggingface.py` - HuggingFace Inference API and local models
- `aws.py` - AWS Bedrock and SageMaker
- `factory.py` - `create_target()` factory function

**Important:** The `api` target supports arbitrary LLM-powered endpoints (e.g., `xyz.com/predict` using Claude behind the scenes) via:
- `--request-template` - Custom JSON request format with `$payload` placeholder
- `--response-path` - JSON path to extract response (e.g., `data.output.text`)
- `--auth-type` - Authentication method (`bearer`, `header`, `query`, `basic`)

### Attacks (`akira/attacks/`)
Attack modules in a flat structure (one .py file per attack). Categories defined in code:
- `dos` - Denial of service (e.g., Claude magic string attacks)
- `injection` - Prompt injection attacks
- `extraction` - System prompt and data extraction
- `jailbreak` - Safety bypass attempts (DAN-style)
- `evasion` - Detection evasion techniques
- `poisoning` - Training data poisoning attacks

### Rust Core (`rust/`)
Performance-critical operations via PyO3 (optional, graceful fallback if not built):
- `fuzzer.rs` - Payload mutation and fuzzing
- `matcher.rs` - Fast multi-pattern matching (Aho-Corasick)
- `analyzer.rs` - Parallel response analysis
- `fuzzy.rs` - Fuzzy string matching for module search

Check for Rust availability with `HAS_RUST` flag in modules.

### CLI (`akira/cli/`)
- `console.py` - Interactive msfconsole-style interface with Rich formatting
- `main.py` - Click-based CLI entry points

### Storage (`akira/core/storage.py`)
SQLite-based persistent storage in `~/.akira/akira.db`:

```
~/.akira/
└── akira.db          # SQLite database
```

**Tables:**
- `attack_history` - Persisted attack results (timestamp, module, target, success, payload, response)
- `prompt_cache` - Cached prompts by key
- `target_profiles` - Saved target configurations for reuse
- `response_cache` - Cached API responses with TTL

**Usage:**
```python
from akira.core.storage import get_storage

storage = get_storage()
storage.save_history(module, target_type, url, success, confidence, payload, response)
storage.save_target_profile("prod-api", "openai", "https://...", {"model": "gpt-4"})
storage.cache_response(request_data, response, ttl_seconds=3600)
```

## CLI Styling Conventions

- Use Rich library for terminal colors and tables
- Status prefixes: `[+]` success (green), `[-]` error (red), `[*]` info (yellow/blue), `[!]` warning
- Severity colors: CRITICAL=bold red, HIGH=red, MEDIUM=yellow, LOW=blue, INFO=dim
- Banner uses cyberpunk aesthetic (red/cyan) inspired by `docs/logo.png`
- Avoid emojis unless user explicitly requests them

## Adding New Attack Modules

Create `akira/attacks/<name>.py` using the `@attack` decorator:

```python
from akira import attack, Option
from akira.core.target import Target

@attack(
    name="my_attack",
    description="What this attack does",
    category="injection",  # dos|injection|jailbreak|extraction|evasion|poisoning
    severity="high",       # info|low|medium|high|critical
    author="your_name",
    references=["https://..."],
    tags=["tag1", "tag2"],
)
async def my_attack(
    target: Target,
    payload: Option("The payload to inject", default="test") = None,
    iterations: Option("Number of attempts", default=1) = None,
):
    response = await target.send(payload)

    # Return bool, dict, or AttackResult
    return {
        "vulnerable": "secret" in response,
        "confidence": 0.9,
        "response": response,
    }
```

**Return values:**
- `bool` - True = vulnerable, False = not vulnerable
- `dict` - `{"vulnerable": bool, "confidence": float, "response": str, ...}`
- `AttackResult` - Full control

Module auto-registers on import. See `akira/attacks/magic_string.py` for a complete example.

## Adding New Targets

1. Create file in `akira/targets/<name>.py`
2. Subclass `Target` and implement:
   - `target_type` property
   - `validate()` for connection/auth testing
   - `send(payload)` and `send_batch(payloads)`
3. Register in `akira/targets/factory.py` TARGET_MAP

## Code Style

- Minimal comments - only where logic isn't self-evident
- Use type hints throughout
- Prefer async/await for I/O operations
- Use `HAS_RUST` pattern for optional Rust acceleration:
  ```python
  try:
      import akira_core
      HAS_RUST = True
  except ImportError:
      HAS_RUST = False
  ```
