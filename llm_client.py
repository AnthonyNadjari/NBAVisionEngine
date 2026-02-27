"""
NBAVision Engine — LLM API (Section 7): Groq free tier, REST, timeout 20s, retry 2.
"""
import json
import re
import requests
from config import get_llm_api_key, get_llm_model, LLM_TIMEOUT_SECONDS, LLM_RETRY_MAX

SYSTEM_PROMPT = """You are a professional NBA analyst replying on Twitter.

Your goal is to increase profile visibility while remaining safe and natural.

You must evaluate the tweet carefully.

SKIP if:
* Mentions death, crime, politics, war, scandal.
* Pure breaking news without angle.
* Engagement already extremely high (>5000 likes).
* No room for insight.

If replying:

STYLE RULES:
* ≤ 180 characters.
* Human tone.
* Confident but calm.
* No promotion.
* No hashtags.
* No links.
* Max one emoji.
* Avoid clichés.
* No robotic phrasing.
* No template repetition.
* Do not mirror tweet wording.
* Provide ONE sharp insight only.
* Vary structure.
* Do not start every response with the same word.
* Sometimes tactical.
* Sometimes strategic.
* Sometimes matchup-based.
* Avoid always referencing betting lines.

Return ONLY JSON:

{
"decision": "REPLY" or "SKIP",
"reason": "...",
"response": "..."
}

No extra text."""


def _extract_json(text: str) -> dict | None:
    """Try to parse JSON from LLM output (allow markdown code block)."""
    text = (text or "").strip()
    # Try raw parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try ```json ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Try first { ... }
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def call_llm(tweet_text: str, tweet_author: str = "") -> dict | None:
    """
    Call Groq API. Returns {"decision": "REPLY"|"SKIP", "reason": "...", "response": "..."} or None on timeout/error.
    """
    api_key = get_llm_api_key()
    if not api_key:
        return None

    model = get_llm_model()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    user_content = f"Tweet by @{tweet_author}:\n\n{tweet_text}" if tweet_author else tweet_text

    last_err = None
    for attempt in range(LLM_RETRY_MAX + 1):
        try:
            r = requests.post(
                url,
                headers=headers,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    "max_tokens": 256,
                    "temperature": 0.7,
                },
                timeout=LLM_TIMEOUT_SECONDS,
            )
            r.raise_for_status()
            data = r.json()
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            parsed = _extract_json(content)
            if parsed and isinstance(parsed.get("decision"), str):
                return parsed
            return {"decision": "SKIP", "reason": "invalid_llm_output", "response": ""}
        except requests.Timeout:
            last_err = "timeout"
        except Exception as e:
            last_err = str(e)
    return None
