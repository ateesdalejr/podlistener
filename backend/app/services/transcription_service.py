import logging
import httpx

from app.config import settings
from app.services.transcription_runtime_config import get_transcription_config_sync

logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio via local whisper server or runtime-configured external provider."""
    runtime_config = get_transcription_config_sync()
    provider = runtime_config["provider"]
    model = runtime_config["model"]

    if provider == "external":
        url = runtime_config["external_url"]
        headers = {}
        if runtime_config["external_api_key"]:
            headers["Authorization"] = f"Bearer {runtime_config['external_api_key']}"
    else:
        url = f"{settings.WHISPER_API_URL}/v1/audio/transcriptions"
        headers = {}

    logger.info("Transcribing audio via provider=%s url=%s model=%s", provider, url, model)

    with open(audio_path, "rb") as f:
        response = httpx.post(
            url,
            headers=headers,
            files={"file": ("audio.mp3", f, "audio/mpeg")},
            data={"model": model, "response_format": "text"},
            timeout=settings.TRANSCRIPTION_TIMEOUT_SECONDS,
        )

    response.raise_for_status()
    return response.text.strip()
