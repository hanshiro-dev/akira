# Basic Concepts

Understanding Akira's core concepts will help you use it effectively.

## Modules

Modules are individual attack implementations. Each module:

- Targets a specific vulnerability type
- Has configurable options
- Returns structured results

Modules are organized by category:

| Category | Description |
|----------|-------------|
| `injection` | Prompt injection attacks |
| `jailbreak` | Safety bypass attempts |
| `extraction` | Data/prompt leakage |
| `dos` | Denial of service |

Module naming follows the pattern: `category/name`

```
injection/basic_injection
jailbreak/dan_jailbreak
extraction/system_prompt_leak
dos/magic_string
```

## Targets

Targets represent the LLM endpoint you're testing. Akira supports:

- **Direct API providers** - OpenAI, Anthropic, HuggingFace
- **Cloud platforms** - AWS Bedrock, SageMaker
- **Custom endpoints** - Any LLM-powered API

The generic `api` target type can test any HTTP endpoint that wraps an LLM.

## Sessions

A session tracks your current state:

- Selected module
- Configured target
- Attack history
- Global options

Sessions persist attack history to SQLite for later analysis.

## Attack Results

Every attack returns an `AttackResult` with:

| Field | Description |
|-------|-------------|
| `success` | Whether the attack succeeded |
| `confidence` | Confidence score (0.0 to 1.0) |
| `payload_used` | The payload that was sent |
| `response` | The LLM's response |
| `details` | Additional metadata |

## Severity Levels

Modules are rated by severity:

| Level | Color | Description |
|-------|-------|-------------|
| CRITICAL | Red (bold) | Immediate exploitation risk |
| HIGH | Red | Significant security impact |
| MEDIUM | Yellow | Moderate risk |
| LOW | Blue | Minor concern |
| INFO | Gray | Informational only |

## The Attack Workflow

1. **Select module** - `use category/module_name`
2. **Configure options** - `set option value`
3. **Set target** - `target type url [options]`
4. **Check** (optional) - `check` for quick probe
5. **Run** - `run` to execute full attack
6. **Analyze** - Review results and history

## Storage

Akira stores data in `~/.akira/`:

```
~/.akira/
└── akira.db    # SQLite database
```

The database contains:
- Attack history (persistent across sessions)
- Target profiles (saved configurations)
- Prompt cache
- Response cache
