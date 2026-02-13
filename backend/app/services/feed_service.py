import logging
from datetime import datetime, timezone

import feedparser

logger = logging.getLogger(__name__)


def parse_feed(rss_url: str) -> dict:
    """Parse an RSS feed and return feed metadata + episodes."""
    feed = feedparser.parse(rss_url)

    if feed.bozo and not feed.entries:
        raise ValueError(f"Failed to parse feed: {feed.bozo_exception}")

    feed_info = {
        "title": feed.feed.get("title"),
        "image_url": None,
    }

    if hasattr(feed.feed, "image") and hasattr(feed.feed.image, "href"):
        feed_info["image_url"] = feed.feed.image.href

    episodes = []
    for entry in feed.entries:
        audio_url = None
        for link in entry.get("links", []):
            if link.get("type", "").startswith("audio/"):
                audio_url = link["href"]
                break
        if not audio_url:
            for enc in entry.get("enclosures", []):
                if enc.get("type", "").startswith("audio/"):
                    audio_url = enc["href"]
                    break

        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

        episodes.append({
            "guid": entry.get("id", entry.get("link", "")),
            "title": entry.get("title"),
            "audio_url": audio_url,
            "published_at": published,
        })

    return {"feed": feed_info, "episodes": episodes}
