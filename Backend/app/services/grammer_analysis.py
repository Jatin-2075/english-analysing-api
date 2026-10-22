import difflib
import re
from functools import lru_cache

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "grammarly/coedit-large"


@lru_cache(maxsize=1)
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    model.eval()
    return tokenizer, model


def _normalize(words):
    return re.sub(r"[^\w]", "", " ".join(words)).lower()


def build_errors(original: str, corrected: str):
    """Word-level diff between the original and the model-corrected text."""
    a, b = original.split(), corrected.split()
    errors = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            continue
        old, new = a[i1:i2], b[j1:j2]
        if tag == "replace" and _normalize(old) == _normalize(new):
            category, message = "Punctuation / capitalization", "Fix punctuation or capitalization"
        elif tag == "replace":
            category, message = "Wording", "Consider rewording"
        elif tag == "delete":
            category, message = "Unnecessary word", "This word is probably not needed"
        else:
            category, message = "Missing word", "A word seems to be missing"
        mistake = " ".join(old) or (a[i1 - 1] if i1 > 0 else "")
        errors.append({
            "message": message,
            "mistake": mistake,
            "suggestions": [" ".join(new)] if new else [],
            "category": category,
        })
    return errors, len(a)


def analyze_grammar(text: str) -> dict:
    text = text.strip()

    if not text:
        return {"original_text": text, "corrected_text": text, "changes_detected": False,
                "word_count": 0, "grammar_error_count": 0, "grammar_score": 0, "errors": [],
                "error": "Text cannot be empty"}

    tokenizer, model = load_model()

    prompt = f"Fix grammatical errors in this sentence: {text}"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

    with torch.inference_mode():
        outputs = model.generate(**inputs, max_new_tokens=256, num_beams=4)

    corrected = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    errors, word_count = build_errors(text, corrected)
    changed = sum(max(1, len(e["mistake"].split())) for e in errors)
    score = max(0, round(100 * (1 - changed / max(word_count, 1))))

    return {
        "original_text": text,
        "corrected_text": corrected,
        "changes_detected": corrected != text,
        "word_count": word_count,
        "grammar_error_count": len(errors),
        "grammar_score": score,
        "errors": errors,
    }
