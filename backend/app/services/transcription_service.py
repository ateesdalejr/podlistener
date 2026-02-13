import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio via local whisper server or cloud provider."""
    if settings.TRANSCRIPTION_PROVIDER == "cloud":
        url = f"{settings.CLOUD_TRANSCRIPTION_BASE_URL}/audio/transcriptions"
        headers = {}
        if settings.CLOUD_TRANSCRIPTION_API_KEY:
            headers["Authorization"] = f"Bearer {settings.CLOUD_TRANSCRIPTION_API_KEY}"
    else:
        url = f"{settings.WHISPER_API_URL}/v1/audio/transcriptions"
        headers = {}

    with open(audio_path, "rb") as f:
        response = httpx.post(
            url,
            headers=headers,
            files={"file": ("audio.mp3", f, "audio/mpeg")},
            data={"model": settings.TRANSCRIPTION_MODEL, "response_format": "text"},
            timeout=settings.TRANSCRIPTION_TIMEOUT_SECONDS,
        )

    response.raise_for_status()
    return response.text.strip()
