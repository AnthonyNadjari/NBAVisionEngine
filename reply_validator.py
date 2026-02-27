"""
NBAVision Engine — Vérification avancée des réponses (Spec Section 9).
"""
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from config import (
    MAX_RESPONSES_SAME_FIRST_WORD,
    MAX_EMOJIS_IN_SESSION,
    MAX_SENTENCES,
    TFIDF_SIMILARITY_THRESHOLD,
)


def _first_word(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    return t.split()[0].lower() if t.split() else ""


def _count_emojis(text: str) -> int:
    # Simple emoji count: common Unicode ranges + common symbols
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F9FF"  # misc symbols and pictographs
        "\U0001F600-\U0001F64F"  # emoticons
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "]+",
        flags=re.UNICODE,
    )
    return len(emoji_pattern.findall(text or ""))


def _count_sentences(text: str) -> int:
    if not (text or "").strip():
        return 0
    return max(1, len(re.split(r"[.!?]+", text.strip())))


def _tfidf_similarity(new_text: str, previous_texts: list[str]) -> float:
    """Return max similarity between new_text and any of previous_texts (0..1)."""
    if not previous_texts or not (new_text or "").strip():
        return 0.0
    try:
        vectorizer = TfidfVectorizer()
        all_texts = previous_texts + [new_text]
        matrix = vectorizer.fit_transform(all_texts)
        from sklearn.metrics.pairwise import cosine_similarity
        new_vec = matrix[-1:]
        prev_matrix = matrix[:-1]
        sims = cosine_similarity(new_vec, prev_matrix)[0]
        return float(sims.max()) if len(sims) else 0.0
    except Exception:
        return 0.0


def validate_reply(
    response: str,
    session_replies: list[str],
) -> tuple[bool, str | None]:
    """
    Vérifier (Section 9):
    - Moins de 3 réponses commençant par même mot
    - Moins de 3 emojis dans session (total)
    - Pas plus de 2 phrases
    - Similarité TF-IDF < 0.7 avec toutes réponses précédentes
    Returns (valid, reason). valid=True means OK to post.
    """
    if not (response or "").strip():
        return False, "empty"

    first = _first_word(response)
    if first:
        same_first = sum(1 for r in session_replies if _first_word(r) == first)
        if same_first >= MAX_RESPONSES_SAME_FIRST_WORD:
            return False, "too_many_same_first_word"

    total_emojis = _count_emojis(response) + sum(_count_emojis(r) for r in session_replies)
    if total_emojis >= MAX_EMOJIS_IN_SESSION:
        return False, "too_many_emojis"

    if _count_sentences(response) > MAX_SENTENCES:
        return False, "too_many_sentences"

    if session_replies and _tfidf_similarity(response, session_replies) >= TFIDF_SIMILARITY_THRESHOLD:
        return False, "too_similar"

    return True, None
