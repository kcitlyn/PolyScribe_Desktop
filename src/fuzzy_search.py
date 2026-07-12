"""
Fuzzy search over model catalogs, powered by RapidFuzz (MIT license).

Tolerates typos and partial words: "japanse" matches Japanese,
"engl" matches English, "chinese big" matches the large Mandarin models.
"""

from rapidfuzz import fuzz

# Below this score a candidate is considered irrelevant (0-100 scale).
SCORE_CUTOFF = 60


def _best_score(query, haystack):
    """Score one query token against a text using the most forgiving metrics."""
    return max(
        fuzz.partial_ratio(query, haystack),      # substring-ish matches
        fuzz.token_set_ratio(query, haystack),    # word-order independent
    )


def search_models(query, models, keys=("lang", "name", "quality", "size")):
    """Filter+rank `models` (list of dicts) against a fuzzy `query`.

    Every whitespace-separated token in the query must match (AND semantics),
    so "german large" narrows to large German models. Returns matches sorted
    by relevance, best first. An empty query returns the list unchanged.
    """
    query = query.strip().lower()
    if not query:
        return list(models)

    tokens = query.split()
    scored = []
    for m in models:
        haystack = " ".join(str(m.get(k, "")) for k in keys).lower()
        token_scores = [_best_score(t, haystack) for t in tokens]
        if all(s >= SCORE_CUTOFF for s in token_scores):
            scored.append((sum(token_scores) / len(token_scores), m))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [m for _, m in scored]


def search_argos_packages(query, packages):
    """Fuzzy-filter Argos translation packages on their language names/codes."""
    query = query.strip().lower()
    if not query:
        return list(packages)

    tokens = query.split()
    scored = []
    for pkg in packages:
        haystack = " ".join(str(pkg.get(k, "")) for k in
                            ("from_name", "to_name", "from_code", "to_code")).lower()
        token_scores = [_best_score(t, haystack) for t in tokens]
        if all(s >= SCORE_CUTOFF for s in token_scores):
            scored.append((sum(token_scores) / len(token_scores), pkg))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [pkg for _, pkg in scored]
