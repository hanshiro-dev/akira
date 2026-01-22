# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Akira is a Python-based CLI framework for LLM security testing, inspired by Metasploit/msfconsole. It verifies AI/LLM deployments against known security attacks including prompt injection, jailbreaks, data extraction, and DoS vulnerabilities.

## Build Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Build Rust extension (required for fuzzing/performance features)
cd rust && maturin develop && cd ..

# Run linter
ruff check akira/

# Run type checker
mypy akira/

# Run tests
pytest tests/
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

## Architecture

### Core (`akira/core/`)
- `module.py` - Base `Module` class for attacks with `check()` and `run()` methods
- `target.py` - Base `Target` class for different LLM platforms
- `session.py` - Session state management and attack history
- `registry.py` - Module discovery and registration

### Targets (`akira/targets/`)
Implementations for different LLM platforms:
- `api.py` - Generic REST API endpoints
- `openai.py`, `anthropic.py` - Provider-specific APIs
- `huggingface.py` - HuggingFace Inference API and local models
- `aws.py` - AWS Bedrock and SageMaker
- `factory.py` - `create_target()` factory function

### Modules (`akira/modules/`)
Attack modules organized by category:
- `dos/` - Denial of service (e.g., magic string attacks)
- `injection/` - Prompt injection attacks
- `extraction/` - System prompt and data extraction
- `jailbreak/` - Safety bypass attempts (DAN-style)

### Rust Core (`rust/`)
Performance-critical operations via PyO3:
- `fuzzer.rs` - Payload mutation and fuzzing (unicode injection, homoglyphs, token splitting)
- `matcher.rs` - Fast multi-pattern matching (Aho-Corasick)
- `analyzer.rs` - Parallel response analysis

### Repository (`akira/repository/`)
Attack definition management (YAML-based, git-backed):
- Pull attacks from remote repositories
- Search and filter by category/tags
- Import/export attack definitions

## Adding New Attack Modules

1. Create file in appropriate category: `akira/modules/<category>/<name>.py`
2. Subclass `Module` and implement:
   - `info` property returning `ModuleInfo`
   - `_setup_options()` for configurable options
   - `check(target)` for quick vulnerability probe
   - `run(target)` for full attack execution
3. Module auto-registers on import via `registry.load_builtin_modules()`

## Adding New Targets

1. Create file in `akira/targets/<name>.py`
2. Subclass `Target` and implement:
   - `target_type` property
   - `validate()` for connection/auth testing
   - `send(payload)` and `send_batch(payloads)`
3. Register in `akira/targets/factory.py` TARGET_MAP
