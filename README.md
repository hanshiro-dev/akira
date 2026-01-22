<div align="center">
  <img src="docs/logo.png" alt="Akira Logo" width="800"/>

  **LLM Security Testing Framework**

  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>

Akira is a security testing framework for LLM-powered applications. Test your AI deployments against prompt injection, jailbreaks, data extraction, denial-of-service, and more.

## Installation

```bash
uv pip install -e ".[dev]"

# Optional: Build Rust extension for performance features
cd rust && maturin develop && cd ..
```

## Three Ways to Run Attacks

### 1. Library API (CI/CD, Scripts)

```python
from akira import scan, create_target

target = create_target("anthropic", api_key="sk-...", model="claude-sonnet-4-20250514")

# Run all attacks
result = await scan(target)

# Run specific category
result = await scan(target, category="dos")

# Run specific attacks
result = await scan(target, attacks=["magic_string"])

print(f"Vulnerabilities: {result.vulnerable}/{result.total}")
for name, r in result.results.items():
    if r.success:
        print(f"  [VULN] {name}: {r.confidence:.0%}")
```

### 2. CLI Commands (Automation, Scripting)

```bash
# Scan with all attacks
akira scan -t https://api.anthropic.com/v1 -T anthropic -k $KEY --all

# Scan specific category
akira scan -t $URL -T anthropic -k $KEY --category dos

# JSON output for pipelines
akira scan -t $URL -T anthropic -k $KEY --all --json > results.json

# Quiet mode + file output
akira scan -t $URL -T anthropic -k $KEY --all --quiet -o results.json

# Run single attack
akira run magic_string -t $URL -T anthropic -k $KEY

# Fingerprint unknown endpoint
akira fingerprint -t https://myapp.com/chat -T api -k $KEY

# Generate HTML report
akira report results.json -o report.html
```

### 3. Interactive Console (Exploration, Manual Testing)

```
$ akira

akira > use magic_string
akira(magic_string) > target anthropic https://api.anthropic.com/v1 -k $KEY
akira(magic_string) > show options
akira(magic_string) > set location system_prompt
akira(magic_string) > run

[*] Executing magic_string...
[+] VULNERABLE (confidence: 95%)
```

**Console Commands:**

| Command | Description |
|---------|-------------|
| `use <attack>` | Select attack module |
| `info` | Show attack details |
| `show modules` | List all attacks |
| `show options` | Show configurable options |
| `set <opt> <val>` | Set option value |
| `target <type> <url>` | Set target |
| `run` | Execute attack |
| `check` | Quick probe |
| `search <term>` | Search attacks |
| `back` | Deselect attack |

## Target Types

| Type | Description |
|------|-------------|
| `anthropic` | Anthropic Claude API |
| `openai` | OpenAI API |
| `api` | Any REST endpoint (custom request/response format) |
| `hf_inference` | HuggingFace Inference API |
| `bedrock` | AWS Bedrock |
| `sagemaker` | AWS SageMaker |

### Generic API Target

For LLM-powered endpoints that aren't direct provider APIs:

```bash
akira scan -t https://myapp.com/chat -T api -k $KEY \
  --request-template '{"message": "$payload"}' \
  --response-path 'data.reply' \
  --all
```

## Attack Categories

| Category | Description |
|----------|-------------|
| `dos` | Denial of service |
| `injection` | Prompt injection |
| `jailbreak` | Safety bypass |
| `extraction` | System prompt / data extraction |
| `evasion` | Detection evasion |
| `poisoning` | Training data poisoning |
| `multiturn` | Multi-turn conversation attacks |
| `tool_abuse` | Function/tool calling exploits |
| `rag_poison` | RAG retrieval poisoning |
| `agent_hijack` | Agentic workflow hijacking |

## Contributing Attacks

Create `akira/attacks/<name>.py`:

```python
from akira import attack, Option
from akira.core.target import Target

@attack(
    name="my_attack",
    description="What it does",
    category="injection",
    severity="high",
    author="you",
)
async def my_attack(
    target: Target,
    payload: Option("Injection payload", default="ignore previous") = None,
):
    response = await target.send(payload)
    return {"vulnerable": "secret" in response, "confidence": 0.9}
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT
