"""Tests for LLM enrichment service."""
import json
from unittest.mock import patch, MagicMock

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
