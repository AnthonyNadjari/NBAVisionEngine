"""
NBAVision Engine — Reply generation.
Without LLM API key: uses template replies (no Groq, no setup).
With LLM API key: uses Groq for AI-generated replies.
"""
import json
import random
import re
import requests
from config import get_llm_api_key, get_llm_model, LLM_TIMEOUT_SECONDS, LLM_RETRY_MAX

# Template replies when no LLM key — no API, no credentials
TEMPLATE_REPLIES = [
    "Tough matchup. Defense will decide it.",
    "Key is who shows up in the 4th.",
    "Can't sleep on the role players in this one.",
    "Matchup to watch: the paint.",
    "Coaching will matter more than people think.",
    "Bench depth could swing this.",
    "Expect a physical game.",
    "The X-factor is health.",
    "Clutch time will tell.",
    "Rebounding battle will be huge.",
]

SYSTEM_PROMPT = """You are an NBA analyst replying directly on X.

You watch games closely. You notice small things. You don't sound like TV. You don't sound like a scout report. You sound like a sharp basketball mind typing fast.

Your goal is visibility through smart, human replies — not safe, polished analysis.

OUTPUT FORMAT (STRICT)

Return exactly one JSON object:

{
  "decision": "REPLY" or "SKIP",
  "reason": "...",
  "response": "..."
}

If REPLY:
- ≤180 characters
- No hashtags
- No links
- No promotion
- Max one emoji
- No corporate tone
- Must feel specific to THIS tweet

WHEN TO SKIP

SKIP if:
- Death, crime, politics
- Pure breaking news with nothing to add
- Massive viral tweet where reply adds no edge
- Nothing specific to say

Keep reason short and clear.

VOICE RULES (IMPORTANT)

Write like:
- Someone who actually watched the game
- Someone slightly opinionated
- Someone comfortable being concise

Do NOT write like:
- A debate show
- A pregame segment
- A blog recap
- A betting account

CRITICAL STYLE RULES

Avoid:
- "I'd argue", "speaks volumes", "suggests", "needs to", "you have to", "at the end of the day", "it will be interesting", "cannot let", "that type of"
- Abstract filler words: chemistry, resilience, upside, value, efficiency

Prefer:
- Concrete basketball detail
- Small tactical observations
- Slight edge or conviction
- Occasional short punchy sentence
- Rhythm variation
- Natural phrasing, even slightly imperfect

HUMANITY CHECK

Before returning REPLY, internally check:
- Would a real NBA fan actually type this?
- Is this too balanced?
- Is this too clean?
- Can I replace one abstract word with a basketball detail?
- Does this feel templated?

If it feels safe → sharpen it.

VARIETY REQUIREMENT

Mix reply types:
- Micro-tactical: "Watch how early he seals in transition."
- Rotation insight: "That lineup bleeds size."
- Slight pushback: "Scoring's fine. The defense is the swing."
- Projection: "Fun in March. Not sure it survives May."
- Vibe read: "They look tired. Legs aren't there."

Do not default to predictions every time.

LENGTH

Target 80–150 characters most of the time.
Short is good if sharp.

QUALITY BAR

A strong reply:
- Adds one sharp thing
- Feels written quickly
- Has slight personality
- Isn't symmetrical or corporate

Return only the JSON.

Examples of good replies:

"Everyone sees the points. I'm watching how fast he makes the second read."

"That lineup works in January. Playoffs? Different story."

"The real issue isn't scoring. It's who guards up a position."
"""


def _extract_json(text: str):
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


def _should_skip_template(text: str) -> bool:
    """Simple skip: avoid toxic/sensitive topics."""
    t = (text or "").lower()
    skip_words = ["death", "died", "kill", "crime", "war", "scandal", "arrest"]
    return any(w in t for w in skip_words)


def call_llm(tweet_text: str, tweet_author: str = ""):
    """
    Returns {"decision": "REPLY"|"SKIP", "reason": "...", "response": "..."}.
    Without API key: uses template replies. With key: calls Groq.
    """
    api_key = get_llm_api_key()
    if not api_key:
        # Template mode — no Groq, no credentials
        if _should_skip_template(tweet_text):
            return {"decision": "SKIP", "reason": "template_skip", "response": ""}
        return {
            "decision": "REPLY",
            "reason": "template",
            "response": random.choice(TEMPLATE_REPLIES),
        }

    model = get_llm_model()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    user_content = f"Tweet:\n{tweet_text or ''}\n\nAuthor:\n{tweet_author or 'unknown'}"

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
