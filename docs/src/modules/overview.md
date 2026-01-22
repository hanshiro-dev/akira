# Module Overview

Akira's attack modules are organized by vulnerability category.

## Categories

| Category | Description | Risk Level |
|----------|-------------|------------|
| `injection` | Prompt injection attacks | High |
| `jailbreak` | Safety/guardrail bypass | High |
| `extraction` | Data and prompt leakage | Medium-High |
| `dos` | Denial of service | High |

## Module Structure

Each module provides:

- **Name** - Unique identifier (`category/name`)
- **Description** - What the attack tests
- **Severity** - Risk level if successful
- **Options** - Configurable parameters
- **Check** - Quick vulnerability probe
- **Run** - Full attack execution

## Listing Modules

```
akira> show modules

                               Available Modules
┌───────────────────────────────┬────────────┬──────────┬──────────────────────┐
│ Name                          │ Category   │ Severity │ Description          │
├───────────────────────────────┼────────────┼──────────┼──────────────────────┤
│ dos/magic_string              │ dos        │ high     │ Tests for Claude...  │
│ extraction/system_prompt_leak │ extraction │ medium   │ Attempts to extr...  │
│ injection/basic_injection     │ injection  │ high     │ Tests for basic...   │
│ jailbreak/dan_jailbreak       │ jailbreak  │ high     │ Tests resistance...  │
└───────────────────────────────┴────────────┴──────────┴──────────────────────┘
```

## Built-in Modules

### Injection

- [`basic_injection`](./injection.md) - Tests basic prompt injection vulnerabilities

### Jailbreak

- [`dan_jailbreak`](./jailbreak.md) - DAN-style jailbreak attempts

### Extraction

- [`system_prompt_leak`](./extraction.md) - System prompt extraction attempts

### DoS

- [`magic_string`](./dos.md) - Claude magic string DoS vulnerability

## Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| CRITICAL | Immediate exploitation risk | Urgent remediation |
| HIGH | Significant security impact | High priority fix |
| MEDIUM | Moderate risk | Should be addressed |
| LOW | Minor concern | Consider fixing |
| INFO | Informational | No action needed |

## Module Selection

```bash
# Use a specific module
akira> use injection/basic_injection

# View module details
akira> info

# See module options
akira> show options
```

## Common Options

Many modules share common options:

| Option | Description |
|--------|-------------|
| `canary` | Marker string to detect success |
| `timeout` | Request timeout |
| `use_fuzzing` | Enable payload fuzzing |
| `fuzz_count` | Number of fuzz variations |
| `variant` | Attack variant to use |

## Attack Results

All modules return standardized results:

```python
AttackResult(
    success=True,           # Did the attack succeed?
    confidence=0.85,        # How confident (0.0-1.0)
    payload_used="...",     # The payload sent
    response="...",         # LLM response
    details={...}           # Additional metadata
)
```
