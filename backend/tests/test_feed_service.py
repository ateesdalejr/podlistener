"""Tests for feed parsing service."""
from unittest.mock import patch, MagicMock
from app.services.feed_service import parse_feed


MOCK_RSS_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Podcast</title>
    <image>
      <url>https://example.com/cover.jpg</url>
    </image>
    <item>
      <guid>ep-001</guid>
      <title>Episode One</title>
      <pubDate>Mon, 10 Feb 2026 10:00:00 GMT</pubDate>
      <enclosure url="https://example.com/ep1.mp3" type="audio/mpeg" length="1000000" />
    </item>
    <item>
      <guid>ep-002</guid>
      <title>Episode Two</title>
      <pubDate>Thu, 13 Feb 2026 10:00:00 GMT</pubDate>
      <enclosure url="https://example.com/ep2.mp3" type="audio/mpeg" length="2000000" />
    </item>
    <item>
      <guid>ep-003</guid>
      <title>Episode Three (no audio)</title>
      <pubDate>Thu, 13 Feb 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""


@patch("app.services.feed_service.feedparser.parse")
def test_parse_feed_extracts_metadata(mock_parse):
    import feedparser
    mock_parse.return_value = feedparser.parse(MOCK_RSS_CONTENT)

    result = parse_feed("https://example.com/feed.xml")

    assert result["feed"]["title"] == "Test Podcast"
    assert len(result["episodes"]) == 3


@patch("app.services.feed_service.feedparser.parse")
def test_parse_feed_extracts_audio_url(mock_parse):
    import feedparser
    mock_parse.return_value = feedparser.parse(MOCK_RSS_CONTENT)

    result = parse_feed("https://example.com/feed.xml")

    eps_with_audio = [e for e in result["episodes"] if e["audio_url"]]
    assert len(eps_with_audio) == 2
    assert eps_with_audio[0]["audio_url"] == "https://example.com/ep1.mp3"


@patch("app.services.feed_service.feedparser.parse")
def test_parse_feed_extracts_guids(mock_parse):
    import feedparser
    mock_parse.return_value = feedparser.parse(MOCK_RSS_CONTENT)

    result = parse_feed("https://example.com/feed.xml")

    guids = [e["guid"] for e in result["episodes"]]
    assert "ep-001" in guids
    assert "ep-002" in guids


@patch("app.services.feed_service.feedparser.parse")
def test_parse_feed_handles_published_date(mock_parse):
    import feedparser
    mock_parse.return_value = feedparser.parse(MOCK_RSS_CONTENT)

    result = parse_feed("https://example.com/feed.xml")

    ep1 = [e for e in result["episodes"] if e["guid"] == "ep-001"][0]
    assert ep1["published_at"] is not None
    assert ep1["published_at"].year == 2026


@patch("app.services.feed_service.feedparser.parse")
def test_parse_feed_bozo_with_no_entries_raises(mock_parse):
    mock_result = MagicMock()
    mock_result.bozo = True
    mock_result.entries = []
    mock_result.bozo_exception = Exception("bad xml")
    mock_parse.return_value = mock_result

    try:
        parse_feed("https://bad-url.com/feed.xml")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Failed to parse feed" in str(e)
