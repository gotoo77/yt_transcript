import pytest

from yt_transcript.transcript_analyzer import (
    analyze_concepts,
    analyze_style,
    analyze_text,
    extract_words,
    generate_summary,
    get_text_statistics,
    get_word_cloud_data,
)


def test_filters_french_english_noise_preserving_meaning():
    assert extract_words("Le robot robot et Python! the 123 hahaha aaaa") == [
        "robot",
        "robot",
        "python",
    ]


def test_frequency_counts_and_limit():
    assert analyze_style(["robot", "python", "robot", "science"], 2) == [
        ("robot", 2),
        ("python", 1),
    ]


@pytest.mark.parametrize("limit,expected", [(0, 1), (-3, 1), (250, 200)])
def test_frequency_limit_is_bounded(limit, expected):
    assert len(analyze_style([f"word{i}" for i in range(210)], limit)) == expected


def test_empty_analysis():
    assert analyze_text("  ") == ([], 0)
    assert analyze_text("le et the") == ([], 0)
    assert analyze_concepts([]) == []
    assert get_word_cloud_data([]) == []


def test_statistics_have_exact_counts():
    stats = get_text_statistics(["robot", "robot", "python"], "robot robot. python.")
    assert stats["total_words"] == 3
    assert stats["unique_words"] == 2
    assert stats["sentences"] == 2
    assert stats["vocabulary_richness"] == 66.7
    assert stats["average_word_length"] == 5.3


def test_empty_statistics_do_not_divide_by_zero():
    stats = get_text_statistics([], "")
    assert stats["total_words"] == stats["complexity_score"] == 0


def test_cloud_sizes_reflect_frequency():
    cloud = get_word_cloud_data(["robot", "robot", "python"])
    assert [(entry["word"], entry["count"], entry["size"]) for entry in cloud] == [
        ("robot", 2, 5.0),
        ("python", 1, 1.0),
    ]
    assert get_word_cloud_data(["robot"])[0]["size"] == 3


def test_summary_selects_important_sentence():
    text = "Robot robot robot science. Python développe des programmes. Jardin fleurs nature."
    assert generate_summary(text, 1) == "Robot robot robot science."
    assert generate_summary("") == ""
    assert generate_summary("Une phrase assez longue.") == "Une phrase assez longue."
