# Configuration

Akira configuration options and files.

## Data Directory

Akira stores data in `~/.akira/`:

```
~/.akira/
├── akira.db          # SQLite database
└── history           # Command history
```

### Custom Location

Set `AKIRA_DATA_DIR` environment variable:

```bash
export AKIRA_DATA_DIR=/custom/path
```

## Global Options

Set with `setg` command in console:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `verbose` | bool | `false` | Enable verbose output |
| `timeout` | int | `30` | Request timeout (seconds) |
| `max_retries` | int | `3` | Maximum retry attempts |
| `parallel_requests` | int | `5` | Concurrent request limit |

Example:
```
akira> setg verbose true
akira> setg timeout 60
```

## Environment Variables

### API Keys

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export HF_TOKEN="hf_..."
```

### AWS Credentials

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"
```

Or use `~/.aws/credentials`.

### Akira Settings

```bash
export AKIRA_DATA_DIR="/custom/data/path"
```

## Module Options

Each module has its own options. View with:

```
akira> show options
```

Common options across modules:

| Option | Description |
|--------|-------------|
| `canary` | Marker string for detection |
| `timeout` | Module-specific timeout |
| `use_fuzzing` | Enable payload fuzzing |
| `fuzz_count` | Number of fuzz variations |
| `variant` | Attack variant to use |

## Target Configuration

### Request Templates

JSON template with `$payload` placeholder:

```json
{
  "messages": [
    {"role": "user", "content": "$payload"}
  ],
  "model": "gpt-4",
  "max_tokens": 500
}
```

### Response Paths

Dot-notation path to extract response:

```
choices.0.message.content
data.response.text
output
```

### Authentication Types

| Type | Header Sent |
|------|------------|
| `bearer` | `Authorization: Bearer <key>` |
| `api-key` | `X-API-Key: <key>` |
| `basic` | `Authorization: Basic <base64>` |
| `none` | No auth header |

Custom header:
```
--auth-type api-key --auth-header X-Custom-Auth
```

## Database Schema

SQLite database at `~/.akira/akira.db`:

### attack_history

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | REAL | Unix timestamp |
| module | TEXT | Module name |
| target_type | TEXT | Target type |
| target_url | TEXT | Target URL |
| success | INTEGER | 0 or 1 |
| confidence | REAL | 0.0 to 1.0 |
| payload | TEXT | Payload used |
| response | TEXT | LLM response |
| details_json | TEXT | JSON metadata |

### target_profiles

| Column | Type | Description |
|--------|------|-------------|
| name | TEXT | Profile name (PK) |
| target_type | TEXT | Target type |
| url | TEXT | Endpoint URL |
| config_json | TEXT | JSON config |
| created_at | REAL | Unix timestamp |

### prompt_cache

| Column | Type | Description |
|--------|------|-------------|
| key | TEXT | Cache key (PK) |
| prompt_text | TEXT | Cached prompt |
| source | TEXT | Source identifier |
| updated_at | REAL | Unix timestamp |

### response_cache

| Column | Type | Description |
|--------|------|-------------|
| request_hash | TEXT | SHA256 hash (PK) |
| response | TEXT | Cached response |
| created_at | REAL | Unix timestamp |
| expires_at | REAL | Expiration time |
