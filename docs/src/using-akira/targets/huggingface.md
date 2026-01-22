# HuggingFace Targets

Test HuggingFace models via Inference API or locally.

## HuggingFace Inference API

### Setup

```
akira> target hf_inference https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf \
    -k $HF_TOKEN
```

### Options

| Option | Description |
|--------|-------------|
| `-k, --key` | HuggingFace API token |
| `-m, --model` | Model ID (in URL) |

### Popular Models

```bash
# Llama 2
target hf_inference https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf -k $HF_TOKEN

# Mistral
target hf_inference https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1 -k $HF_TOKEN

# Falcon
target hf_inference https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct -k $HF_TOKEN
```

## Local Models

### Setup

For locally running models (via text-generation-webui, llama.cpp server, etc.):

```
akira> target hf http://localhost:5000/api/generate
```

### Common Local Endpoints

| Tool | Default Endpoint |
|------|-----------------|
| text-generation-webui | `http://localhost:5000/api/v1/generate` |
| llama.cpp server | `http://localhost:8080/completion` |
| Ollama | `http://localhost:11434/api/generate` |

### Custom Request Format

Local servers may have different request formats:

```
akira> target api http://localhost:5000/api/generate \
    --request-template '{"prompt": "$payload", "max_new_tokens": 200}' \
    --response-path 'results.0.text' \
    --auth-type none
```

## Example Session

```
akira> target hf_inference https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf -k $HF_TOKEN
[+] Target configured: hf_inference

akira> use jailbreak/dan_jailbreak
akira> set variant 3
akira> run
```

## Rate Limits

HuggingFace Inference API has rate limits for free tier:
- Consider using Pro subscription for testing
- Or run models locally for unlimited testing
