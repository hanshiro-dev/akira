# Search & Discovery

Find modules quickly with fuzzy search.

## Interactive Search

Launch the interactive fuzzy finder:

```
akira> search
```

This opens a real-time search interface:

```
 Fuzzy Search (ESC to cancel, Enter to select)
 ────────────────────────────────────────────────────────────
 ▶ injection/basic_injection         100%  Tests for basic prompt injection
   jailbreak/dan_jailbreak            47%  Tests resistance to DAN-style jailbreak
   extraction/system_prompt_leak      32%  Attempts to extract system prompt
   dos/magic_string                   21%  Tests for Claude magic string DoS

 Search: inj
```

### Controls

| Key | Action |
|-----|--------|
| Type | Filter results |
| ↑/↓ | Navigate results |
| Tab | Cycle through results |
| Enter | Select and load module |
| ESC | Cancel |

## Static Search

Search with a specific term:

```
akira> search injection

                         Search: injection
┌───────────────────────────┬───────┬────────────────────────────────────┐
│ Module                    │ Score │ Description                        │
├───────────────────────────┼───────┼────────────────────────────────────┤
│ injection/basic_injection │  100% │ Tests for basic prompt injection   │
└───────────────────────────┴───────┴────────────────────────────────────┘
```

## Search Targets

The fuzzy search matches against:

1. **Module name** (highest weight)
2. **Tags** (high weight)
3. **Description** (moderate weight)

## Search Examples

```bash
# Find injection-related modules
akira> search injection

# Find Claude-specific attacks
akira> search claude

# Find by tag
akira> search owasp

# Find by severity (in description)
akira> search dos

# Fuzzy matching works
akira> search jlbrk    # matches "jailbreak"
```

## Listing Modules

To see all modules without searching:

```
akira> show modules
```

Filter by category:

```
# Not yet implemented - use search instead
akira> search injection/
akira> search dos/
```

## Tips

1. **Start broad** - Use short queries to see more matches
2. **Use tags** - Modules are tagged (e.g., `owasp`, `claude`, `safety-bypass`)
3. **Interactive for exploration** - Use `search` without args to browse
4. **Static for scripts** - Use `search <term>` for known modules
