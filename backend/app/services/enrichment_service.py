import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

ENRICHMENT_PROMPT = """Analyze this podcast transcript segment where the keyword "{keyword}" was mentioned.

Transcript segment:
---
{segment}
---

Respond with ONLY valid JSON (no markdown, no explanation):
{{
  "sentiment": "positive" | "negative" | "neutral" | "mixed",
  "sentiment_score": 0.0 to 1.0 (0=very negative, 1=very positive),
  "context_summary": "1-2 sentence summary of how the keyword is discussed",
  "topics": ["topic1", "topic2"],
  "is_buying_signal": true/false (speaker expresses intent to purchase/adopt),
  "is_pain_point": true/false (speaker describes a problem or frustration),
  "is_recommendation": true/false (speaker recommends or endorses)
}}"""


def enrich_mention(keyword: str, segment: str) -> dict:
    """Call the configured LLM provider to analyze a transcript segment."""
    prompt = ENRICHMENT_PROMPT.format(keyword=keyword, segment=segment)

    try:
        content = _call_llm(prompt)
        parsed = json.loads(content)
        return _validate_enrichment(parsed)
    except Exception:
        logger.exception("Enrichment failed")
        return _default_enrichment()


def _call_llm(prompt: str) -> str:
    if settings.LLM_PROVIDER == "openrouter":
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        if settings.OPENROUTER_SITE_URL:
            headers["HTTP-Referer"] = settings.OPENROUTER_SITE_URL
        if settings.OPENROUTER_APP_NAME:
            headers["X-Title"] = settings.OPENROUTER_APP_NAME

        response = httpx.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json={
                "model": settings.OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            },
            timeout=120.0,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    response = httpx.post(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json={
            "model": settings.OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
        },
        timeout=120.0,
    )
    response.raise_for_status()
    result = response.json()
    return result["message"]["content"]


def _validate_enrichment(data: dict) -> dict:
    """Ensure enrichment response has all required fields with correct types."""
    return {
        "sentiment": str(data.get("sentiment", "neutral")),
        "sentiment_score": float(data.get("sentiment_score", 0.5)),
        "context_summary": str(data.get("context_summary", "")),
        "topics": list(data.get("topics", [])),
        "is_buying_signal": bool(data.get("is_buying_signal", False)),
        "is_pain_point": bool(data.get("is_pain_point", False)),
        "is_recommendation": bool(data.get("is_recommendation", False)),
    }


def _default_enrichment() -> dict:
    return {
        "sentiment": "neutral",
        "sentiment_score": 0.5,
        "context_summary": "Enrichment unavailable",
        "topics": [],
        "is_buying_signal": False,
        "is_pain_point": False,
        "is_recommendation": False,
    }
