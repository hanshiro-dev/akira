# Targets

Targets represent the LLM endpoint you want to test. Akira supports multiple target types for different LLM providers and custom deployments.

## Target Types

| Type | Description |
|------|-------------|
| `api` | Generic REST API (any LLM-powered endpoint) |
| `openai` | OpenAI API |
| `anthropic` | Anthropic Claude API |
| `hf` | HuggingFace local model |
| `hf_inference` | HuggingFace Inference API |
| `bedrock` | AWS Bedrock |
| `sagemaker` | AWS SageMaker endpoint |

## Setting a Target

Basic syntax:

```
target <type> <endpoint> [options]
```

### Common Options

| Option | Description |
|--------|-------------|
| `-k, --key` | API key |
| `-m, --model` | Model identifier |
| `--request-template` | Custom request JSON template |
| `--response-path` | JSON path to extract response |
| `--auth-type` | Authentication type |
| `--auth-header` | Custom auth header name |

## Examples

### OpenAI

```
akira> target openai https://api.openai.com/v1/chat/completions -k $OPENAI_API_KEY -m gpt-4
```

### Anthropic

```
akira> target anthropic https://api.anthropic.com/v1/messages -k $ANTHROPIC_API_KEY -m claude-3-opus-20240229
```

### Generic API

For any LLM-powered endpoint:

```
akira> target api https://mycompany.com/api/chat \
    --request-template '{"message": "$payload", "user_id": "test"}' \
    --response-path 'data.reply.text' \
    -k my-api-key
```

## Request Templates

The `$payload` placeholder is replaced with the attack payload:

```json
{
  "message": "$payload",
  "context": "You are a helpful assistant",
  "temperature": 0.7
}
```

## Response Path

Extract the LLM response from nested JSON using dot notation:

```
--response-path 'choices.0.message.content'
--response-path 'data.response.text'
--response-path 'output'
```

## Authentication Types

| Type | Description |
|------|-------------|
| `bearer` | Authorization: Bearer <key> |
| `api-key` | X-API-Key: <key> (or custom header) |
| `basic` | HTTP Basic Auth |
| `none` | No authentication |

Custom header:

```
--auth-type api-key --auth-header X-Custom-Auth
```

## Verifying Target

After setting a target, verify connectivity:

```
akira> check
```

This sends a simple probe to ensure the target is reachable and responding.

## Target Information

View current target:

```
akira> show options
```

The target information appears at the top of the options display.

## Next Steps

See specific target documentation:

- [Generic API](./targets/api.md)
- [OpenAI](./targets/openai.md)
- [Anthropic](./targets/anthropic.md)
- [HuggingFace](./targets/huggingface.md)
- [AWS](./targets/aws.md)
