# Anthropic Target

Test Anthropic's Claude models.

## Setup

```
akira> target anthropic https://api.anthropic.com/v1/messages -k $ANTHROPIC_API_KEY
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `-k, --key` | Anthropic API key | Required |
| `-m, --model` | Model ID | `claude-3-sonnet-20240229` |

## Model Selection

```
akira> target anthropic https://api.anthropic.com/v1/messages \
    -k $ANTHROPIC_API_KEY \
    -m claude-3-opus-20240229
```

Available models:
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
- `claude-3-5-sonnet-20241022`

## Example Session

```
akira> target anthropic https://api.anthropic.com/v1/messages \
    -k $ANTHROPIC_API_KEY \
    -m claude-3-opus-20240229
[+] Target configured: anthropic

akira> use dos/magic_string
[+] Using dos/magic_string
    Severity: HIGH

akira> check
[*] Checking if target is Claude...
[+] Target confirmed as Claude model

akira> run
[*] Running magic_string...
```

## Claude-Specific Modules

Some modules are designed specifically for Claude:

- `dos/magic_string` - Tests Claude-specific DoS vulnerability

These modules may have reduced effectiveness against other providers.

## API Differences

Anthropic's API differs from OpenAI's:
- Uses `messages` array format
- Requires `anthropic-version` header
- Different response structure

Akira handles these differences automatically when using the `anthropic` target type.
