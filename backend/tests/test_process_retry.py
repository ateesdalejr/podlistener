import httpx

from app.worker.tasks.process import _parse_retry_after_seconds, _transcription_retry_countdown


def _make_429_error(retry_after: str | None = None) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://example.com/v1/audio/transcriptions")
    headers = {}
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    response = httpx.Response(429, headers=headers, request=request)
    return httpx.HTTPStatusError("rate limited", request=request, response=response)


def test_parse_retry_after_seconds_delta_seconds():
    assert _parse_retry_after_seconds("120") == 120


def test_transcription_retry_countdown_uses_retry_after_header():
    err = _make_429_error("75")
    countdown = _transcription_retry_countdown(err, retries_used=0)
    assert countdown == 75


def test_transcription_retry_countdown_exponential_when_no_header(monkeypatch):
    monkeypatch.setattr("app.worker.tasks.process.settings.TRANSCRIPTION_429_RETRY_BASE_SECONDS", 30)
    monkeypatch.setattr("app.worker.tasks.process.settings.TRANSCRIPTION_429_RETRY_MAX_SECONDS", 300)
    err = _make_429_error()
    assert _transcription_retry_countdown(err, retries_used=0) == 30
    assert _transcription_retry_countdown(err, retries_used=1) == 60
    assert _transcription_retry_countdown(err, retries_used=10) == 300
