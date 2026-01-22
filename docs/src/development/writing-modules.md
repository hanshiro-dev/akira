# Writing Modules

Create custom attack modules for Akira.

## Quick Start

Create a new module in `akira/modules/<category>/<name>.py`:

```python
from akira.core.module import AttackCategory, AttackResult, Module, ModuleInfo, Severity
from akira.core.target import Target


class MyAttack(Module):
    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            name="my_attack",
            description="Description of what this attack tests",
            author="Your Name",
            category=AttackCategory.INJECTION,
            severity=Severity.HIGH,
            references=["https://example.com/reference"],
            tags=["injection", "custom"],
        )

    def _setup_options(self) -> None:
        self.add_option("my_option", "Description of option", default="value")

    async def check(self, target: Target) -> bool:
        # Quick probe - return True if target might be vulnerable
        response = await target.send("Test query")
        return "vulnerable" in response.lower()

    async def run(self, target: Target) -> AttackResult:
        payload = self.get_option("my_option")

        response = await target.send(str(payload))

        success = "expected_string" in response

        return AttackResult(
            success=success,
            confidence=0.9 if success else 0.1,
            payload_used=str(payload),
            response=response[:500],
            details={"custom_field": "value"},
        )
```

## Module Structure

### ModuleInfo

Required metadata about your module:

```python
ModuleInfo(
    name="unique_name",           # Unique identifier
    description="...",            # What this attack tests
    author="Your Name",           # Author attribution
    category=AttackCategory.XXX,  # Attack category
    severity=Severity.XXX,        # Risk level
    references=["url1", "url2"],  # Reference links
    tags=["tag1", "tag2"],        # Searchable tags
)
```

### Categories

```python
class AttackCategory(Enum):
    INJECTION = "injection"
    JAILBREAK = "jailbreak"
    EXTRACTION = "extraction"
    DOS = "dos"
```

### Severity Levels

```python
class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
```

## Options

### Adding Options

```python
def _setup_options(self) -> None:
    self.add_option("name", "description", default="value")
    self.add_option("count", "Number of attempts", default=10)
    self.add_option("enable_feature", "Enable X", default=False)
```

### Using Options

```python
async def run(self, target: Target) -> AttackResult:
    name = str(self.get_option("name"))
    count = int(self.get_option("count") or 10)
    enabled = bool(self.get_option("enable_feature"))
```

## Check Method

Quick vulnerability probe:

```python
async def check(self, target: Target) -> bool:
    """Return True if target might be vulnerable."""
    try:
        response = await target.send("Probe query")
        indicators = ["leaked", "revealed", "here is"]
        return any(ind in response.lower() for ind in indicators)
    except Exception:
        return False
```

Guidelines:
- Should be fast (single request if possible)
- Return `True` if *might* be vulnerable
- Return `False` if definitely not vulnerable
- Handle exceptions gracefully

## Run Method

Full attack execution:

```python
async def run(self, target: Target) -> AttackResult:
    payloads = self._generate_payloads()

    for payload in payloads:
        try:
            response = await target.send(payload)

            if self._is_successful(response):
                return AttackResult(
                    success=True,
                    confidence=0.9,
                    payload_used=payload,
                    response=response[:500],
                    details={"successful_payload_index": payloads.index(payload)},
                )
        except Exception as e:
            continue  # Or handle error

    return AttackResult(
        success=False,
        confidence=0.1,
        payload_used=payloads[0],
        response="",
        details={"payloads_tested": len(payloads)},
    )
```

## Using Rust Extensions

Check for Rust availability:

```python
try:
    import akira_core
    HAS_RUST = True
except ImportError:
    HAS_RUST = False


async def run(self, target: Target) -> AttackResult:
    if HAS_RUST:
        # Use fast Rust implementation
        variations = akira_core.generate_payload_variations(
            base_payload, "technique", count=20
        )
    else:
        # Fallback to Python
        variations = self._generate_variations_python(base_payload)
```

## Testing Your Module

```python
# tests/test_my_module.py
import pytest
from akira.modules.injection.my_attack import MyAttack


def test_module_info():
    module = MyAttack()
    assert module.info.name == "my_attack"
    assert module.info.category.value == "injection"


@pytest.mark.asyncio
async def test_check():
    module = MyAttack()
    # Mock target and test check logic
```

## Best Practices

1. **Truncate responses** - Store only first 500-1000 chars
2. **Handle errors** - Catch exceptions, return meaningful results
3. **Validate options** - Check types and ranges
4. **Document payloads** - Comment why each payload exists
5. **Add references** - Link to research/CVEs
6. **Use meaningful tags** - Help users find your module
7. **Test thoroughly** - Write unit tests
