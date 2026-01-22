# CLI Reference

Command-line interface reference.

## Global Commands

### akira

Start the interactive console:

```bash
akira
```

### akira --version

Show version information:

```bash
akira --version
```

### akira --help

Show help:

```bash
akira --help
```

## Commands

### akira list

List all available attack modules:

```bash
akira list
```

Output shows module name, category, severity, and description.

### akira run

Run a specific module non-interactively:

```bash
akira run <module> [options]
```

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--target` | `-t` | Target URL |
| `--target-type` | `-T` | Target type (openai, anthropic, api, etc.) |
| `--key` | `-k` | API key |
| `--model` | `-m` | Model identifier |
| `--set` | | Set module option (name=value) |
| `--request-template` | | Custom request JSON |
| `--response-path` | | JSON path to response |
| `--auth-type` | | Authentication type |
| `--auth-header` | | Custom auth header |
| `--timeout` | | Request timeout |
| `--output` | `-o` | Output format (json, table) |

#### Examples

```bash
# Basic usage
akira run injection/basic_injection \
    -t https://api.openai.com/v1/chat/completions \
    -T openai \
    -k $OPENAI_API_KEY

# With options
akira run injection/basic_injection \
    -t https://api.openai.com/v1/chat/completions \
    -T openai \
    -k $OPENAI_API_KEY \
    --set canary=MY_TEST_STRING \
    --set use_fuzzing=true

# Custom API
akira run extraction/system_prompt_leak \
    -t https://myapi.com/chat \
    -T api \
    --request-template '{"message": "$payload"}' \
    --response-path 'data.reply' \
    -k $API_KEY

# JSON output
akira run jailbreak/dan_jailbreak \
    -t https://api.anthropic.com/v1/messages \
    -T anthropic \
    -k $ANTHROPIC_API_KEY \
    -o json
```

### akira update

Update attack repository from remote:

```bash
akira update
```

Options:

| Option | Description |
|--------|-------------|
| `--repo` | Repository URL |
| `--force` | Force update |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Default OpenAI API key |
| `ANTHROPIC_API_KEY` | Default Anthropic API key |
| `HF_TOKEN` | HuggingFace API token |
| `AWS_ACCESS_KEY_ID` | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials |
| `AKIRA_DATA_DIR` | Custom data directory |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Target connection failed |
| 4 | Authentication failed |
| 5 | Module not found |

## Output Formats

### Table (default)

```
[+] Attack completed

    Success:    True
    Confidence: 0.95
    Payload:    Ignore all previous...
    Response:   CANARY_STRING
```

### JSON

```bash
akira run module -o json
```

```json
{
  "success": true,
  "confidence": 0.95,
  "payload_used": "...",
  "response": "...",
  "details": {},
  "module": "injection/basic_injection",
  "target": "https://api.openai.com/..."
}
```
