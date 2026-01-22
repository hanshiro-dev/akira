# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Akira is a Python-based CLI framework for LLM security testing, inspired by Metasploit/msfconsole. It tests AI/LLM deployments against known security attacks including prompt injection, jailbreaks, data extraction, and DoS vulnerabilities.

Key design principles:
- Metasploit-style interactive console with commands like `use`, `set`, `run`, `show modules`
- Support for any LLM-powered endpoint (not just direct API providers)
- Attack repository similar to exploitdb
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
akira run dos/magic_string -t https://api.example.com -T openai -k $API_KEY

# List available modules
akira list

# Update attack repository
akira update
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
- `module.py` - Base `Module` class with `check()` and `run()` methods, `AttackCategory` enum (DOS, INJECTION, JAILBREAK, EXTRACTION, EVASION, POISONING), `Severity` enum, `ModuleInfo` and `AttackResult` dataclasses
- `target.py` - Base `Target` class for LLM platforms
- `session.py` - Session state and attack history (auto-persists to storage)
- `registry.py` - Module discovery and registration
- `fuzzy.py` - Fuzzy string matching for module search (Python fallback for Rust)
- `storage.py` - SQLite storage for history, prompts, target profiles, and response cache

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

### Repository (`akira/repository/`)
Attack definition management (YAML-based, git-backed).

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

1. Create file: `akira/attacks/<name>.py` (flat structure, category is defined in code)
2. Subclass `Module` and implement:
   - `info` property returning `ModuleInfo`
   - `_setup_options()` for configurable options
   - `check(target)` for quick vulnerability probe
   - `run(target)` for full attack execution
3. Module auto-registers on import via `registry.load_builtin_attacks()`

Example structure:
```python
class MyAttack(Module):
    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            name="my_attack",
            description="Description here",
            author="Author",
            category=AttackCategory.INJECTION,
            severity=Severity.HIGH,
            references=["https://..."],
            tags=["tag1", "tag2"],
        )

    def _setup_options(self) -> None:
        self.add_option("option_name", "description", default="value")

    async def check(self, target: Target) -> bool:
        # Quick probe, return True if potentially vulnerable
        pass

    async def run(self, target: Target) -> AttackResult:
        # Full attack execution
        pass
```

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
