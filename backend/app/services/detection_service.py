import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SEGMENT_RADIUS = 300  # chars of context around a match


@dataclass
class KeywordMatch:
    keyword_id: str
    phrase: str
    matched_text: str
    transcript_segment: str


def detect_keywords(transcript: str, keywords: list[dict]) -> list[KeywordMatch]:
    """Find keyword matches in transcript text.

    Args:
        transcript: Full transcript text
        keywords: List of dicts with id, phrase, match_type

    Returns:
        List of KeywordMatch objects with surrounding context
    """
    matches = []
    transcript_lower = transcript.lower()

    for kw in keywords:
        phrase = kw["phrase"]
        match_type = kw["match_type"]

        if match_type == "regex":
            try:
                pattern = re.compile(phrase, re.IGNORECASE)
            except re.error:
                logger.warning(f"Invalid regex pattern: {phrase}")
                continue
            for m in pattern.finditer(transcript):
                segment = _extract_segment(transcript, m.start(), m.end())
                matches.append(KeywordMatch(
                    keyword_id=kw["id"],
                    phrase=phrase,
                    matched_text=m.group(),
                    transcript_segment=segment,
                ))
        elif match_type == "exact_word":
            pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
            for m in pattern.finditer(transcript):
                segment = _extract_segment(transcript, m.start(), m.end())
                matches.append(KeywordMatch(
                    keyword_id=kw["id"],
                    phrase=phrase,
                    matched_text=m.group(),
                    transcript_segment=segment,
                ))
        else:  # contains
            start = 0
            phrase_lower = phrase.lower()
            while True:
                idx = transcript_lower.find(phrase_lower, start)
                if idx == -1:
                    break
                end = idx + len(phrase)
                segment = _extract_segment(transcript, idx, end)
                matches.append(KeywordMatch(
                    keyword_id=kw["id"],
                    phrase=phrase,
                    matched_text=transcript[idx:end],
                    transcript_segment=segment,
                ))
                start = end

    return matches


def _extract_segment(text: str, match_start: int, match_end: int) -> str:
    seg_start = max(0, match_start - SEGMENT_RADIUS)
    seg_end = min(len(text), match_end + SEGMENT_RADIUS)
    prefix = "..." if seg_start > 0 else ""
    suffix = "..." if seg_end < len(text) else ""
    return prefix + text[seg_start:seg_end] + suffix
