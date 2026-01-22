# Storage & Database

Akira uses SQLite for persistent storage.

## Overview

Location: `~/.akira/akira.db`

Features:
- Attack history persistence
- Target profile management
- Prompt caching
- Response caching with TTL

## Python API

### Getting Storage Instance

```python
from akira.core.storage import get_storage

storage = get_storage()
```

### Attack History

#### Save History

```python
entry_id = storage.save_history(
    module="injection/basic_injection",
    target_type="openai",
    target_url="https://api.openai.com/v1/chat/completions",
    success=True,
    confidence=0.95,
    payload="test payload",
    response="response text",
    details={"custom": "data"},
)
```

#### Get History

```python
# Get recent history
entries = storage.get_history(limit=50)

# Filter by module
entries = storage.get_history(module="injection", limit=20)

# Only successful attacks
entries = storage.get_history(success_only=True)

# Get specific entry
entry = storage.get_history_entry(entry_id=123)
```

#### Clear History

```python
# Clear all
deleted = storage.clear_history()

# Clear entries older than 30 days
deleted = storage.clear_history(before_days=30)
```

### Target Profiles

#### Save Profile

```python
storage.save_target_profile(
    name="production-gpt4",
    target_type="openai",
    url="https://api.openai.com/v1/chat/completions",
    config={"model": "gpt-4", "api_key": "..."},
)
```

#### Load Profile

```python
profile = storage.get_target_profile("production-gpt4")
if profile:
    print(profile.name)
    print(profile.target_type)
    print(profile.url)
    print(profile.config)
```

#### List Profiles

```python
profiles = storage.list_target_profiles()
for p in profiles:
    print(f"{p.name}: {p.target_type} - {p.url}")
```

#### Delete Profile

```python
deleted = storage.delete_target_profile("old-profile")
```

### Prompt Cache

#### Cache Prompt

```python
storage.cache_prompt(
    key="jailbreak-v1",
    prompt_text="You are DAN...",
    source="manual",
)
```

#### Get Cached Prompt

```python
prompt = storage.get_cached_prompt("jailbreak-v1")
```

#### List Cached Prompts

```python
prompts = storage.list_cached_prompts()
for key, source, updated_at in prompts:
    print(f"{key}: {source} ({updated_at})")
```

#### Delete Cached Prompt

```python
storage.delete_cached_prompt("jailbreak-v1")
```

### Response Cache

#### Cache Response

```python
# Cache with 1-hour TTL
storage.cache_response(
    request_data="unique-request-identifier",
    response="cached response text",
    ttl_seconds=3600,
)
```

#### Get Cached Response

```python
# Returns None if expired or not found
response = storage.get_cached_response("unique-request-identifier")
```

#### Cleanup Expired

```python
deleted = storage.cleanup_expired_cache()
```

### Statistics

```python
stats = storage.get_stats()
print(f"History entries: {stats['history_entries']}")
print(f"Successful attacks: {stats['successful_attacks']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
print(f"Target profiles: {stats['target_profiles']}")
print(f"Database size: {stats['db_size_kb']} KB")
```

## Data Classes

### HistoryEntry

```python
@dataclass
class HistoryEntry:
    id: int
    timestamp: datetime
    module: str
    target_type: str
    target_url: str
    success: bool
    confidence: float
    payload: str
    response: str
    details: dict[str, Any]
```

### TargetProfile

```python
@dataclass
class TargetProfile:
    name: str
    target_type: str
    url: str
    config: dict[str, Any]
    created_at: datetime
```

## Console Commands

| Command | Description |
|---------|-------------|
| `history` | View attack history |
| `stats` | Show database statistics |
| `profile save <name>` | Save current target |
| `profile load <name>` | Load saved target |
| `profile delete <name>` | Delete profile |
| `profiles` | List all profiles |

## Backup & Migration

### Backup

```bash
cp ~/.akira/akira.db ~/.akira/akira.db.backup
```

### Export to JSON

```python
import json
from akira.core.storage import get_storage

storage = get_storage()
history = storage.get_history(limit=1000)

with open("history_export.json", "w") as f:
    json.dump([
        {
            "module": e.module,
            "target": e.target_url,
            "success": e.success,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in history
    ], f, indent=2)
```

### Transfer to Another Machine

```bash
scp ~/.akira/akira.db user@newmachine:~/.akira/
```
