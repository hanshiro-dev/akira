# Running Attacks

This guide covers executing attacks and interpreting results.

## Attack Workflow

1. Select a module
2. Configure options
3. Set target
4. (Optional) Run check
5. Run the attack
6. Analyze results

## Quick Check

Before running a full attack, use `check` for a quick vulnerability probe:

```
akira> check
[*] Quick check against target...
[!] Target appears potentially vulnerable
```

The check runs a lightweight test to determine if the target might be susceptible.

## Running Attacks

### Basic Run

```
akira> run
```

Or use the alias:

```
akira> exploit
```

### Verbose Output

Enable verbose mode for detailed output:

```
akira> setg verbose true
akira> run
```

## Understanding Results

### Result Fields

| Field | Description |
|-------|-------------|
| `Success` | Whether the attack achieved its goal |
| `Confidence` | How confident Akira is in the result (0.0-1.0) |
| `Payload` | The attack payload that was sent |
| `Response` | The LLM's response (truncated) |

### Success Indicators

```
[+] Attack completed
    Success:    True       # Attack worked
    Confidence: 0.95       # High confidence
```

```
[+] Attack completed
    Success:    False      # Attack blocked
    Confidence: 0.10       # Low confidence (might be false negative)
```

### Interpreting Confidence

| Confidence | Interpretation |
|------------|---------------|
| > 0.8 | High confidence in result |
| 0.5 - 0.8 | Moderate confidence, manual review recommended |
| < 0.5 | Low confidence, may need different approach |

## Attack Options

Most modules have configurable options:

```
akira> show options

Module Options:
┌─────────────┬────────────────────────────────────┬─────────────────────┐
│ Option      │ Description                        │ Current Value       │
├─────────────┼────────────────────────────────────┼─────────────────────┤
│ canary      │ Canary phrase to detect injection  │ AKIRA_INJECTION_... │
│ use_fuzzing │ Use Rust fuzzer for variations     │ False               │
│ fuzz_count  │ Number of fuzzing variations       │ 10                  │
└─────────────┴────────────────────────────────────┴─────────────────────┘
```

Set options before running:

```
akira> set canary MY_UNIQUE_STRING_12345
akira> set use_fuzzing true
akira> run
```

## Multiple Targets

To test the same attack against multiple targets:

```bash
# Save profiles for each target
akira> target openai ... -k $KEY1
akira> profile save openai-prod

akira> target anthropic ... -k $KEY2
akira> profile save anthropic-prod

# Test each
akira> profile load openai-prod
akira> run

akira> profile load anthropic-prod
akira> run

# Compare in history
akira> history
```

## Batch Testing

For non-interactive batch testing, use the CLI:

```bash
akira run injection/basic_injection \
    -t https://api.openai.com/v1/chat/completions \
    -T openai \
    -k $OPENAI_API_KEY \
    --set canary=BATCH_TEST_123
```

## Error Handling

### Timeout

```
[-] Request timed out after 30 seconds
```

Increase timeout:
```
akira> setg timeout 60
```

### Authentication Error

```
[-] Authentication failed (401)
```

Check your API key:
```
akira> target openai ... -k $CORRECT_KEY
```

### Rate Limiting

```
[-] Rate limited (429)
```

Reduce parallel requests:
```
akira> setg parallel_requests 1
```
