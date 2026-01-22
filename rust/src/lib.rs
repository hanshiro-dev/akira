//! Akira Core - High-performance Rust components for LLM security testing
//!
//! This module provides performance-critical operations:
//! - Payload mutation and fuzzing
//! - Parallel response analysis
//! - Fast pattern matching for vulnerability detection

use pyo3::prelude::*;
use rayon::prelude::*;
use std::collections::HashMap;

mod fuzzer;
mod matcher;
mod analyzer;

pub use fuzzer::PayloadFuzzer;
pub use matcher::PatternMatcher;
pub use analyzer::ResponseAnalyzer;

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

#[pymodule]
fn akira_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(mutate_payload, m)?)?;
    m.add_function(wrap_pyfunction!(analyze_responses_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(find_patterns, m)?)?;
    m.add_function(wrap_pyfunction!(check_attack_success, m)?)?;
    m.add_function(wrap_pyfunction!(generate_payload_variations, m)?)?;
    Ok(())
}
