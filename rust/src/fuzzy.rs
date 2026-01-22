//! Fuzzy string matching for module search

use std::cmp::max;

pub struct FuzzyMatcher;

impl FuzzyMatcher {
    pub fn new() -> Self {
        Self
    }

    /// Calculate fuzzy match score between query and target (0.0 to 1.0)
    pub fn score(&self, query: &str, target: &str) -> f64 {
        if query.is_empty() {
            return 1.0;
        }
        if target.is_empty() {
            return 0.0;
        }

        let query_lower = query.to_lowercase();
        let target_lower = target.to_lowercase();

        // Exact substring match gets high score
        if target_lower.contains(&query_lower) {
            let length_ratio = query.len() as f64 / target.len() as f64;
            return 0.8 + (0.2 * length_ratio);
        }

        // Fuzzy character matching
        let mut score = 0.0;
        let mut query_idx = 0;
        let mut consecutive_bonus = 0.0;
        let mut last_match_idx: Option<usize> = None;

        let query_chars: Vec<char> = query_lower.chars().collect();
        let target_chars: Vec<char> = target_lower.chars().collect();

        for (target_idx, &target_char) in target_chars.iter().enumerate() {
            if query_idx < query_chars.len() && target_char == query_chars[query_idx] {
                // Base score for match
                let mut match_score = 1.0;

                // Bonus for consecutive matches
                if let Some(last_idx) = last_match_idx {
                    if target_idx == last_idx + 1 {
                        consecutive_bonus += 0.5;
                        match_score += consecutive_bonus;
                    } else {
                        consecutive_bonus = 0.0;
                    }
                }

                // Bonus for matching at word boundaries
                if target_idx == 0 || !target_chars[target_idx - 1].is_alphanumeric() {
                    match_score += 0.5;
                }

                // Bonus for matching uppercase in camelCase
                if target.chars().nth(target_idx).map_or(false, |c| c.is_uppercase()) {
                    match_score += 0.3;
                }

                score += match_score;
                last_match_idx = Some(target_idx);
                query_idx += 1;
            }
        }

        // All query chars must match
        if query_idx < query_chars.len() {
            return 0.0;
        }

        // Normalize score
        let max_possible = query_chars.len() as f64 * 3.0;
        (score / max_possible).min(1.0)
    }

    /// Score multiple targets and return sorted results
    pub fn rank(&self, query: &str, targets: &[(String, String, Vec<String>)]) -> Vec<(usize, f64)> {
        let mut results: Vec<(usize, f64)> = targets
            .iter()
            .enumerate()
            .filter_map(|(idx, (name, description, tags))| {
                // Score against name, description, and tags
                let name_score = self.score(query, name) * 1.5; // Name matches weighted higher
                let desc_score = self.score(query, description) * 0.8;
                let tag_score = tags
                    .iter()
                    .map(|t| self.score(query, t))
                    .max_by(|a, b| a.partial_cmp(b).unwrap())
                    .unwrap_or(0.0)
                    * 1.2;

                let best_score = name_score.max(desc_score).max(tag_score);
                if best_score > 0.1 {
                    Some((idx, best_score))
                } else {
                    None
                }
            })
            .collect();

        results.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        results
    }
}

impl Default for FuzzyMatcher {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_exact_match() {
        let matcher = FuzzyMatcher::new();
        assert!(matcher.score("injection", "injection") > 0.9);
    }

    #[test]
    fn test_substring_match() {
        let matcher = FuzzyMatcher::new();
        assert!(matcher.score("inj", "basic_injection") > 0.5);
    }

    #[test]
    fn test_fuzzy_match() {
        let matcher = FuzzyMatcher::new();
        assert!(matcher.score("bscnj", "basic_injection") > 0.2);
    }

    #[test]
    fn test_no_match() {
        let matcher = FuzzyMatcher::new();
        assert!(matcher.score("xyz", "basic_injection") < 0.1);
    }
}
