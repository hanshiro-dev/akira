# Contributing to Akira

## Adding a New Attack

1. Create `akira/attacks/<name>.py`
2. Use the `@attack` decorator
3. Submit a PR

### Template

```python
"""Brief description of what this attack does"""

from akira import Option, attack
from akira.core.target import Target

@attack(
    name="my_attack",
    description="One-line description",
    category="injection",  # see categories below
    severity="high",       # info|low|medium|high|critical
    author="your_github_username",
    references=["https://link-to-research-or-cve"],
    tags=["relevant", "tags"],
)
async def my_attack(
    target: Target,
    option_name: Option("What this option does", default="default_value") = None,
):
    """
    Longer description if needed.
    """
    # Your attack logic
    response = await target.send(payload)

    # Return a dict with results
    return {
        "vulnerable": some_condition,
        "confidence": 0.9,  # 0.0 to 1.0
        "response": response,
        "payload": payload,
        # any other details...
    }
```

### Categories

| Category | Description |
|----------|-------------|
| `dos` | Denial of service |
| `injection` | Prompt injection |
| `jailbreak` | Safety bypass |
| `extraction` | Data/prompt extraction |
| `evasion` | Detection evasion |
| `poisoning` | Training data poisoning |
| `multiturn` | Multi-turn conversation attacks |
| `tool_abuse` | Function/tool calling abuse |
| `rag_poison` | RAG retrieval poisoning |
| `agent_hijack` | Agentic workflow hijacking |

### Return Values

Your attack function can return:

- `bool` - `True` = vulnerable, `False` = not vulnerable
- `dict` - `{"vulnerable": bool, "confidence": float, ...}`
- `AttackResult` - Full control over the result object

### Testing Your Attack

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run linter
ruff check akira/attacks/your_attack.py

# Test in console
akira
> use your_attack
> target anthropic https://api.anthropic.com/v1 -k $KEY
> run

# Or via CLI
akira run your_attack -t $URL -T anthropic -k $KEY
```

### Guidelines

- One attack per file
- Include references (papers, blog posts, CVEs)
- Set appropriate severity based on impact
- Test against at least one target type before submitting
- Keep payloads focused - don't bundle unrelated techniques

### Example Attacks to Contribute

We're looking for implementations of:

- OWASP LLM Top 10 vulnerabilities
- Known jailbreak techniques (DAN, etc.)
- Prompt leaking methods
- Context window attacks
- Tool/function calling exploits
- Multi-turn manipulation
- RAG poisoning vectors

## Bug Reports

Open an issue with:

1. Akira version (`akira --version`)
2. Python version
3. Steps to reproduce
4. Expected vs actual behavior

## Questions

Open a discussion or issue. We're happy to help.
