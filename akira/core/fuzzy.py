"""Fuzzy string matching for module search"""

from dataclasses import dataclass

try:
    import akira_core
    HAS_RUST = True
except ImportError:
    HAS_RUST = False


@dataclass
class SearchResult:
    name: str
    description: str
    tags: list[str]
    score: float


def fuzzy_score(query: str, target: str) -> float:
    """Calculate fuzzy match score between query and target (0.0 to 1.0)"""
    if HAS_RUST:
        return akira_core.fuzzy_score(query, target)
    return _py_fuzzy_score(query, target)


def fuzzy_rank(
    query: str, targets: list[tuple[str, str, list[str]]]
) -> list[tuple[int, float]]:
    """Rank targets by fuzzy match score. Returns (index, score) tuples."""
    if HAS_RUST:
        return akira_core.fuzzy_rank(query, targets)
    return _py_fuzzy_rank(query, targets)


def _py_fuzzy_score(query: str, target: str) -> float:
    """Pure Python fuzzy matching fallback"""
    if not query:
        return 1.0
    if not target:
        return 0.0

    query_lower = query.lower()
    target_lower = target.lower()

    # Exact substring match
    if query_lower in target_lower:
        length_ratio = len(query) / len(target)
        return 0.8 + (0.2 * length_ratio)

    # Fuzzy character matching
    score = 0.0
    query_idx = 0
    consecutive_bonus = 0.0
    last_match_idx = None
    query_chars = list(query_lower)
    target_chars = list(target_lower)

    for target_idx, target_char in enumerate(target_chars):
        if query_idx < len(query_chars) and target_char == query_chars[query_idx]:
            match_score = 1.0

            if last_match_idx is not None and target_idx == last_match_idx + 1:
                consecutive_bonus += 0.5
                match_score += consecutive_bonus
            else:
                consecutive_bonus = 0.0

            # Word boundary bonus
            if target_idx == 0 or not target_chars[target_idx - 1].isalnum():
                match_score += 0.5

            # Uppercase bonus
            if target_idx < len(target) and target[target_idx].isupper():
                match_score += 0.3

            score += match_score
            last_match_idx = target_idx
            query_idx += 1

    if query_idx < len(query_chars):
        return 0.0

    max_possible = len(query_chars) * 3.0
    return min(score / max_possible, 1.0)


def _py_fuzzy_rank(
    query: str, targets: list[tuple[str, str, list[str]]]
) -> list[tuple[int, float]]:
    """Pure Python ranking fallback"""
    results = []

    for idx, (name, description, tags) in enumerate(targets):
        name_score = _py_fuzzy_score(query, name) * 1.5
        desc_score = _py_fuzzy_score(query, description) * 0.8
        tag_scores = [_py_fuzzy_score(query, t) for t in tags] if tags else [0.0]
        tag_score = max(tag_scores) * 1.2

        best_score = max(name_score, desc_score, tag_score)
        if best_score > 0.1:
            results.append((idx, best_score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
