import language_tool_python


tool = language_tool_python.LanguageTool("en-US")


def analyze_grammar(transcript: str) -> dict:
    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty")

    matches = tool.check(transcript)
    errors = []

    for match in matches:
        errors.append({
            "message": match.message,
            "mistake": transcript[match.offset:match.offset + match.errorLength],
            "suggestions": match.replacements[:5],
            "category": match.category,
        })

    word_count = len(transcript.split())
    error_count = len(errors)

    return {
        "word_count": word_count,
        "grammar_error_count": error_count,
        "grammar_score": round(max(0, 100 - (error_count / max(word_count, 1)) * 100), 2),
        "errors": errors,
    }