
def build_word_suggestion(original_word: str, suggested_word: str | None = None) -> dict:
    original = original_word.strip()
    suggestion = suggested_word.strip() if suggested_word else None

    if not original:
        raise ValueError("Original word cannot be empty.")

    return {
        "original_word": original,
        "suggested_word": suggestion,
        "confirmed_word": None,
        "requires_confirmation": suggestion is not None,
    }


def confirm_word(original_word: str, suggested_word: str | None, confirmed_word: str) -> dict:
    original = original_word.strip()
    confirmed = confirmed_word.strip()

    if not original:
        raise ValueError("Original word cannot be empty.")

    if not confirmed:
        raise ValueError("Confirmed word cannot be empty.")

    return {
        "original_word": original,
        "suggested_word": suggested_word.strip() if suggested_word else None,
        "confirmed_word": confirmed,
        "user_confirmed": True,
        "is_name": True,
    }
