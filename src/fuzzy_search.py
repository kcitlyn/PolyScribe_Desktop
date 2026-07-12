"""
Fuzzy search over model catalogs, powered by RapidFuzz (MIT license).

Tolerates typos and partial words: "japanse" matches Japanese,
"engl" matches English, "chinese big" matches the large Mandarin models.
"""

from rapidfuzz import fuzz, process

# Vosk models: bigger haystack, more room for partial matches
VOSK_CUTOFF = 60

# Argos packages: short names, need tighter matching to avoid noise.
# 80 eliminates false positives (spanish/danish=77) while keeping all
# reasonable single-char typos (germin/german=83 is the tightest passing).
ARGOS_CUTOFF = 80


def _best_score(query, haystack):
    """Score one query token against a text using the most forgiving metrics."""
    return max(
        fuzz.partial_ratio(query, haystack),
        fuzz.token_set_ratio(query, haystack),
    )


def _field_score(query, fields):
    """Score a query token against individual fields (from_name, to_name, etc).

    Scoring strategy:
    - Short tokens (<=3 chars, like language codes): exact substring or bust
    - Prefix match: strongly preferred (100 points)
    - Full-string ratio: penalizes char-overlap coincidences (like spanish/danish)
    """
    if len(query) <= 3:
        for f in fields:
            if query in f:
                return 100
        return 0
    best = 0
    for f in fields:
        if f.startswith(query) or query.startswith(f):
            best = max(best, 100)
        else:
            best = max(best, fuzz.ratio(query, f))
    return best


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
        if all(s >= VOSK_CUTOFF for s in token_scores):
            scored.append((sum(token_scores) / len(token_scores), m))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [m for _, m in scored]


def search_argos_packages(query, packages):
    """Fuzzy-filter Argos translation packages on their language names/codes.

    Uses per-field matching with a tighter cutoff to avoid noise — "spanish"
    won't accidentally match "Danish" via substring overlap.
    """
    query = query.strip().lower()
    if not query:
        return list(packages)

    tokens = query.split()
    scored = []
    for pkg in packages:
        fields = [
            str(pkg.get("from_name", "")).lower(),
            str(pkg.get("to_name", "")).lower(),
            str(pkg.get("from_code", "")).lower(),
            str(pkg.get("to_code", "")).lower(),
        ]
        token_scores = [_field_score(t, fields) for t in tokens]
        if all(s >= ARGOS_CUTOFF for s in token_scores):
            scored.append((sum(token_scores) / len(token_scores), pkg))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [pkg for _, pkg in scored]
