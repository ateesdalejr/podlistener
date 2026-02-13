import os
import logging
import uuid
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx
from celery import chain

from app.worker.celery_app import celery
from app.database import SyncSessionLocal
from app.config import settings
from app.models import Episode, Keyword, Mention
from app.services.transcription_service import transcribe_audio
from app.services.detection_service import detect_keywords
from app.services.enrichment_service import enrich_mention

logger = logging.getLogger(__name__)


@celery.task(
    name="app.worker.tasks.process.process_episode",
    bind=True,
    max_retries=0,
)
def process_episode(self, episode_id: str):
    """Orchestrate the processing chain for one episode."""
    logger.info("Episode %s: queueing processing chain", episode_id)
    chain(
        download_episode_audio.s(episode_id),
        transcribe_episode_audio.s(),
        detect_episode_keywords.s(),
    ).delay()


@celery.task(
    name="app.worker.tasks.process.download_episode_audio",
    bind=True,
    max_retries=2,
    soft_time_limit=settings.PROCESS_EPISODE_SOFT_TIME_LIMIT_SECONDS,
    time_limit=settings.PROCESS_EPISODE_TIME_LIMIT_SECONDS,
)
def download_episode_audio(self, episode_id: str):
    """Download episode audio to disk and hand off to pipeline task."""
    with SyncSessionLocal() as db:
        episode = db.query(Episode).filter(Episode.id == episode_id).first()
        if not episode:
            logger.warning(f"Episode {episode_id} not found yet; retrying")
            self.retry(countdown=10, exc=ValueError(f"Episode {episode_id} not found"))
            return

        try:
            logger.info("Episode %s: starting download", episode_id)
            _update_status(db, episode, "downloading")
            _download_audio(episode.audio_url, episode_id)
            logger.info("Episode %s: download completed", episode_id)
            return episode_id

        except Exception as exc:
            logger.exception("Audio download failed for episode %s", episode_id)
            _mark_episode_failed(db, episode, exc)
            self.retry(countdown=120, exc=exc)


@celery.task(
    name="app.worker.tasks.process.transcribe_episode_audio",
    bind=True,
    max_retries=2,
    rate_limit=settings.TRANSCRIPTION_TASK_RATE_LIMIT,
    soft_time_limit=settings.PROCESS_EPISODE_SOFT_TIME_LIMIT_SECONDS,
    time_limit=settings.PROCESS_EPISODE_TIME_LIMIT_SECONDS,
)
def transcribe_episode_audio(self, episode_id: str):
    """Transcribe previously downloaded audio and persist transcript."""
    with SyncSessionLocal() as db:
        episode = db.query(Episode).filter(Episode.id == episode_id).first()
        if not episode:
            logger.warning("Episode %s not found yet; retrying", episode_id)
            self.retry(countdown=10, exc=ValueError(f"Episode {episode_id} not found"))
            return

        audio_path = _audio_path(episode_id)
        if not os.path.exists(audio_path):
            logger.warning("Episode %s audio file missing; retrying", episode_id)
            self.retry(countdown=30, exc=FileNotFoundError(audio_path))
            return

        try:
            logger.info("Episode %s: starting transcription", episode_id)
            _update_status(db, episode, "transcribing")
            transcript = transcribe_audio(audio_path)
            episode.transcript_text = transcript
            db.commit()
            logger.info("Episode %s: transcription complete", episode_id)
            return {"episode_id": episode_id, "transcription_done": True}

        except Exception as exc:
            countdown = _transcription_retry_countdown(exc, self.request.retries)
            retries_used = int(self.request.retries or 0)
            max_retries = int(self.max_retries or 0)
            if retries_used >= max_retries:
                logger.exception("Transcription failed for episode %s (retries exhausted)", episode_id)
                _mark_episode_failed(db, episode, exc)
                raise

            logger.warning(
                "Transcription failed for episode %s; retrying in %ss (attempt %s/%s)",
                episode_id,
                countdown,
                retries_used + 1,
                max_retries,
                exc_info=exc,
            )
            self.retry(countdown=countdown, exc=exc)


@celery.task(
    name="app.worker.tasks.process.detect_episode_keywords",
    bind=True,
    max_retries=2,
    soft_time_limit=settings.PROCESS_EPISODE_SOFT_TIME_LIMIT_SECONDS,
    time_limit=settings.PROCESS_EPISODE_TIME_LIMIT_SECONDS,
)
def detect_episode_keywords(self, transcription_result):
    """Detect keyword matches from an episode transcript."""
    # Backward-compatible input handling:
    # - New chain handoff: {"episode_id": "...", "transcription_done": True}
    # - Legacy/direct call: "episode_id"
    if isinstance(transcription_result, dict):
        episode_id = transcription_result.get("episode_id")
        transcription_done = bool(transcription_result.get("transcription_done"))
        if not transcription_done:
            logger.warning("Episode %s transcription not marked done; retrying", episode_id)
            self.retry(countdown=10, exc=ValueError("Transcription not complete"))
            return
    else:
        episode_id = transcription_result

    with SyncSessionLocal() as db:
        episode = db.query(Episode).filter(Episode.id == episode_id).first()
        if not episode:
            logger.warning("Episode %s not found yet; retrying", episode_id)
            self.retry(countdown=10, exc=ValueError(f"Episode {episode_id} not found"))
            return
        # Empty string is a valid transcript result; None means it is not persisted yet.
        if episode.transcript_text is None:
            logger.warning("Episode %s transcript missing; retrying", episode_id)
            self.retry(countdown=30, exc=ValueError(f"Episode {episode_id} transcript missing"))
            return

        try:
            logger.info("Episode %s: starting keyword detection", episode_id)
            _update_status(db, episode, "analyzing")
            keywords = db.query(Keyword).all()
            if not keywords:
                _update_status(db, episode, "completed")
                logger.info("Episode %s: completed (no keywords)", episode_id)
                return {"episode_id": episode_id, "matches": []}

            kw_dicts = [
                {"id": str(k.id), "phrase": k.phrase, "match_type": k.match_type}
                for k in keywords
            ]
            matches = detect_keywords(episode.transcript_text, kw_dicts)
            logger.info("Episode %s: found %s matches", episode_id, len(matches))
            detection_payload = {
                "episode_id": episode_id,
                "matches": [
                    {
                        "keyword_id": match.keyword_id,
                        "phrase": match.phrase,
                        "matched_text": match.matched_text,
                        "transcript_segment": match.transcript_segment,
                    }
                    for match in matches
                ],
            }
            # Queue enrichment explicitly so direct/manual keyword detection runs
            # still trigger LLM processing and mention persistence.
            enrich_episode_mentions.apply_async(args=[detection_payload], queue="llm")
            return detection_payload

        except Exception as exc:
            logger.exception("Keyword detection failed for episode %s", episode_id)
            _mark_episode_failed(db, episode, exc)
            self.retry(countdown=120, exc=exc)


@celery.task(
    name="app.worker.tasks.process.enrich_episode_mentions",
    bind=True,
    max_retries=2,
    soft_time_limit=settings.PROCESS_EPISODE_SOFT_TIME_LIMIT_SECONDS,
    time_limit=settings.PROCESS_EPISODE_TIME_LIMIT_SECONDS,
)
def enrich_episode_mentions(self, detection_result: dict):
    """Enrich detected matches and persist mentions."""
    episode_id = detection_result["episode_id"]
    matches = detection_result.get("matches", [])
    start_index = int(detection_result.get("start_index", 0))
    audio_path = _audio_path(episode_id)

    with SyncSessionLocal() as db:
        episode = db.query(Episode).filter(Episode.id == episode_id).first()
        if not episode:
            logger.warning("Episode %s not found yet; retrying", episode_id)
            self.retry(countdown=10, exc=ValueError(f"Episode {episode_id} not found"))
            return

        try:
            if not matches:
                _update_status(db, episode, "completed")
                logger.info("Episode %s: completed (no matches)", episode_id)
                return

            start_index = max(0, min(start_index, len(matches)))
            logger.info(
                "Episode %s: enriching %s matches (starting at index %s)",
                episode_id,
                len(matches),
                start_index,
            )
            next_index = start_index
            if start_index == 0:
                db.query(Mention).filter(Mention.episode_id == episode.id).delete(synchronize_session=False)
                db.commit()

            while next_index < len(matches):
                match = matches[next_index]
                keyword_id = uuid.UUID(match["keyword_id"])

                existing = (
                    db.query(Mention)
                    .filter(
                        Mention.episode_id == episode.id,
                        Mention.keyword_id == keyword_id,
                        Mention.matched_text == match["matched_text"],
                        Mention.transcript_segment == match["transcript_segment"],
                    )
                    .first()
                )
                if existing:
                    next_index += 1
                    continue

                enrichment = enrich_mention(
                    match["phrase"],
                    match["transcript_segment"],
                    raise_on_error=True,
                )
                mention = Mention(
                    episode_id=episode.id,
                    keyword_id=keyword_id,
                    matched_text=match["matched_text"],
                    transcript_segment=match["transcript_segment"],
                    sentiment=enrichment["sentiment"],
                    sentiment_score=enrichment["sentiment_score"],
                    context_summary=enrichment["context_summary"],
                    topics=enrichment["topics"],
                    is_buying_signal=enrichment["is_buying_signal"],
                    is_pain_point=enrichment["is_pain_point"],
                    is_recommendation=enrichment["is_recommendation"],
                    raw_llm_response=enrichment,
                )
                db.add(mention)
                db.commit()
                next_index += 1

            _update_status(db, episode, "completed")
            logger.info("Episode %s: completed", episode_id)

        except Exception as exc:
            db.rollback()
            retries_used = int(self.request.retries or 0)
            max_retries = int(self.max_retries or 0)
            retry_payload = _enrichment_retry_payload(detection_result, next_index)
            if retries_used >= max_retries:
                logger.exception("Enrichment failed for episode %s (retries exhausted)", episode_id)
                _mark_episode_failed(db, episode, exc)
                raise

            logger.warning(
                "Enrichment failed for episode %s; retrying in %ss from match index %s (attempt %s/%s)",
                episode_id,
                120,
                retry_payload.get("start_index", 0),
                retries_used + 1,
                max_retries,
                exc_info=exc,
            )
            self.retry(countdown=120, args=[retry_payload], exc=exc)
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)


def _update_status(db, episode, status):
    episode.status = status
    db.commit()


def _mark_episode_failed(db, episode, exc: Exception):
    episode.status = "failed"
    episode.error_message = str(exc)[:500]
    db.commit()


def _audio_path(episode_id: str) -> str:
    return os.path.join(settings.AUDIO_DIR, f"{episode_id}.mp3")


def _enrichment_retry_payload(detection_result: dict, start_index: int) -> dict:
    payload = dict(detection_result)
    payload["start_index"] = max(0, int(start_index))
    return payload


def _download_audio(audio_url: str, episode_id: str) -> str:
    """Stream download audio to disk."""
    os.makedirs(settings.AUDIO_DIR, exist_ok=True)
    audio_path = _audio_path(episode_id)
    started_at = time.monotonic()
    bytes_written = 0

    timeout = httpx.Timeout(connect=20.0, read=30.0, write=30.0, pool=20.0)
    with httpx.stream("GET", audio_url, follow_redirects=True, timeout=timeout) as resp:
        resp.raise_for_status()
        with open(audio_path, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=8192):
                f.write(chunk)
                bytes_written += len(chunk)
                if bytes_written > settings.AUDIO_DOWNLOAD_MAX_BYTES:
                    raise RuntimeError(
                        f"Audio exceeds max size ({settings.AUDIO_DOWNLOAD_MAX_BYTES} bytes)"
                    )
                if time.monotonic() - started_at > settings.AUDIO_DOWNLOAD_TIMEOUT_SECONDS:
                    raise RuntimeError(
                        f"Audio download exceeded {settings.AUDIO_DOWNLOAD_TIMEOUT_SECONDS} seconds"
                    )

    return audio_path


def _transcription_retry_countdown(exc: Exception, retries_used: int) -> int:
    """Compute retry delay with 429-aware exponential backoff."""
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        if exc.response.status_code == 429:
            retry_after = _parse_retry_after_seconds(exc.response.headers.get("Retry-After"))
            if retry_after is not None:
                return max(30, min(retry_after, settings.TRANSCRIPTION_429_RETRY_MAX_SECONDS))

            base = max(30, settings.TRANSCRIPTION_429_RETRY_BASE_SECONDS)
            countdown = base * (2 ** max(0, retries_used))
            return min(countdown, settings.TRANSCRIPTION_429_RETRY_MAX_SECONDS)

    return 120


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
