"""
NBAVision Engine — Reply generation.
Without LLM API key: uses template replies (no Groq, no setup).
With LLM API key: uses Groq for AI-generated replies. Handles 429 with backoff.
"""
import json
import random
import re
import time
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

SYSTEM_PROMPT = """You are an NBA fan who's always on X. You watch games, you have opinions, you're quick.

You reply to tweets the way a real person does — fast, confident, sometimes a little rough.

OUTPUT FORMAT (STRICT)

Return exactly one JSON object:

{
  "decision": "REPLY" or "SKIP",
  "reason": "...",
  "response": "..."
}

BIAS TOWARD REPLY. Your default is REPLY. Only SKIP if there is a clear reason not to.

If REPLY:
- ≤180 characters
- No hashtags, no links, no promotion
- Max one emoji (most replies should have zero)
- Specific to THIS tweet's content

ONLY SKIP if:
- Death, serious crime, or heavy politics
- Tweet is in a language you can't reply to naturally
- Tweet is literally just a link with no text

Do NOT skip just because a tweet is "too viral" or "nothing to add". There's always something to say if it's about basketball.

VOICE

Write like a real fan on their phone:
- Slightly opinionated
- Comfortable being blunt
- Uses short sentences naturally
- Sometimes agrees and adds a detail
- Sometimes pushes back
- Occasionally funny or dry
- Never sounds like a TV analyst or a blog

BANNED PHRASES

Never use: "I'd argue", "speaks volumes", "at the end of the day", "it will be interesting", "cannot let", "that type of", "key factor", "moving forward", "the question is", "only time will tell"

Never use abstract filler: chemistry, resilience, upside, value, efficiency, narrative

REPLY TYPES (mix these)

- Quick agree + detail: "Yeah his midrange has been different since January"
- Pushback: "Nah that's a regular season take. Playoffs he's getting trapped"
- Observation: "Watch his feet on that closeout. That's why he's elite"
- Prediction: "This team is a second-round exit and everyone knows it"
- Vibe: "They just look flat out there"
- Humor: "Bro got cooked so bad the arena went quiet"

LENGTH: 60–150 characters. Short and sharp > long and safe.

Return only the JSON."""


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
            print("    LLM: template mode — skip (sensitive)", flush=True)
            return {"decision": "SKIP", "reason": "template_skip", "response": ""}
        reply = random.choice(TEMPLATE_REPLIES)
        print(f"    LLM: template reply ({len(reply)} chars)", flush=True)
        return {
            "decision": "REPLY",
            "reason": "template",
            "response": reply,
        }

    model = get_llm_model()
    print(f"    LLM: calling Groq ({model})...", flush=True)
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    user_content = f"Tweet:\n{tweet_text or ''}\n\nAuthor:\n{tweet_author or 'unknown'}"

    max_attempts = LLM_RETRY_MAX + 1
    max_429_backoffs = 3
    last_err = None

    for attempt in range(max_attempts + max_429_backoffs):
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

            if r.status_code == 429:
                retry_after = 30
                if "Retry-After" in r.headers:
                    try:
                        retry_after = int(r.headers["Retry-After"])
                    except ValueError:
                        pass
                retry_after = min(90, max(retry_after, 25))
                if attempt < max_attempts + max_429_backoffs - 1:
                    print(f"    LLM: 429 rate limit — waiting {retry_after}s then retry", flush=True)
                    time.sleep(retry_after)
                    continue
                last_err = "429 Too Many Requests"
                print(f"    LLM: 429 — all backoffs exhausted", flush=True)
                break

            r.raise_for_status()
            data = r.json()
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            parsed = _extract_json(content)
            if parsed and isinstance(parsed.get("decision"), str):
                dec = (parsed.get("decision") or "").upper()
                reason = (parsed.get("reason") or "")[:80]
                print(f"    LLM: {dec} — {reason}", flush=True)
                return parsed
            print("    LLM: invalid output -> SKIP", flush=True)
            return {"decision": "SKIP", "reason": "invalid_llm_output", "response": ""}
        except requests.Timeout:
            last_err = "timeout"
            print(f"    LLM: timeout (attempt {attempt + 1})", flush=True)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                retry_after = 35
                if e.response.headers.get("Retry-After"):
                    try:
                        retry_after = int(e.response.headers["Retry-After"])
                    except ValueError:
                        pass
                retry_after = min(90, max(retry_after, 25))
                if attempt < max_attempts + max_429_backoffs - 1:
                    print(f"    LLM: 429 — waiting {retry_after}s then retry", flush=True)
                    time.sleep(retry_after)
                    continue
            last_err = str(e)
            print(f"    LLM: error — {e}", flush=True)
        except Exception as e:
            last_err = str(e)
            print(f"    LLM: error — {e}", flush=True)

    print("    LLM: all attempts failed -> None", flush=True)
    return None
