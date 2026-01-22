# Rust Extensions

Akira includes optional Rust extensions for performance-critical operations.

## Overview

The Rust extension (`akira_core`) provides:

| Module | Purpose |
|--------|---------|
| `fuzzer.rs` | Payload mutation and fuzzing |
| `matcher.rs` | Fast multi-pattern matching |
| `analyzer.rs` | Parallel response analysis |
| `fuzzy.rs` | Fuzzy string matching |

## Building

### Prerequisites

- Rust toolchain (rustup)
- maturin (`pip install maturin`)

### Build Commands

```bash
cd rust

# Development build (debug)
maturin develop

# Release build (optimized)
maturin develop --release

# Build wheel for distribution
maturin build --release
```

## Using in Python

### Check Availability

```python
try:
    import akira_core
    HAS_RUST = True
except ImportError:
    HAS_RUST = False
```

### Available Functions

```python
import akira_core

# Payload fuzzing
variations = akira_core.generate_payload_variations(
    base_payload="Ignore instructions",
    technique="prompt_injection",
    count=20
)

# Pattern matching
matches = akira_core.find_patterns(
    text="response text here",
    patterns=["leaked", "secret", "password"]
)

# Response analysis
results = akira_core.analyze_responses_parallel(
    responses=["response1", "response2", ...],
    indicators=["success", "vulnerable"]
)

# Attack success check
success, confidence = akira_core.check_attack_success(
    response="model response",
    success_indicators=["CANARY_STRING"],
    failure_indicators=["I cannot", "I won't"]
)

# Fuzzy matching
score = akira_core.fuzzy_score("query", "target string")
ranked = akira_core.fuzzy_rank("query", [("name", "desc", ["tags"])])
```

## Adding New Rust Functions

### 1. Implement in Rust

```rust
// rust/src/my_module.rs
pub fn my_function(input: &str) -> String {
    // Implementation
    input.to_uppercase()
}
```

### 2. Expose to Python

```rust
// rust/src/lib.rs
mod my_module;

#[pyfunction]
fn my_function(input: &str) -> String {
    my_module::my_function(input)
}

#[pymodule]
fn akira_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // ... existing functions
    m.add_function(wrap_pyfunction!(my_function, m)?)?;
    Ok(())
}
```

### 3. Create Python Fallback

```python
# akira/core/my_module.py
try:
    import akira_core
    HAS_RUST = True
except ImportError:
    HAS_RUST = False


def my_function(input: str) -> str:
    if HAS_RUST:
        return akira_core.my_function(input)
    return input.upper()  # Python fallback
```

## Fuzzer Module

### Payload Mutation

```rust
// rust/src/fuzzer.rs
pub struct PayloadFuzzer;

impl PayloadFuzzer {
    pub fn mutate(&self, payload: &str, strategies: &[String], count: usize) -> Vec<String>;
    pub fn generate_variations(&self, base: &str, technique: &str, count: usize) -> Vec<String>;
}
```

Mutation strategies:
- Unicode homoglyphs
- Token splitting
- Case variations
- Whitespace manipulation
- Encoding tricks

## Matcher Module

### Pattern Matching

Uses Aho-Corasick algorithm for efficient multi-pattern matching:

```rust
// rust/src/matcher.rs
pub struct PatternMatcher {
    patterns: Vec<String>,
}

impl PatternMatcher {
    pub fn find_all(&self, text: &str) -> Vec<(String, Vec<usize>)>;
}
```

## Analyzer Module

### Parallel Response Analysis

```rust
// rust/src/analyzer.rs
pub struct ResponseAnalyzer {
    indicators: Vec<String>,
}

impl ResponseAnalyzer {
    pub fn analyze(&self, response: &str) -> HashMap<String, bool>;
    pub fn check_success(&self, response: &str, success: &[String], failure: &[String]) -> (bool, f64);
}
```

Uses Rayon for parallel processing of multiple responses.

## Testing Rust Code

```bash
cd rust
cargo test
```

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_my_function() {
        assert_eq!(my_function("hello"), "HELLO");
    }
}
```

## Performance Notes

- Rust extensions provide 10-100x speedup for fuzzing
- Pattern matching is significantly faster with Aho-Corasick
- Parallel analysis scales with CPU cores
- Always provide Python fallback for compatibility
