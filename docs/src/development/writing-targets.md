# Writing Targets

Create custom target implementations for new LLM platforms.

## Quick Start

Create a new target in `akira/targets/<name>.py`:

```python
from akira.core.target import Target, TargetType
import httpx


class MyTarget(Target):
    def __init__(self, endpoint: str, api_key: str, **kwargs):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = kwargs.get("model", "default-model")
        self._client = httpx.AsyncClient(timeout=30.0)

    @property
    def target_type(self) -> TargetType:
        return TargetType.CUSTOM  # Or add new type to enum

    async def validate(self) -> bool:
        """Test connectivity and authentication."""
        try:
            response = await self._client.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"prompt": "test", "max_tokens": 1},
            )
            return response.status_code == 200
        except Exception:
            return False

    async def send(self, payload: str) -> str:
        """Send a payload and return the response."""
        response = await self._client.post(
            self.endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "prompt": payload,
                "model": self.model,
                "max_tokens": 500,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["output"]["text"]

    async def send_batch(self, payloads: list[str]) -> list[str]:
        """Send multiple payloads (optional optimization)."""
        # Default: sequential execution
        return [await self.send(p) for p in payloads]

    def __repr__(self) -> str:
        return f"MyTarget({self.endpoint})"
```

## Registering the Target

Add to `akira/targets/factory.py`:

```python
from akira.targets.my_target import MyTarget

TARGET_MAP = {
    # ... existing targets
    "my_target": MyTarget,
}
```

And update `TargetType` enum if needed:

```python
# akira/core/target.py
class TargetType(Enum):
    # ... existing types
    CUSTOM = "custom"
    MY_TARGET = "my_target"
```

## Target Interface

### Required Methods

```python
@property
def target_type(self) -> TargetType:
    """Return the target type enum value."""
    ...

async def validate(self) -> bool:
    """Test if target is reachable and authenticated."""
    ...

async def send(self, payload: str) -> str:
    """Send payload to LLM and return response text."""
    ...
```

### Optional Methods

```python
async def send_batch(self, payloads: list[str]) -> list[str]:
    """Send multiple payloads. Override for batch API support."""
    return [await self.send(p) for p in payloads]
```

## Configuration

### Constructor Parameters

Accept flexible configuration:

```python
def __init__(
    self,
    endpoint: str,
    api_key: str | None = None,
    model: str | None = None,
    timeout: int = 30,
    **kwargs,  # For additional options
):
    self.endpoint = endpoint
    self.api_key = api_key
    self.model = model or "default"
    self.config = kwargs
```

### From Factory

The factory passes CLI arguments:

```python
# User runs:
# target my_target https://api.example.com -k KEY -m model-v1 --custom-opt value

# Factory calls:
target = MyTarget(
    endpoint="https://api.example.com",
    api_key="KEY",
    model="model-v1",
    custom_opt="value",
)
```

## Error Handling

Handle common errors gracefully:

```python
async def send(self, payload: str) -> str:
    try:
        response = await self._client.post(...)
        response.raise_for_status()
        return self._extract_response(response.json())
    except httpx.TimeoutException:
        raise TimeoutError(f"Request timed out after {self.timeout}s")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif e.response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        raise
    except Exception as e:
        raise TargetError(f"Request failed: {e}")
```

## Response Extraction

Extract text from various response formats:

```python
def _extract_response(self, data: dict) -> str:
    """Extract response text from API response."""
    # OpenAI-style
    if "choices" in data:
        return data["choices"][0]["message"]["content"]

    # Anthropic-style
    if "content" in data:
        return data["content"][0]["text"]

    # Simple format
    if "text" in data:
        return data["text"]

    if "output" in data:
        return data["output"]

    raise ValueError(f"Unknown response format: {list(data.keys())}")
```

## Testing

```python
# tests/test_my_target.py
import pytest
from akira.targets.my_target import MyTarget


@pytest.mark.asyncio
async def test_validate():
    target = MyTarget("https://api.example.com", "test-key")
    # Mock HTTP client
    assert await target.validate()


@pytest.mark.asyncio
async def test_send():
    target = MyTarget("https://api.example.com", "test-key")
    response = await target.send("Hello")
    assert isinstance(response, str)
```

## Best Practices

1. **Use async HTTP** - httpx or aiohttp for async requests
2. **Handle timeouts** - Make timeout configurable
3. **Validate early** - Check auth in `validate()`
4. **Extract cleanly** - Handle various response formats
5. **Informative repr** - Include endpoint in `__repr__`
6. **Close resources** - Implement cleanup if needed
