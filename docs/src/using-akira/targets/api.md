# Generic API Target

The `api` target type allows testing any HTTP endpoint that wraps an LLM, regardless of the underlying provider.

## Use Cases

- Custom LLM deployments
- LLM-powered chatbots
- AI features in web applications
- Internal tools using LLMs
- Third-party AI services

## Basic Usage

```
akira> target api https://example.com/api/chat -k YOUR_API_KEY
```

## Request Template

Customize the request format with `--request-template`:

```
akira> target api https://example.com/chat \
    --request-template '{"prompt": "$payload", "max_tokens": 100}'
```

The `$payload` placeholder is replaced with the attack payload.

### Complex Templates

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "$payload"}
  ],
  "temperature": 0.7,
  "stream": false
}
```

## Response Path

Extract the response from nested JSON:

```
akira> target api https://example.com/chat \
    --response-path 'data.choices.0.text'
```

### Path Examples

| Response Structure | Path |
|-------------------|------|
| `{"response": "text"}` | `response` |
| `{"data": {"text": "..."}}` | `data.text` |
| `{"choices": [{"message": {"content": "..."}}]}` | `choices.0.message.content` |
| `{"result": {"output": ["text"]}}` | `result.output.0` |

## Authentication

### Bearer Token (Default)

```
akira> target api https://example.com/chat -k YOUR_TOKEN
# Sends: Authorization: Bearer YOUR_TOKEN
```

### API Key Header

```
akira> target api https://example.com/chat \
    -k YOUR_KEY \
    --auth-type api-key
# Sends: X-API-Key: YOUR_KEY
```

### Custom Header

```
akira> target api https://example.com/chat \
    -k YOUR_KEY \
    --auth-type api-key \
    --auth-header X-Custom-Auth
# Sends: X-Custom-Auth: YOUR_KEY
```

### No Authentication

```
akira> target api https://example.com/public-chat --auth-type none
```

## Full Example

Testing a custom chatbot API:

```
akira> target api https://mycompany.com/api/v1/assistant \
    --request-template '{"query": "$payload", "session_id": "test-123", "context": []}' \
    --response-path 'answer.text' \
    --auth-type api-key \
    --auth-header X-Assistant-Key \
    -k sk-assistant-key-12345

akira> use injection/basic_injection
akira> run
```

## Tips

1. **Test manually first** - Use `curl` to understand the API format before configuring Akira
2. **Check response structure** - Examine actual API responses to determine the correct response path
3. **Handle arrays** - Use `.0`, `.1`, etc. to access array elements in the response path
4. **URL encode if needed** - Some APIs may require URL-encoded payloads in the template
