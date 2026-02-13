import logging
import os
import glob
import subprocess
import tempfile

import httpx

from app.config import settings
from app.services.transcription_runtime_config import get_transcription_config_sync

logger = logging.getLogger(__name__)

def _format_mb(num_bytes: int) -> str:
    return f"{num_bytes / (1024 * 1024):.1f}MB"


def _submit_transcription_request(url: str, headers: dict[str, str], model: str, audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        response = httpx.post(
            url,
            headers=headers,
            files={"file": (os.path.basename(audio_path), f, "audio/mpeg")},
            data={"model": model, "response_format": "text"},
            timeout=settings.TRANSCRIPTION_TIMEOUT_SECONDS,
        )
    response.raise_for_status()
    return response.text.strip()


def _split_audio_into_chunks(
    *,
    audio_path: str,
    chunk_seconds: int,
    bitrate_kbps: int,
    max_upload_bytes: int,
) -> tuple[tempfile.TemporaryDirectory[str], list[str]]:
    tmpdir = tempfile.TemporaryDirectory(prefix="transcription_chunks_")
    output_pattern = os.path.join(tmpdir.name, "chunk_%04d.mp3")
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        audio_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-b:a",
        f"{bitrate_kbps}k",
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-reset_timestamps",
        "1",
        output_pattern,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        tmpdir.cleanup()
        raise RuntimeError(
            "ffmpeg is required for chunked external transcription but is not installed."
        ) from exc
    except subprocess.CalledProcessError as exc:
        tmpdir.cleanup()
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(f"Failed to chunk audio for transcription: {stderr or str(exc)}") from exc

    chunk_paths = sorted(glob.glob(os.path.join(tmpdir.name, "chunk_*.mp3")))
    if not chunk_paths:
        tmpdir.cleanup()
        raise RuntimeError("Failed to chunk audio for transcription: no chunks were generated.")

    for chunk_path in chunk_paths:
        chunk_size = os.path.getsize(chunk_path)
        if chunk_size > max_upload_bytes:
            tmpdir.cleanup()
            raise RuntimeError(
                f"Chunk {os.path.basename(chunk_path)} is too large for external transcription: "
                f"{_format_mb(chunk_size)} (max {_format_mb(max_upload_bytes)}). "
                "Reduce chunk seconds or bitrate."
            )

    return tmpdir, chunk_paths


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

    file_size = os.path.getsize(audio_path)
    external_upload_max_bytes = settings.TRANSCRIPTION_EXTERNAL_MAX_UPLOAD_BYTES

    logger.info("Transcribing audio via provider=%s url=%s model=%s", provider, url, model)

    try:
        if provider == "external" and file_size > external_upload_max_bytes:
            logger.info(
                "Audio exceeds external upload max (%s > %s); chunking for transcription",
                _format_mb(file_size),
                _format_mb(external_upload_max_bytes),
            )
            chunk_seconds = max(60, settings.TRANSCRIPTION_EXTERNAL_CHUNK_SECONDS)
            bitrate_kbps = max(16, settings.TRANSCRIPTION_EXTERNAL_CHUNK_BITRATE_KBPS)
            tmpdir, chunk_paths = _split_audio_into_chunks(
                audio_path=audio_path,
                chunk_seconds=chunk_seconds,
                bitrate_kbps=bitrate_kbps,
                max_upload_bytes=external_upload_max_bytes,
            )
            try:
                chunk_texts = []
                for index, chunk_path in enumerate(chunk_paths, start=1):
                    logger.info(
                        "Transcribing chunk %s/%s (%s)",
                        index,
                        len(chunk_paths),
                        _format_mb(os.path.getsize(chunk_path)),
                    )
                    chunk_text = _submit_transcription_request(url, headers, model, chunk_path)
                    if chunk_text:
                        chunk_texts.append(chunk_text)
            finally:
                tmpdir.cleanup()
            return "\n".join(chunk_texts).strip()

        return _submit_transcription_request(url, headers, model, audio_path)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 413:
            raise RuntimeError(
                f"Transcription upload rejected as too large: {_format_mb(file_size)} "
                f"(configured max {_format_mb(external_upload_max_bytes)} for external uploads)."
            ) from exc
        raise
