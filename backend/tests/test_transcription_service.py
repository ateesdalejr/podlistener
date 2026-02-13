from pathlib import Path

import httpx

from app.services.transcription_service import transcribe_audio


class _FakeResponse:
    def __init__(self, text: str = "ok"):
        self.text = text

    def raise_for_status(self):
        return None


def test_transcribe_audio_external_direct_upload(monkeypatch, tmp_path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"x" * 1024)

    monkeypatch.setattr(
        "app.services.transcription_service.get_transcription_config_sync",
        lambda: {
            "provider": "external",
            "external_url": "https://example.com/v1/audio/transcriptions",
            "external_api_key": "token",
            "model": "gpt-4o-mini-transcribe",
        },
    )
    monkeypatch.setattr("app.services.transcription_service.httpx.post", lambda *args, **kwargs: _FakeResponse("hello"))

    transcript = transcribe_audio(str(audio_path))
    assert transcript == "hello"


def test_transcribe_audio_external_large_file_chunked(monkeypatch, tmp_path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"x" * 1024)

    monkeypatch.setattr(
        "app.services.transcription_service.get_transcription_config_sync",
        lambda: {
            "provider": "external",
            "external_url": "https://example.com/v1/audio/transcriptions",
            "external_api_key": "",
            "model": "gpt-4o-mini-transcribe",
        },
    )
    monkeypatch.setattr("app.services.transcription_service.settings.TRANSCRIPTION_EXTERNAL_MAX_UPLOAD_BYTES", 100)
    monkeypatch.setattr("app.services.transcription_service.settings.TRANSCRIPTION_EXTERNAL_CHUNK_SECONDS", 60)
    monkeypatch.setattr("app.services.transcription_service.settings.TRANSCRIPTION_EXTERNAL_CHUNK_BITRATE_KBPS", 32)

    def _fake_ffmpeg_run(cmd, check, capture_output, text):
        pattern = Path(cmd[-1])
        pattern.parent.mkdir(parents=True, exist_ok=True)
        (pattern.parent / "chunk_0000.mp3").write_bytes(b"a" * 50)
        (pattern.parent / "chunk_0001.mp3").write_bytes(b"b" * 50)
        return None

    monkeypatch.setattr("app.services.transcription_service.subprocess.run", _fake_ffmpeg_run)

    responses = iter([_FakeResponse("first"), _FakeResponse("second")])
    monkeypatch.setattr("app.services.transcription_service.httpx.post", lambda *args, **kwargs: next(responses))

    transcript = transcribe_audio(str(audio_path))
    assert transcript == "first\nsecond"


def test_transcribe_audio_external_413_raises_runtime_error(monkeypatch, tmp_path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"x" * 1024)

    monkeypatch.setattr(
        "app.services.transcription_service.get_transcription_config_sync",
        lambda: {
            "provider": "external",
            "external_url": "https://example.com/v1/audio/transcriptions",
            "external_api_key": "",
            "model": "gpt-4o-mini-transcribe",
        },
    )

    request = httpx.Request("POST", "https://example.com/v1/audio/transcriptions")
    response = httpx.Response(413, request=request)

    class _ErrorResponse:
        text = ""

        def raise_for_status(self):
            raise httpx.HTTPStatusError("too large", request=request, response=response)

    monkeypatch.setattr("app.services.transcription_service.httpx.post", lambda *args, **kwargs: _ErrorResponse())

    try:
        transcribe_audio(str(audio_path))
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "too large" in str(exc).lower()
