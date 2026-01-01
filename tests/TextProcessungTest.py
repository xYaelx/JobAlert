import pytest
import re
from text_processor import normalize_text, needs_llm_decision, MED_REGEX, GIVING_SELLING_INTENT, QUESTION_WORDS

# Test for the normalize_text function
def test_normalize_text():
    assert normalize_text("   Hello!! 😊") == "hello"
    assert normalize_text("Gonal, GONAL!!   ") == "gonal gonal"
    assert normalize_text("   מנופור!    ") == "מנופור"
    assert normalize_text("Testing punctuation!!! 1234...") == "testing punctuation 1234"
    assert normalize_text("") == ""

# Test for needs_llm_decision when medication is mentioned but no explicit intent
def test_medication_without_clear_intent():
    text = "אני מחפשת גונל"
    decision = needs_llm_decision(normalize_text(text))
    assert not decision["is_relevant"]
    assert decision["needs_llm"]
    assert "medication_without_clear_intent" in decision["reasons"]

# Test for needs_llm_decision when clear intent to give/sell medication is found
def test_clear_giving_intent():
    text = "יש לי גונל למסירה"
    decision = needs_llm_decision(normalize_text(text))
    assert decision["is_relevant"]
    assert not decision["needs_llm"]
    assert "explicit_giving_or_selling_intent" in decision["reasons"]

# Test for needs_llm_decision when message is a question
def test_question_detected():
    text = "מישהי יודעת איפה אפשר לקנות גונל?"
    decision = needs_llm_decision(normalize_text(text))
    assert not decision["is_relevant"]
    assert not decision["needs_llm"]
    assert "question_detected" in decision["reasons"]

# Test for needs_llm_decision when no medication is mentioned
def test_no_medication_match():
    text = "היי, איך אתם?"
    decision = needs_llm_decision(normalize_text(text))
    assert not decision["is_relevant"]
    assert not decision["needs_llm"]
    assert "no_medication_match" in decision["reasons"]

# Test for needs_llm_decision with very short text
def test_too_short_message():
    text = "Gonal"
    decision = needs_llm_decision(normalize_text(text))
    assert not decision["is_relevant"]
    assert not decision["needs_llm"]
    assert "too_short" in decision["reasons"]

# Test for needs_llm_decision with a valid giving intent but no medication
def test_explicit_intent_without_medication():
    text = "יש לי תרופה למסירה"
    decision = needs_llm_decision(normalize_text(text))
    assert not decision["is_relevant"]
    assert not decision["needs_llm"]
    assert "no_medication_match" in decision["reasons"]

# Test for needs_llm_decision with a message that includes both medication and a question
def test_medication_and_question():
    text = "מישהי יודעת איפה אפשר לקנות גונל?"
    decision = needs_llm_decision(normalize_text(text))
    assert not decision["is_relevant"]
    assert not decision["needs_llm"]
    assert "question_detected" in decision["reasons"]

# Test for needs_llm_decision with multiple medications mentioned
def test_multiple_medications():
    text = "אני צריכה גונל ומנופור"
    decision = needs_llm_decision(normalize_text(text))
    assert not decision["is_relevant"]
    assert decision["needs_llm"]
    assert "medication_without_clear_intent" in decision["reasons"]
