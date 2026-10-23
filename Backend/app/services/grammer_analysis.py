
import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

client = genai.Client(api_key=API_KEY) if API_KEY else None


class GrammarAnalysisError(Exception):
    """Raised when grammar analysis cannot be completed."""


def _parse_json(response_text: str) -> dict[str, Any]:
    text = response_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GrammarAnalysisError(
            "The grammar model returned invalid JSON."
        ) from exc

    if not isinstance(result, dict):
        raise GrammarAnalysisError("Invalid grammar response format.")

    return result


def analyze_grammar(text: str) -> dict[str, Any]:
    """Analyze an English transcript using Gemini."""

    if not isinstance(text, str):
        raise ValueError("text must be a string")

    text = text.strip()

    if not text:
        return {
            "score": 100.0,
            "total_words": 0,
            "error_count": 0,
            "grammar_errors": [],
            "corrected_text": "",
            "feedback": "No text was provided.",
        }

    if len(text) > 20000:
        raise ValueError("Text is too long. Maximum length is 20000 characters.")

    if client is None:
        raise GrammarAnalysisError(
            "GEMINI_API_KEY is missing. Configure it in Backend/.env."
        )

    prompt = f"""
You are an English grammar assessment assistant.

Analyze the student's original transcript for genuine grammar errors.
Preserve the intended meaning. Do not invent errors or penalize acceptable
informal speech. Avoid duplicate errors. Focus on grammar, tense,
subject-verb agreement, articles, prepositions, sentence structure,
pronouns, and word choice.

Return valid JSON only, using exactly this structure:
{{
  "grammar_errors": [
    {{
      "original": "incorrect phrase",
      "correction": "correct phrase",
      "explanation": "Short explanation",
      "category": "tense"
    }}
  ],
  "corrected_text": "Corrected complete transcript",
  "feedback": "Brief constructive feedback"
}}

If no errors exist, return an empty grammar_errors array.

Transcript:
<transcript>
{text}
</transcript>
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        if not response.text:
            raise GrammarAnalysisError("The grammar model returned no text.")

        data = _parse_json(response.text)

    except GrammarAnalysisError:
        raise
    except Exception as exc:
        raise GrammarAnalysisError(
            "Grammar analysis is temporarily unavailable."
        ) from exc

    raw_errors = data.get("grammar_errors", [])

    if not isinstance(raw_errors, list):
        raise GrammarAnalysisError("Invalid grammar_errors field.")

    errors = []

    for item in raw_errors:
        if not isinstance(item, dict):
            continue

        original = item.get("original")
        correction = item.get("correction")
        explanation = item.get("explanation")
        category = item.get("category", "other")

        if not all(
            isinstance(value, str)
            for value in (original, correction, explanation, category)
        ):
            continue

        errors.append({
            "original": original,
            "correction": correction,
            "explanation": explanation,
            "category": category,
        })

    corrected_text = data.get("corrected_text", text)
    feedback = data.get("feedback", "Grammar analysis completed.")

    if not isinstance(corrected_text, str):
        corrected_text = text

    if not isinstance(feedback, str):
        feedback = "Grammar analysis completed."

    total_words = len(re.findall(r"\b[\w'-]+\b", text))
    error_count = len(errors)

    score = round(max(0.0, 100.0 - error_count * 5.0), 2)

    return {
        "score": score,
        "total_words": total_words,
        "error_count": error_count,
        "grammar_errors": errors,
        "corrected_text": corrected_text,
        "feedback": feedback,
    }


def grammar_analysis(text: str) -> dict[str, Any]:
    return analyze_grammar(text)
