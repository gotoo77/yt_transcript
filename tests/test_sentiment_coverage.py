"""Focused branch coverage for sentiment, emotions and readability."""

import pytest

from yt_transcript import sentiment_analyzer
from yt_transcript.sentiment_analyzer import (
    analyze_sentiment,
    calculate_readability_metrics,
    detect_emotions,
    estimate_syllables,
    get_comprehensive_analysis,
)


def test_sentiment_backend_failure_returns_none(monkeypatch):
    class BrokenBlob:
        def __init__(self, text):
            raise RuntimeError("simulated TextBlob failure")

    monkeypatch.setattr(sentiment_analyzer, "TextBlob", BrokenBlob)
    assert analyze_sentiment("A sufficiently long sentence.") is None


def test_emotion_detection_without_keywords_has_no_dominant_emotion():
    result = detect_emotions("ordinary words without emotional vocabulary")
    assert result is not None
    assert result["emotions"] == {}
    assert result["dominant_emotion"] is None
    assert result["total_emotion_words"] == 0
    assert result["emotional_intensity"] == 0


def test_emotion_detection_failure_returns_none(monkeypatch):
    class BrokenText(str):
        def lower(self):
            raise RuntimeError("simulated lower failure")

    assert detect_emotions(BrokenText("text")) is None


@pytest.mark.parametrize(
    ("syllables", "expected_level"),
    [
        (1, "Très facile"),
        (13, "Facile"),
        (14, "Assez facile"),
        (15, "Standard"),
        (17, "Assez difficile"),
        (18, "Difficile"),
        (20, "Très difficile"),
    ],
)
def test_readability_level_boundaries(monkeypatch, syllables, expected_level):
    monkeypatch.setattr(
        sentiment_analyzer,
        "extract_words",
        lambda text: ["robot"] * 10,
    )
    monkeypatch.setattr(
        sentiment_analyzer,
        "estimate_syllables",
        lambda text: syllables,
    )
    result = calculate_readability_metrics("One sentence.")
    assert result is not None
    assert result["ease_level"] == expected_level


def test_readability_backend_failure_returns_none(monkeypatch):
    def fail(_text):
        raise RuntimeError("simulated tokenizer failure")

    monkeypatch.setattr(sentiment_analyzer, "extract_words", fail)
    assert calculate_readability_metrics("A valid sentence.") is None


def test_syllable_estimator_covers_silent_e_and_consonant_only_word():
    assert estimate_syllables("table") == 1
    assert estimate_syllables("rhythms") >= 1
    assert estimate_syllables("") == 0


def test_comprehensive_analysis_omits_missing_sections(monkeypatch):
    monkeypatch.setattr(sentiment_analyzer, "analyze_sentiment", lambda text: None)
    monkeypatch.setattr(sentiment_analyzer, "detect_emotions", lambda text: None)
    monkeypatch.setattr(
        sentiment_analyzer,
        "calculate_readability_metrics",
        lambda text: None,
    )
    assert get_comprehensive_analysis("plain text") == {}


def test_comprehensive_analysis_failure_returns_empty_dict(monkeypatch):
    def fail(_text):
        raise RuntimeError("simulated comprehensive failure")

    monkeypatch.setattr(sentiment_analyzer, "analyze_sentiment", fail)
    assert get_comprehensive_analysis("plain text") == {}
