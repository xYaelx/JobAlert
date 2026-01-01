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
    """
    Performs deterministic preprocessing on text, handling emojis, punctuation,
    and whitespace to produce a clean, normalized string.
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


def needs_llm_decision(chat_text):
    """
    Filters out irrelevant messages.

    Returns a decision object with:
    - is_relevant: message is an offer for fertility meds
    - needs_llm: requires LLM to disambiguate
    - reasons: decision trace for debugging
    - signals: extracted heuristic signals

    :param chat_text: normalized message text
    :return: dict
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