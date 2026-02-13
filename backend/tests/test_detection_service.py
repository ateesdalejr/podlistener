"""Tests for keyword detection service."""
from app.services.detection_service import detect_keywords, _extract_segment


SAMPLE_TRANSCRIPT = (
    "Welcome to the show. Today we're talking about Acme Corp and how "
    "they've changed the game. I've been using acme corp's platform for "
    "six months. Their competitor, BetaCo, is also interesting but Acme Corp "
    "really stands out. Let me tell you about my workflow improvements."
)


class TestDetectKeywordsContains:
    def test_finds_case_insensitive_match(self):
        keywords = [{"id": "1", "phrase": "Acme Corp", "match_type": "contains"}]
        matches = detect_keywords(SAMPLE_TRANSCRIPT, keywords)
        assert len(matches) == 3
        assert all(m.phrase == "Acme Corp" for m in matches)

    def test_no_match_returns_empty(self):
        keywords = [{"id": "1", "phrase": "Nonexistent", "match_type": "contains"}]
        matches = detect_keywords(SAMPLE_TRANSCRIPT, keywords)
        assert len(matches) == 0

    def test_multiple_keywords(self):
        keywords = [
            {"id": "1", "phrase": "Acme Corp", "match_type": "contains"},
            {"id": "2", "phrase": "BetaCo", "match_type": "contains"},
        ]
        matches = detect_keywords(SAMPLE_TRANSCRIPT, keywords)
        acme_matches = [m for m in matches if m.keyword_id == "1"]
        beta_matches = [m for m in matches if m.keyword_id == "2"]
        assert len(acme_matches) == 3
        assert len(beta_matches) == 1

    def test_matched_text_preserves_original_case(self):
        keywords = [{"id": "1", "phrase": "acme corp", "match_type": "contains"}]
        matches = detect_keywords(SAMPLE_TRANSCRIPT, keywords)
        original_cases = [m.matched_text for m in matches]
        assert "Acme Corp" in original_cases
        assert "acme corp" in original_cases


class TestDetectKeywordsExactWord:
    def test_exact_word_matches(self):
        text = "The game is changing in the gaming world"
        keywords = [{"id": "1", "phrase": "game", "match_type": "exact_word"}]
        matches = detect_keywords(text, keywords)
        assert len(matches) == 1
        assert matches[0].matched_text == "game"

    def test_exact_word_no_partial(self):
        text = "I was gaming all day"
        keywords = [{"id": "1", "phrase": "game", "match_type": "exact_word"}]
        matches = detect_keywords(text, keywords)
        assert len(matches) == 0


class TestDetectKeywordsRegex:
    def test_regex_pattern(self):
        text = "Contact us at support@acme.com or sales@acme.com"
        keywords = [{"id": "1", "phrase": r"\w+@acme\.com", "match_type": "regex"}]
        matches = detect_keywords(text, keywords)
        assert len(matches) == 2
        assert matches[0].matched_text == "support@acme.com"
        assert matches[1].matched_text == "sales@acme.com"

    def test_invalid_regex_skipped(self):
        keywords = [{"id": "1", "phrase": "[invalid", "match_type": "regex"}]
        matches = detect_keywords("some text", keywords)
        assert len(matches) == 0


class TestExtractSegment:
    def test_short_text_returns_full(self):
        text = "Hello world"
        segment = _extract_segment(text, 0, 5)
        assert segment == "Hello world"

    def test_long_text_adds_ellipsis(self):
        text = "a" * 1000
        segment = _extract_segment(text, 500, 505)
        assert segment.startswith("...")
        assert segment.endswith("...")

    def test_start_of_text_no_prefix_ellipsis(self):
        text = "a" * 1000
        segment = _extract_segment(text, 0, 5)
        assert not segment.startswith("...")
        assert segment.endswith("...")

    def test_segment_includes_match(self):
        text = "x" * 400 + "MATCH" + "y" * 400
        segment = _extract_segment(text, 400, 405)
        assert "MATCH" in segment
