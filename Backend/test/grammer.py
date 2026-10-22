import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.grammer_analysis import analyze_grammar

def test_grammar_analysis():
    print("Starting grammar test...", flush=True)
    text = "She go to school every day."

    result = analyze_grammar(text)

    print("Original:", result["original_text"])
    print("Corrected:", result["corrected_text"])
    print("Changes detected:", result["changes_detected"])

    assert result["original_text"] == text
    assert result["corrected_text"]
    assert isinstance(result["changes_detected"], bool)


if __name__ == "__main__":
    test_grammar_analysis()