# Interactive Console

Akira's interactive console provides a Metasploit-style interface for security testing.

## Starting the Console

```bash
akira
```

## Command Overview

| Command | Description |
|---------|-------------|
| `help` | Show all commands |
| `use <module>` | Select an attack module |
| `info` | Show current module details |
| `show modules` | List all attack modules |
| `show options` | Show module options |
| `search [term]` | Fuzzy search modules |
| `set <opt> <val>` | Set module option |
| `setg <opt> <val>` | Set global option |
| `target <type> <url>` | Set target endpoint |
| `targets` | List target types |
| `profile <action> <name>` | Manage target profiles |
| `profiles` | List saved profiles |
| `check` | Quick vulnerability probe |
| `run` / `exploit` | Execute attack |
| `back` | Deselect module |
| `history` | Show attack history |
| `stats` | Show statistics |
| `exit` / `quit` | Exit console |

## Module Selection

### Listing Modules

```
akira> show modules
```

Shows all available attack modules with category, severity, and description.

### Searching Modules

Interactive fuzzy search:

```
akira> search
```

This opens a real-time search interface. Type to filter, use arrow keys to navigate, Enter to select.

Static search with term:

```
akira> search injection
```

### Using a Module

```
akira> use injection/basic_injection
[+] Using injection/basic_injection
    Severity: HIGH
```

### Module Information

```
akira> info
```

Shows detailed information about the selected module including description, references, and tags.

## Configuration

### Module Options

View options:

```
akira> show options
```

Set an option:

```
akira> set canary MY_CANARY_STRING
```

### Global Options

Global options apply to all modules:

```
akira> setg timeout 60
akira> setg verbose true
```

Available global options:
- `verbose` - Enable verbose output
- `timeout` - Request timeout in seconds
- `max_retries` - Maximum retry attempts
- `parallel_requests` - Concurrent request limit

## Prompt Customization

The prompt shows your current context:

```
akira>                           # No module selected
akira (basic_injection)>         # Module selected
```

## Tab Completion

The console supports tab completion for:
- Commands
- Module names
- Target types
- Options

## History

Command history is preserved across sessions. Use up/down arrows to navigate.

## Color Coding

Output uses consistent color coding:

- `[+]` Green - Success/positive result
- `[-]` Red - Error/failure
- `[*]` Blue/Yellow - Information
- `[!]` Yellow - Warning
