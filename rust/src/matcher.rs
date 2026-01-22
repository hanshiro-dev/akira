//! Fast multi-pattern matching using Aho-Corasick algorithm

use aho_corasick::AhoCorasick;

pub struct PatternMatcher {
    patterns: Vec<String>,
    automaton: AhoCorasick,
}

impl PatternMatcher {
    pub fn new(patterns: Vec<String>) -> Self {
        let automaton = AhoCorasick::new(&patterns).expect("Failed to build pattern matcher");
        Self { patterns, automaton }
    }

    /// Find all pattern matches and their positions
    pub fn find_all(&self, text: &str) -> Vec<(String, Vec<usize>)> {
        let mut results: Vec<(String, Vec<usize>)> = self
            .patterns
            .iter()
            .map(|p| (p.clone(), Vec::new()))
            .collect();

        for mat in self.automaton.find_iter(text) {
            let pattern_idx = mat.pattern().as_usize();
            results[pattern_idx].1.push(mat.start());
        }

        // Only return patterns that had matches
        results.into_iter().filter(|(_, pos)| !pos.is_empty()).collect()
    }

    /// Check if any pattern matches
    pub fn has_match(&self, text: &str) -> bool {
        self.automaton.is_match(text)
    }

    /// Count total matches across all patterns
    pub fn count_matches(&self, text: &str) -> usize {
        self.automaton.find_iter(text).count()
    }
}
