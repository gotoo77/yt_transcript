"""Focused branch coverage for transcript analysis concepts, summaries and fallbacks."""

import pytest

import yt_transcript.transcript_analyzer as analyzer
from yt_transcript.transcript_analyzer import (
    analyze_concepts,
    analyze_text,
    extract_words,
    generate_summary,
)


def test_extract_words_keeps_meaningful_apostrophe_contraction():
    words = extract_words("Aujourd'hui robot science")
    assert "aujourd'hui" in words


def test_concept_analysis_counts_repeated_matches():
    words = ["science", "science", "recherche", "robot"]
    concepts = dict(analyze_concepts(words))

    assert concepts
    science_like = [
        data
        for data in concepts.values()
        if "science" in data["words"] or "recherche" in data["words"]
    ]
    assert science_like
    assert any(data["score"] >= 2 for data in science_like)
    assert any(data["percentage"] > 0 for data in science_like)


def test_summary_applies_length_and_position_bonuses():
    middle = " ".join(["robot"] * 12)
    text = (
        "Première phrase suffisamment longue avec science et robot. "
        "Deuxième phrase suffisamment longue avec python et données. "
        f"{middle}. "
        "Quatrième phrase suffisamment longue avec jardin et nature. "
        "Dernière phrase suffisamment longue avec analyse et résultat."
    )

    summary = generate_summary(text, 2)
    assert summary.endswith(".")
    assert summary.count(".") == 2


def test_analyze_text_concepts_mode_returns_concepts():
    result, count = analyze_text("science recherche science robot", mode="concepts")
    assert count == 4
    assert result


def test_unknown_mode_falls_back_to_style():
    expected, count = analyze_text("robot robot python", mode="style", max_words=2)
    actual, fallback_count = analyze_text("robot robot python", mode="unexpected", max_words=2)

    assert fallback_count == count
    assert actual == expected


def test_analyze_text_propagates_internal_failure(monkeypatch):
    def fail(_text):
        raise RuntimeError("simulated extraction failure")

    monkeypatch.setattr(analyzer, "extract_words", fail)

    with pytest.raises(RuntimeError, match="simulated extraction failure"):
        analyze_text("robot science")
