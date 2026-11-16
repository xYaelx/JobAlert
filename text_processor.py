import re
import unicodedata
from config import JOB_KEYWORDS


def build_job_regex(keywords: list[str]) -> re.Pattern:
    """Build a case-insensitive regex matching any of the plain keyword phrases.

    ASCII keywords match whole words only ("ml" must not match "html").
    Hebrew keywords match as substrings, since Hebrew attaches prefix
    letters (ב, ל, ו...) directly to the word ("בלמידה עמוקה").
    """
    patterns = [
        rf"\b{re.escape(kw)}\b" if kw.isascii() else re.escape(kw)
        for kw in keywords
    ]
    return re.compile("|".join(patterns), re.IGNORECASE)


JOB_REGEX = build_job_regex(JOB_KEYWORDS)


def normalize_text(text: str) -> str:
    """Normalize and clean text for consistent processing.
    
    Performs deterministic preprocessing to handle variations in text:
    - Converts to lowercase for case-insensitive matching
    - Drops combining marks (e.g. Hebrew niqqud) so words stay whole
    - Replaces emojis, punctuation, and other non-word characters with a space
      ("computer-vision" → "computer vision", "4/26" → "4 26")
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

    # 2. Drop combining marks (niqqud, accents); they are not \w and would otherwise split words
    text = "".join(ch for ch in text if not unicodedata.category(ch).startswith("M"))

    # 3. Replace emojis, punctuation, and other non-alphanumeric/non-space symbols with a space.
    # [^\w\s] matches anything that is NOT a word character (letter\char\underscore) or whitespace.
    text = re.sub(r'[^\w\s]', ' ', text, flags=re.UNICODE)

    # 4. Normalize whitespace: replace multiple spaces with a single space and strip leading/trailing spaces
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