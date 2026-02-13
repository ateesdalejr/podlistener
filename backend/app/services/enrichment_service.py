import json
import logging
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
_RATE_LIMIT_LOCK = threading.Lock()
_NEXT_ALLOWED_TS = 0.0

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


def enrich_mention(keyword: str, segment: str, raise_on_error: bool = False) -> dict:
    """Call the configured LLM provider to analyze a transcript segment."""
    prompt = ENRICHMENT_PROMPT.format(keyword=keyword, segment=segment)

    try:
        content = _call_llm(prompt)
        parsed = json.loads(content)
        return _validate_enrichment(parsed)
    except Exception:
        logger.exception("Enrichment failed for provider '%s'", settings.LLM_PROVIDER)
        if raise_on_error:
            raise
        return _default_enrichment()


def _call_llm(prompt: str) -> str:
    if settings.LLM_PROVIDER == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not set")

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        if settings.OPENROUTER_SITE_URL:
            headers["HTTP-Referer"] = settings.OPENROUTER_SITE_URL
        if settings.OPENROUTER_APP_NAME:
            headers["X-Title"] = settings.OPENROUTER_APP_NAME

        response = _post_with_backoff(
            _openrouter_endpoint(),
            headers=headers,
            json={
                "model": settings.OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            },
            timeout=120.0,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "OpenRouter request failed: status=%s body=%s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        result = response.json()
        return result["choices"][0]["message"]["content"]

    chat_response = _post_with_backoff(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json={
            "model": settings.OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
        },
        timeout=120.0,
    )
    if chat_response.status_code == 404:
        _raise_ollama_model_error_if_needed(chat_response)
        logger.warning("Ollama /api/chat returned 404, trying /api/generate fallback")
        generate_response = _post_with_backoff(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=120.0,
        )
        if generate_response.status_code == 404:
            _raise_ollama_model_error_if_needed(generate_response)
        generate_response.raise_for_status()
        result = generate_response.json()
        return result["response"]

    chat_response.raise_for_status()
    result = chat_response.json()
    return result["message"]["content"]


def _openrouter_endpoint() -> str:
    base = settings.OPENROUTER_BASE_URL.rstrip("/")
    if base.endswith("/api/v1") or base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/api/v1/chat/completions"


def _post_with_backoff(url: str, **kwargs) -> httpx.Response:
    max_attempts = max(1, settings.LLM_ENRICH_MAX_RETRIES + 1)

    for attempt in range(max_attempts):
        _apply_rate_limit()
        try:
            response = httpx.post(url=url, **kwargs)
        except httpx.RequestError:
            if attempt == max_attempts - 1:
                raise

            delay = _retry_delay(status_code=None, attempt=attempt, retry_after=None)
            logger.warning(
                "LLM request failed (%s); retrying in %.2fs (%s/%s)",
                url,
                delay,
                attempt + 1,
                max_attempts,
            )
            time.sleep(delay)
            continue

        if _is_retryable_status(response.status_code):
            if attempt == max_attempts - 1:
                response.raise_for_status()

            retry_after = _parse_retry_after_seconds(response.headers.get("Retry-After"))
            delay = _retry_delay(
                status_code=response.status_code,
                attempt=attempt,
                retry_after=retry_after,
            )
            logger.warning(
                "LLM request got retryable status %s (%s); retrying in %.2fs (%s/%s)",
                response.status_code,
                url,
                delay,
                attempt + 1,
                max_attempts,
            )
            time.sleep(delay)
            continue

        return response

    raise RuntimeError("Retry loop exhausted without returning or raising")


def _apply_rate_limit() -> None:
    global _NEXT_ALLOWED_TS

    min_interval = max(0.0, settings.LLM_ENRICH_MIN_INTERVAL_SECONDS)
    if min_interval <= 0:
        return

    with _RATE_LIMIT_LOCK:
        now = time.monotonic()
        wait_seconds = _NEXT_ALLOWED_TS - now
        if wait_seconds > 0:
            time.sleep(wait_seconds)
            now = time.monotonic()
        _NEXT_ALLOWED_TS = now + min_interval


def _is_retryable_status(status_code: int) -> bool:
    return status_code in {408, 425, 429, 500, 502, 503, 504}


def _retry_delay(status_code: int | None, attempt: int, retry_after: int | None) -> float:
    max_delay = max(1.0, settings.LLM_ENRICH_RETRY_MAX_SECONDS)

    if status_code == 429 and retry_after is not None:
        return float(min(retry_after, max_delay))

    base = max(0.1, settings.LLM_ENRICH_RETRY_BASE_SECONDS)
    return float(min(base * (2 ** max(0, attempt)), max_delay))


def _parse_retry_after_seconds(raw_value: str | None) -> int | None:
    if not raw_value:
        return None

    value = raw_value.strip()
    if value.isdigit():
        return int(value)

    try:
        retry_at = parsedate_to_datetime(value)
    except Exception:
        return None

    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    seconds = int((retry_at - datetime.now(timezone.utc)).total_seconds())
    return max(0, seconds)


def _raise_ollama_model_error_if_needed(response: httpx.Response) -> None:
    try:
        payload = response.json()
    except Exception:
        return

    error_text = str(payload.get("error", "")).lower()
    model = settings.OLLAMA_MODEL
    if "model" in error_text and "not found" in error_text:
        raise RuntimeError(
            f"Ollama model '{model}' not found. Pull it first (e.g. `make pull-model` or "
            f"`docker compose exec ollama ollama pull {model}`)."
        )


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
