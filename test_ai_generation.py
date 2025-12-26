"""
Smoke tests for AI draft generation helper.
"""
from app import generate_ai_draft, normalize_doc_type


def test_ai_generation_from_prompt_and_file():
    print("Testing AI draft generation with prompt and file text...")
    title, content = generate_ai_draft(
        "Maak een rapport over veiligheid en risico management.",
        "Belangrijk: veiligheidsbeleid\n- Processen verbeteren\n- Training en communicatie",
        "report",
    )

    assert "rapport" in title.lower() or "veiligheid" in title.lower()
    assert "Context" in content
    assert "veilig" in content.lower() or "risico" in content.lower()
    assert "Recommendations" in content
    print("[PASS] AI draft with prompt and file generated")


def test_ai_generation_defaults_to_general():
    print("Testing AI draft generation defaults for unknown doc type...")
    title, content = generate_ai_draft("", "", "unknown")
    assert normalize_doc_type("unknown") == "general"
    assert title.startswith("AI General Draft")
    assert "Overview" in content
    print("[PASS] AI draft defaulted to general")


if __name__ == "__main__":
    test_ai_generation_from_prompt_and_file()
    test_ai_generation_defaults_to_general()
    print("All AI draft generation tests passed.")
