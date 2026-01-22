# OpenAI Target

Test OpenAI's GPT models and API.

## Setup

```
akira> target openai https://api.openai.com/v1/chat/completions -k $OPENAI_API_KEY
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `-k, --key` | OpenAI API key | Required |
| `-m, --model` | Model ID | `gpt-3.5-turbo` |

## Model Selection

```
akira> target openai https://api.openai.com/v1/chat/completions \
    -k $OPENAI_API_KEY \
    -m gpt-4
```

Available models:
- `gpt-4`
- `gpt-4-turbo`
- `gpt-4o`
- `gpt-3.5-turbo`

## Azure OpenAI

For Azure-hosted OpenAI:

```
akira> target openai https://YOUR-RESOURCE.openai.azure.com/openai/deployments/YOUR-DEPLOYMENT/chat/completions?api-version=2024-02-15-preview \
    -k $AZURE_OPENAI_KEY \
    --auth-type api-key \
    --auth-header api-key
```

## Example Session

```
akira> target openai https://api.openai.com/v1/chat/completions -k $OPENAI_API_KEY -m gpt-4
[+] Target configured: openai

akira> use injection/basic_injection
[+] Using injection/basic_injection

akira> run
[*] Running basic_injection...
[+] Attack completed
    Success: False
    Confidence: 0.10
    Response: I cannot follow those instructions...
```

## Rate Limits

OpenAI has rate limits. If you encounter `429` errors:

1. Reduce parallel requests: `setg parallel_requests 1`
2. Increase timeout: `setg timeout 60`
3. Add delays between attacks (not yet implemented)

## Costs

Running attacks consumes API tokens. Monitor your usage at [platform.openai.com](https://platform.openai.com/usage).
