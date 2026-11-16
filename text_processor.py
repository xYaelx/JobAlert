import re

# normalize_text strips punctuation without inserting a space ("computer-vision" -> "computervision"),
# so multi-word terms allow an optional space
JOB_REGEX = re.compile(
    r"(computer\s?vision|deep\s?learning|machine\s?learning|"
    r"pytorch|opencv|tensorflow|"
    r"algorithms?|image\s?processing|object\s?detection|segmentation|perception|"
    r"\bml|\bdl\b|"
    r"ראייה ממוחשבת|ראיה ממוחשבת|למידה עמוקה|למידת מכונה|אלגוריתמיקאי|אלגוריתמים)",
    re.IGNORECASE
)


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
    2. CV/ML job keyword (regex pattern match)

    Relevance depends on the candidate profile (role, seniority, location),
    which keywords cannot judge, so every keyword match goes to the LLM.

    Args:
        chat_text: Normalized message text.

    Returns:
        Dictionary with keys:
            - is_relevant (bool): Never set by heuristics; kept for the pipeline
            - needs_llm (bool): LLM classification required
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

    # 2. Detect CV/ML job keywords
    has_job_keyword = bool(JOB_REGEX.search(chat_text))
    decision["signals"]["has_job_keyword"] = has_job_keyword

    if not has_job_keyword:
        decision["reasons"].append("no_job_keyword_match")
        return decision

    # Keyword found → LLM judges fit against the profile
    decision["needs_llm"] = True
    decision["reasons"].append("job_keyword_match")

    return decision