# Console Commands

Complete reference for interactive console commands.

## Module Commands

### use

Select an attack module:

```
akira> use <module_name>
```

Examples:
```
akira> use injection/basic_injection
akira> use dos/magic_string
```

### info

Show detailed information about the current module:

```
akira> info
```

Displays: name, category, severity, author, description, references, tags.

### back

Deselect the current module:

```
akira> back
```

## Display Commands

### show modules

List all available attack modules:

```
akira> show modules
```

### show options

Show current module's configurable options:

```
akira> show options
```

### show targets

List available target types:

```
akira> targets
```

### help

Display command help:

```
akira> help
```

## Configuration Commands

### set

Set a module option:

```
akira> set <option> <value>
```

Examples:
```
akira> set canary MY_CANARY_STRING
akira> set timeout 60
akira> set use_fuzzing true
```

### setg

Set a global option (applies to all modules):

```
akira> setg <option> <value>
```

Examples:
```
akira> setg verbose true
akira> setg timeout 45
akira> setg parallel_requests 3
```

Global options:
- `verbose` - Enable verbose output
- `timeout` - Request timeout (seconds)
- `max_retries` - Maximum retry attempts
- `parallel_requests` - Concurrent requests

### options

Alias for `show options`:

```
akira> options
```

## Target Commands

### target

Configure the target endpoint:

```
akira> target <type> <url> [options]
```

Options:
- `-k, --key` - API key
- `-m, --model` - Model identifier
- `--request-template` - Custom request JSON
- `--response-path` - Response extraction path
- `--auth-type` - Authentication type
- `--auth-header` - Custom auth header

Examples:
```
akira> target openai https://api.openai.com/v1/chat/completions -k $KEY
akira> target api https://myapi.com/chat --request-template '{"q": "$payload"}'
```

### targets

List available target types:

```
akira> targets
```

## Profile Commands

### profile

Manage target profiles:

```
akira> profile <action> <name>
```

Actions:
- `save` - Save current target as profile
- `load` - Load a saved profile
- `delete` - Delete a profile

Examples:
```
akira> profile save my-openai
akira> profile load my-openai
akira> profile delete old-profile
```

### profiles

List all saved profiles:

```
akira> profiles
```

## Execution Commands

### check

Run quick vulnerability probe:

```
akira> check
```

Fast check to determine if target might be vulnerable.

### run

Execute the attack:

```
akira> run
```

### exploit

Alias for `run`:

```
akira> exploit
```

## Search Commands

### search

Fuzzy search for modules:

```
akira> search [term]
```

Without term: Opens interactive fuzzy finder
With term: Shows matching modules

Examples:
```
akira> search              # Interactive mode
akira> search injection    # Static search
akira> search claude       # Find Claude-specific modules
```

## History & Stats

### history

Show attack history for current session:

```
akira> history
```

### stats

Show session and database statistics:

```
akira> stats
```

## Session Commands

### exit / quit

Exit the console:

```
akira> exit
akira> quit
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Tab | Auto-complete |
| Up/Down | Command history |
| Ctrl+C | Cancel current input |
| Ctrl+D | Exit console |
