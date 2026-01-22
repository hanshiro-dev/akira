# Target Profiles

Save and reuse target configurations across sessions.

## Why Use Profiles?

- **Convenience** - Don't re-enter complex configurations
- **Consistency** - Same settings for repeated tests
- **Organization** - Name targets meaningfully
- **Security** - API keys stored locally (not in command history)

## Managing Profiles

### Save Current Target

```
akira> target openai https://api.openai.com/v1/chat/completions -k $KEY -m gpt-4
akira> profile save production-gpt4
[+] Saved profile: production-gpt4
```

### List Profiles

```
akira> profiles

                    Saved Target Profiles
┌─────────────────┬─────────┬──────────────────────────────┬────────────┐
│ Name            │ Type    │ URL                          │ Created    │
├─────────────────┼─────────┼──────────────────────────────┼────────────┤
│ production-gpt4 │ openai  │ https://api.openai.com/v1... │ 2024-01-15 │
│ staging-claude  │ anthropic│ https://api.anthropic.com... │ 2024-01-14 │
│ local-llama     │ api     │ http://localhost:8080/...    │ 2024-01-10 │
└─────────────────┴─────────┴──────────────────────────────┴────────────┘
```

### Load a Profile

```
akira> profile load production-gpt4
[+] Loaded profile: production-gpt4
    Type: openai | URL: https://api.openai.com/v1/chat/completions
```

### Delete a Profile

```
akira> profile delete old-test-target
[+] Deleted profile: old-test-target
```

## Profile Storage

Profiles are stored in the SQLite database at `~/.akira/akira.db`.

### What's Stored

- Profile name
- Target type
- Endpoint URL
- Configuration (model, auth settings, templates)
- Creation timestamp

### Security Note

API keys are stored in the database. Ensure appropriate file permissions:

```bash
chmod 600 ~/.akira/akira.db
```

## Naming Conventions

Recommended naming patterns:

```
<environment>-<provider>-<model>
```

Examples:
- `prod-openai-gpt4`
- `staging-claude-sonnet`
- `dev-local-llama`
- `test-custom-chatbot`

## Workflow Example

```bash
# Initial setup (once)
akira> target openai https://api.openai.com/v1/chat/completions -k $KEY -m gpt-4
akira> profile save prod-gpt4

akira> target anthropic https://api.anthropic.com/v1/messages -k $KEY -m claude-3-opus-20240229
akira> profile save prod-claude

# Daily testing
akira> profile load prod-gpt4
akira> use injection/basic_injection
akira> run

akira> profile load prod-claude
akira> run

# Compare results
akira> history
```

## Export/Import

Currently profiles are stored locally. To transfer between machines:

```bash
# Copy the database
scp ~/.akira/akira.db user@other-machine:~/.akira/
```
