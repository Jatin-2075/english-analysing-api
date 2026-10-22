import re

SOUND_FILLER = re.compile(r"^(?:u+m+|u+h+|e+r+m*|h+m+|m{2,})$")

PUNCT = set(",.!?;:")

CONTEXT_FILLERS = {
    ("you", "know"): "comma",
    ("i", "mean"): "comma",
    ("basically",): "any",
    ("actually",): "any",
    ("literally",): "any",
    ("like",): "both",
    ("well",): "well",
}
MAX_PHRASE_LEN = max(len(k) for k in CONTEXT_FILLERS)


def _is_filler(rule: str, prev: str | None, nxt: str | None) -> bool:
    clause_start = prev is None or prev in PUNCT
    after_comma = nxt == ","
    after_comma_prev = prev == ","

    if rule == "any":
        return clause_start or after_comma
    if rule == "comma":
        return after_comma_prev or after_comma
    if rule == "both":
        return clause_start and after_comma
    if rule == "well":
        return (prev is None or prev in ".!?") and after_comma
    return False


def analyze_fillers(transcript: str) -> dict:
    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty")

    tokens = re.findall(r"[\w']+|[.,!?;:]", transcript.lower())
    filler_counts: dict[str, int] = {}
    word_count = 0
    i = 0

    while i < len(tokens):
        token = tokens[i]

        if token in PUNCT:
            i += 1
            continue

        if SOUND_FILLER.match(token):
            filler_counts[token] = filler_counts.get(token, 0) + 1
            word_count += 1
            i += 1
            continue

        matched = False
        for size in range(MAX_PHRASE_LEN, 0, -1):
            phrase = tuple(tokens[i : i + size])
            rule = CONTEXT_FILLERS.get(phrase)
            if rule is None or len(phrase) != size:
                continue
            prev = tokens[i - 1] if i > 0 else None
            nxt = tokens[i + size] if i + size < len(tokens) else None
            word_count += size
            if _is_filler(rule, prev, nxt):
                key = " ".join(phrase)
                filler_counts[key] = filler_counts.get(key, 0) + 1
            i += size
            matched = True
            break

        if not matched:
            word_count += 1
            i += 1

    total_fillers = sum(filler_counts.values())

    return {
        "filler_count": total_fillers,
        "filler_words": filler_counts,
        "filler_rate_percent": round(total_fillers / max(word_count, 1) * 100, 2),
    }
