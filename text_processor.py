import re

MED_REGEX = re.compile(
    r"(גונל|gonal|גונאל|גונל[-\s]?אף|"
    r"צטרוטייד|צטרוטיד|cetrotide|"
    r"מנופור|menopur|"
    r"אוביטרל|ovitrelle)",
    re.IGNORECASE
)

GIVING_SELLING_INTENT = [ "למסירה", "למכירה", "מוכרת", "מוכר", "נותנת", "יש לי", "נשאר", "מסירה", "מכירה", "לתת", "לתרום" ]
QUESTION_WORDS = ["מישהי", "מישהו", "יודעת", "יש המלצה", "איפה"] # no ? after text normalization so check it by other words


def normalize_text(text: str) -> str:
    """Normalize and clean text for consistent processing.
    
    Performs deterministic preprocessing to handle variations in text:
    - Converts to lowercase for case-insensitive matching
    - Removes emojis, punctuation, and non-alphanumeric characters
    - Normalizes whitespace (multiple spaces → single space)
    
    Args:
        text: Raw input text (may contain mixed case, emojis, punctuation).
        
    Returns:
        Normalized text suitable for heuristic matching and LLM classification.
        Returns empty string if input is not a string.
    """
    if not isinstance(text, str):
        return ""

    # 1. Convert to lowercase
    text = text.lower()

    # 2. Remove emojis, punctuation, and other non-alphanumeric/non-space symbols.
    # [^\w\s] matches anything that is NOT a word character (letter\char\underscore) or whitespace.
    text = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)

    # 3. Normalize whitespace: replace multiple spaces with a single space and strip leading/trailing spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def needs_llm_decision(chat_text: str) -> dict:
    """Determine if message requires LLM classification.
    
    Applies heuristic filters in sequence to classify messages without LLM.
    Messages that pass heuristic filters or need disambiguation are routed
    to LLM; others are filtered out early for efficiency.
    
    Filter sequence:
    1. Message length (minimum 3 words)
    2. Medication mention (regex pattern match)
    3. Question detection (common Hebrew question words)
    4. Explicit giving/selling intent (keyword pattern match)
    
    Args:
        chat_text: Normalized message text.
        
    Returns:
        Dictionary with keys:
            - is_relevant (bool): Message appears to be a medication offer
            - needs_llm (bool): LLM classification required for disambiguation
            - reasons (list): Chain of filtering decisions for debugging
            - signals (dict): Extracted features used in decisions
    """
    decision = {
        "is_relevant": False,
        "needs_llm": False,
        "reasons": [],
        "signals": {}
    }

    words_count = len(chat_text.split())
    decision["signals"]["words_count"] = words_count

    # 1. Filter out very short messages
    if words_count < 3:
        decision["reasons"].append("too_short")
        return decision

    # 2. Detect medication mention
    has_med = bool(MED_REGEX.search(chat_text))
    decision["signals"]["has_med"] = has_med

    if not has_med:
        decision["reasons"].append("no_medication_match")
        return decision

    # 3. Filter out questions
    is_question = any(q in chat_text for q in QUESTION_WORDS)
    decision["signals"]["is_question"] = is_question

    if is_question:
        decision["reasons"].append("question_detected")
        return decision

    # 4. Detect explicit giving / selling intent
    give_intent_regex = re.compile(
        "|".join(map(re.escape, GIVING_SELLING_INTENT))
    )
    has_explicit_intent = bool(give_intent_regex.search(chat_text))
    decision["signals"]["has_explicit_intent"] = has_explicit_intent

    # Case A: clear offer → no LLM needed
    if has_explicit_intent:
        decision["is_relevant"] = True
        decision["needs_llm"] = False
        decision["reasons"].append("explicit_giving_or_selling_intent")
        return decision

    # Case B: medication mentioned but intent unclear → LLM candidate
    decision["is_relevant"] = False
    decision["needs_llm"] = True
    decision["reasons"].append("medication_without_clear_intent")

    return decision