import logging
from datetime import datetime, timezone

from app.worker.celery_app import celery
from app.database import SyncSessionLocal
from app.config import settings
from app.models import Feed, Episode
from app.services.feed_service import parse_feed

logger = logging.getLogger(__name__)


@celery.task(name="app.worker.tasks.poll.poll_all_feeds")
def poll_all_feeds():
    """Fan out polling to individual feed tasks."""
    with SyncSessionLocal() as db:
        feeds = db.query(Feed).all()
        for feed in feeds:
            poll_single_feed.delay(str(feed.id))
        logger.info(f"Queued polling for {len(feeds)} feeds")


@celery.task(name="app.worker.tasks.poll.poll_single_feed", bind=True, max_retries=3)
def poll_single_feed(self, feed_id: str):
    """Parse RSS feed and create episodes for new entries."""
    from app.worker.tasks.process import process_episode

    with SyncSessionLocal() as db:
        feed = db.query(Feed).filter(Feed.id == feed_id).first()
        if not feed:
            logger.warning(f"Feed {feed_id} not found")
            return

        try:
            data = parse_feed(feed.rss_url)
        except Exception as exc:
            logger.error(f"Failed to parse feed {feed.rss_url}: {exc}")
            self.retry(countdown=60, exc=exc)
            return

        if data["feed"]["title"] and not feed.title:
            feed.title = data["feed"]["title"]
        if data["feed"]["image_url"] and not feed.image_url:
            feed.image_url = data["feed"]["image_url"]

        episodes = data["episodes"]

        new_count = 0
        for ep_data in episodes:
            existing = db.query(Episode).filter(Episode.guid == ep_data["guid"]).first()
            if existing:
                continue

            if not ep_data["audio_url"]:
                continue

            episode = Episode(
                feed_id=feed.id,
                guid=ep_data["guid"],
                title=ep_data["title"],
                audio_url=ep_data["audio_url"],
                published_at=ep_data["published_at"],
                status="pending",
            )
            db.add(episode)
            new_count += 1

        feed.last_polled_at = datetime.now(timezone.utc)
        db.commit()

        max_episodes = settings.MAX_EPISODES_PER_FEED
        if max_episodes > 0:
            recent_episodes = (
                db.query(Episode)
                .filter(Episode.feed_id == feed.id)
                .order_by(Episode.published_at.desc().nullslast(), Episode.created_at.desc())
                .limit(max_episodes)
                .all()
            )
        else:
            recent_episodes = (
                db.query(Episode)
                .filter(Episode.feed_id == feed.id)
                .order_by(Episode.published_at.desc().nullslast(), Episode.created_at.desc())
                .all()
            )

        queued_episode_ids: list[str] = []
        for episode in recent_episodes:
            if episode.status != "pending":
                continue
            episode.status = "queued"
            queued_episode_ids.append(str(episode.id))

        if queued_episode_ids:
            db.commit()

        for episode_id in queued_episode_ids:
            process_episode.delay(episode_id)
        queued_count = len(queued_episode_ids)

        logger.info(
            "Feed '%s': %s new episodes, queued %s for processing",
            feed.title,
            new_count,
            queued_count,
        )
