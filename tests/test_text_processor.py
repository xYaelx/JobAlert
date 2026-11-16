from config import JOB_KEYWORDS
from text_processor import normalize_text, needs_llm_decision, build_job_regex

# The regex is built from a plain keyword list
def test_build_job_regex_from_plain_keywords():
    regex = build_job_regex(["computer vision", "ml", "למידה עמוקה"])
    assert regex.search("senior computer vision engineer")
    assert regex.search("ml researcher")
    assert not regex.search("html developer")       # ASCII keywords match whole words only
    assert regex.search("ניסיון בלמידה עמוקה")      # Hebrew keywords allow an attached prefix letter

# Every configured keyword triggers the prefilter
def test_every_config_keyword_triggers_llm():
    for keyword in JOB_KEYWORDS:
        decision = needs_llm_decision(normalize_text(f"hiring {keyword} engineer now"))
        assert decision["needs_llm"], keyword

# Test for the normalize_text function
def test_normalize_text():
    assert normalize_text("   Hello!! 😊") == "hello"
    assert normalize_text("Testing punctuation!!! 1234...") == "testing punctuation 1234"
    assert normalize_text("") == ""
    assert normalize_text(None) == ""

# Non-word characters become a space instead of gluing words together
def test_normalize_text_replaces_separators_with_space():
    assert normalize_text("computer-vision") == "computer vision"
    assert normalize_text("4/26") == "4 26"
    assert normalize_text("ML/DL") == "ml dl"
    assert normalize_text("Algorithm Engineer (PyTorch)") == "algorithm engineer pytorch"

# Hebrew vowel marks are dropped, not turned into spaces that split the word
def test_normalize_text_keeps_hebrew_words_with_niqqud_whole():
    assert normalize_text("דָּרוּשׁ") == "דרוש"

# Test for needs_llm_decision with very short text
def test_too_short_message():
    decision = needs_llm_decision(normalize_text("PyTorch!"))
    assert not decision["needs_llm"]
    assert "too_short" in decision["reasons"]

# Test for needs_llm_decision when no job keyword is mentioned
def test_no_job_keyword_match():
    decision = needs_llm_decision(normalize_text("Senior Frontend Developer, React, remote"))
    assert not decision["is_relevant"]
    assert not decision["needs_llm"]
    assert "no_job_keyword_match" in decision["reasons"]

# Hyphenated and slashed keywords still match after normalization
def test_job_keyword_with_separators():
    for text in ["Computer-Vision Algorithm Engineer, Tel Aviv", "Looking for an ML/DL researcher"]:
        decision = needs_llm_decision(normalize_text(text))
        assert decision["needs_llm"], text
        assert "job_keyword_match" in decision["reasons"]

# Short keywords must not match inside other words
def test_short_keyword_does_not_match_inside_words():
    decision = needs_llm_decision(normalize_text("HTML and XML developer wanted"))
    assert not decision["needs_llm"]

# Hebrew keywords match even with an attached prefix letter (ב, ל, ו...)
def test_hebrew_keyword_with_prefix():
    decision = needs_llm_decision(normalize_text("דרושה אלגוריתמיקאית עם ניסיון בלמידה עמוקה"))
    assert decision["needs_llm"]

# Heuristics never mark a post relevant on their own; the LLM decides
def test_keyword_match_is_not_relevant_without_llm():
    decision = needs_llm_decision(normalize_text("Deep Learning engineer, PyTorch, Haifa"))
    assert not decision["is_relevant"]
    assert decision["needs_llm"]
