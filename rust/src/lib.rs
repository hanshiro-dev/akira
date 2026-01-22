//! Akira Core - High-performance Rust components for LLM security testing
//!
//! This module provides performance-critical operations:
//! - Payload mutation and fuzzing
//! - Parallel response analysis
//! - Fast pattern matching for vulnerability detection
//! - Fuzzy string matching for module search

use pyo3::prelude::*;
use rayon::prelude::*;
use std::collections::HashMap;

mod fuzzer;
mod matcher;
mod analyzer;
mod fuzzy;

pub use fuzzer::PayloadFuzzer;
pub use matcher::PatternMatcher;
pub use analyzer::ResponseAnalyzer;
pub use fuzzy::FuzzyMatcher;

/// Mutate a payload with various fuzzing strategies
#[pyfunction]
fn mutate_payload(payload: &str, strategies: Vec<String>, count: usize) -> Vec<String> {
    let fuzzer = fuzzer::PayloadFuzzer::new();
    fuzzer.mutate(payload, &strategies, count)
}

/// Analyze multiple responses in parallel for vulnerability indicators
#[pyfunction]
fn analyze_responses_parallel(
    responses: Vec<String>,
    indicators: Vec<String>,
) -> Vec<HashMap<String, bool>> {
    let analyzer = analyzer::ResponseAnalyzer::new(indicators);
    responses
        .par_iter()
        .map(|r| analyzer.analyze(r))
        .collect()
}

/// Fast multi-pattern matching across text
#[pyfunction]
fn find_patterns(text: &str, patterns: Vec<String>) -> Vec<(String, Vec<usize>)> {
    let matcher = matcher::PatternMatcher::new(patterns);
    matcher.find_all(text)
}

/// Check if a response indicates a successful attack
#[pyfunction]
fn check_attack_success(
    response: &str,
    success_indicators: Vec<String>,
    failure_indicators: Vec<String>,
) -> (bool, f64) {
    let analyzer = analyzer::ResponseAnalyzer::new(success_indicators.clone());
    analyzer.check_success(response, &success_indicators, &failure_indicators)
}

/// Generate payload variations for testing
#[pyfunction]
fn generate_payload_variations(
    base_payload: &str,
    technique: &str,
    count: usize,
) -> Vec<String> {
    let fuzzer = fuzzer::PayloadFuzzer::new();
    fuzzer.generate_variations(base_payload, technique, count)
}

/// Calculate fuzzy match score between query and target
#[pyfunction]
fn fuzzy_score(query: &str, target: &str) -> f64 {
    let matcher = fuzzy::FuzzyMatcher::new();
    matcher.score(query, target)
}

/// Rank multiple targets by fuzzy match score
/// targets: list of (name, description, tags) tuples
/// Returns: list of (index, score) tuples sorted by score descending
#[pyfunction]
fn fuzzy_rank(query: &str, targets: Vec<(String, String, Vec<String>)>) -> Vec<(usize, f64)> {
    let matcher = fuzzy::FuzzyMatcher::new();
    matcher.rank(query, &targets)
}

#[pymodule]
fn akira_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(mutate_payload, m)?)?;
    m.add_function(wrap_pyfunction!(analyze_responses_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(find_patterns, m)?)?;
    m.add_function(wrap_pyfunction!(check_attack_success, m)?)?;
    m.add_function(wrap_pyfunction!(generate_payload_variations, m)?)?;
    m.add_function(wrap_pyfunction!(fuzzy_score, m)?)?;
    m.add_function(wrap_pyfunction!(fuzzy_rank, m)?)?;
    Ok(())
}
