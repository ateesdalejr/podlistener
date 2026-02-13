import os
import logging
import uuid

import httpx

from app.worker.celery_app import celery
from app.database import SyncSessionLocal
from app.config import settings
from app.models import Episode, Keyword, Mention
from app.services.transcription_service import transcribe_audio
from app.services.detection_service import detect_keywords
from app.services.enrichment_service import enrich_mention

logger = logging.getLogger(__name__)


@celery.task(name="app.worker.tasks.process.process_episode", bind=True, max_retries=2)
def process_episode(self, episode_id: str):
    """Full pipeline: download → transcribe → detect → enrich."""
    with SyncSessionLocal() as db:
        episode = db.query(Episode).filter(Episode.id == episode_id).first()
        if not episode:
            logger.warning(f"Episode {episode_id} not found yet; retrying")
            self.retry(countdown=10, exc=ValueError(f"Episode {episode_id} not found"))
            return

        try:
            # Step 1: Download
            _update_status(db, episode, "downloading")
            audio_path = _download_audio(episode.audio_url, episode_id)

            # Step 2: Transcribe
            _update_status(db, episode, "transcribing")
            transcript = transcribe_audio(audio_path)
            episode.transcript_text = transcript
            db.commit()

            # Clean up audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)

            # Step 3: Detect keywords
            _update_status(db, episode, "analyzing")
            keywords = db.query(Keyword).all()
            if not keywords:
                _update_status(db, episode, "completed")
                return

            kw_dicts = [
                {"id": str(k.id), "phrase": k.phrase, "match_type": k.match_type}
                for k in keywords
            ]
            matches = detect_keywords(transcript, kw_dicts)

            if not matches:
                _update_status(db, episode, "completed")
                return

            # Step 4: Enrich each match with Ollama
            for match in matches:
                enrichment = enrich_mention(match.phrase, match.transcript_segment)

                mention = Mention(
                    episode_id=episode.id,
                    keyword_id=uuid.UUID(match.keyword_id),
                    matched_text=match.matched_text,
                    transcript_segment=match.transcript_segment,
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

            _update_status(db, episode, "completed")

        except Exception as exc:
            logger.exception(f"Processing failed for episode {episode_id}")
            episode.status = "failed"
            episode.error_message = str(exc)[:500]
            db.commit()
            self.retry(countdown=120, exc=exc)


def _update_status(db, episode, status):
    episode.status = status
    db.commit()


def _download_audio(audio_url: str, episode_id: str) -> str:
    """Stream download audio to disk."""
    os.makedirs(settings.AUDIO_DIR, exist_ok=True)
    audio_path = os.path.join(settings.AUDIO_DIR, f"{episode_id}.mp3")

    with httpx.stream("GET", audio_url, follow_redirects=True, timeout=300.0) as resp:
        resp.raise_for_status()
        with open(audio_path, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=8192):
                f.write(chunk)

    return audio_path
