"""Tests for LLM enrichment service."""
import json
from unittest.mock import patch, MagicMock

from app.services import enrichment_service
from app.services.enrichment_service import enrich_mention, _validate_enrichment, _default_enrichment


class TestValidateEnrichment:
    def test_valid_response(self):
        data = {
            "sentiment": "positive",
            "sentiment_score": 0.85,
            "context_summary": "Great product",
            "topics": ["SaaS", "tools"],
            "is_buying_signal": False,
            "is_pain_point": False,
            "is_recommendation": True,
        }
        result = _validate_enrichment(data)
        assert result["sentiment"] == "positive"
        assert result["sentiment_score"] == 0.85
        assert result["is_recommendation"] is True
        assert result["topics"] == ["SaaS", "tools"]

    def test_missing_fields_get_defaults(self):
        result = _validate_enrichment({})
        assert result["sentiment"] == "neutral"
        assert result["sentiment_score"] == 0.5
        assert result["context_summary"] == ""
        assert result["topics"] == []
        assert result["is_buying_signal"] is False

    def test_type_coercion(self):
        data = {
            "sentiment": 123,
            "sentiment_score": "0.7",
            "is_buying_signal": 1,
        }
        result = _validate_enrichment(data)
        assert result["sentiment"] == "123"
        assert result["sentiment_score"] == 0.7
        assert result["is_buying_signal"] is True


class TestDefaultEnrichment:
    def test_returns_neutral_defaults(self):
        result = _default_enrichment()
        assert result["sentiment"] == "neutral"
        assert result["sentiment_score"] == 0.5
        assert result["is_buying_signal"] is False
        assert result["is_pain_point"] is False
        assert result["is_recommendation"] is False


class TestEnrichMention:
    def setup_method(self):
        enrichment_service._NEXT_ALLOWED_TS = 0.0

    @patch("app.services.enrichment_service.httpx.post")
    def test_successful_enrichment(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": json.dumps({
                    "sentiment": "positive",
                    "sentiment_score": 0.9,
                    "context_summary": "Endorsement of the product",
                    "topics": ["software"],
                    "is_buying_signal": False,
                    "is_pain_point": False,
                    "is_recommendation": True,
                })
            }
        }
        mock_post.return_value = mock_response

        result = enrich_mention("Acme Corp", "I love Acme Corp's product")
        assert result["sentiment"] == "positive"
        assert result["is_recommendation"] is True

    @patch("app.services.enrichment_service.httpx.post")
    def test_failed_enrichment_returns_default(self, mock_post):
        mock_post.side_effect = Exception("Connection refused")

        result = enrich_mention("Acme Corp", "some text")
        assert result["sentiment"] == "neutral"
        assert result["context_summary"] == "Enrichment unavailable"

    @patch("app.services.enrichment_service.httpx.post")
    def test_failed_enrichment_raises_in_strict_mode(self, mock_post):
        mock_post.side_effect = Exception("Connection refused")

        import pytest

        with pytest.raises(Exception, match="Connection refused"):
            enrich_mention("Acme Corp", "some text", raise_on_error=True)

    @patch("app.services.enrichment_service.httpx.post")
    def test_invalid_json_returns_default(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "not valid json at all"}
        }
        mock_post.return_value = mock_response

        result = enrich_mention("Acme Corp", "some text")
        assert result["sentiment"] == "neutral"

    @patch("app.services.enrichment_service.httpx.post")
    def test_openrouter_enrichment(self, mock_post):
        from app.config import settings

        old_provider = settings.LLM_PROVIDER
        old_key = settings.OPENROUTER_API_KEY
        try:
            settings.LLM_PROVIDER = "openrouter"
            settings.OPENROUTER_API_KEY = "test-key"

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "sentiment": "negative",
                            "sentiment_score": 0.2,
                            "context_summary": "Complaint about pricing",
                            "topics": ["pricing"],
                            "is_buying_signal": False,
                            "is_pain_point": True,
                            "is_recommendation": False,
                        })
                    }
                }]
            }
            mock_post.return_value = mock_response

            result = enrich_mention("Acme Corp", "This is too expensive")
            assert result["sentiment"] == "negative"
            assert result["is_pain_point"] is True
        finally:
            settings.LLM_PROVIDER = old_provider
            settings.OPENROUTER_API_KEY = old_key

    @patch("app.services.enrichment_service.httpx.post")
    def test_openrouter_base_url_variants(self, mock_post):
        from app.config import settings

        old_provider = settings.LLM_PROVIDER
        old_key = settings.OPENROUTER_API_KEY
        old_base = settings.OPENROUTER_BASE_URL
        try:
            settings.LLM_PROVIDER = "openrouter"
            settings.OPENROUTER_API_KEY = "test-key"

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": json.dumps({"sentiment": "neutral"})}}]
            }
            mock_post.return_value = mock_response

            settings.OPENROUTER_BASE_URL = "https://openrouter.ai"
            enrich_mention("Acme Corp", "ok")
            url_1 = mock_post.call_args.kwargs["url"]
            assert url_1.endswith("/api/v1/chat/completions")

            settings.OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
            enrich_mention("Acme Corp", "ok")
            url_2 = mock_post.call_args.kwargs["url"]
            assert url_2.endswith("/api/v1/chat/completions")

            settings.OPENROUTER_BASE_URL = "https://openrouter.ai/v1"
            enrich_mention("Acme Corp", "ok")
            url_3 = mock_post.call_args.kwargs["url"]
            assert url_3.endswith("/v1/chat/completions")
        finally:
            settings.LLM_PROVIDER = old_provider
            settings.OPENROUTER_API_KEY = old_key
            settings.OPENROUTER_BASE_URL = old_base

    @patch("app.services.enrichment_service.time.sleep")
    @patch("app.services.enrichment_service.httpx.post")
    def test_retries_429_then_succeeds(self, mock_post, mock_sleep):
        from app.config import settings

        old_retries = settings.LLM_ENRICH_MAX_RETRIES
        old_base = settings.LLM_ENRICH_RETRY_BASE_SECONDS
        old_max = settings.LLM_ENRICH_RETRY_MAX_SECONDS
        try:
            settings.LLM_ENRICH_MAX_RETRIES = 1
            settings.LLM_ENRICH_RETRY_BASE_SECONDS = 1
            settings.LLM_ENRICH_RETRY_MAX_SECONDS = 30

            response_429 = MagicMock()
            response_429.status_code = 429
            response_429.headers = {"Retry-After": "2"}

            response_200 = MagicMock()
            response_200.status_code = 200
            response_200.headers = {}
            response_200.json.return_value = {
                "message": {"content": json.dumps({"sentiment": "neutral"})}
            }

            mock_post.side_effect = [response_429, response_200]

            result = enrich_mention("Acme Corp", "some text")
            assert result["sentiment"] == "neutral"
            assert mock_post.call_count == 2
            mock_sleep.assert_called_once_with(2.0)
        finally:
            settings.LLM_ENRICH_MAX_RETRIES = old_retries
            settings.LLM_ENRICH_RETRY_BASE_SECONDS = old_base
            settings.LLM_ENRICH_RETRY_MAX_SECONDS = old_max

    @patch("app.services.enrichment_service.time.sleep")
    @patch("app.services.enrichment_service.time.monotonic")
    @patch("app.services.enrichment_service.httpx.post")
    def test_rate_limit_applies_between_chat_and_fallback(self, mock_post, mock_monotonic, mock_sleep):
        from app.config import settings

        old_min_interval = settings.LLM_ENRICH_MIN_INTERVAL_SECONDS
        try:
            settings.LLM_ENRICH_MIN_INTERVAL_SECONDS = 0.25

            response_404 = MagicMock()
            response_404.status_code = 404
            response_404.headers = {}
            response_404.json.return_value = {"error": "not found"}

            response_200 = MagicMock()
            response_200.status_code = 200
            response_200.headers = {}
            response_200.json.return_value = {
                "response": json.dumps({"sentiment": "neutral"})
            }

            mock_post.side_effect = [response_404, response_200]
            mock_monotonic.side_effect = [100.0, 100.1, 100.25]

            result = enrich_mention("Acme Corp", "some text")
            assert result["sentiment"] == "neutral"
            assert mock_post.call_count == 2
            assert mock_sleep.call_count == 1
            waited = mock_sleep.call_args.args[0]
            assert abs(waited - 0.15) < 1e-6
        finally:
            settings.LLM_ENRICH_MIN_INTERVAL_SECONDS = old_min_interval
