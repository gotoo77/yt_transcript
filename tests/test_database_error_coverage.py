"""Exercise analysis persistence fallbacks with an isolated application database."""

import pytest

from yt_transcript import database


@pytest.mark.parametrize(
    ("function", "args", "fallback"),
    [
        ("save_analysis", ("A short analysis.", "style", [], {}), None),
        ("get_recent_analyses", (), []),
        ("get_analysis_by_id", (123,), None),
        ("search_analyses", ("robot",), []),
        (
            "get_analysis_stats",
            (),
            {
                "total_analyses": 0,
                "total_words_analyzed": 0,
                "average_text_length": 0,
            },
        ),
    ],
)
def test_analysis_storage_unavailable_returns_documented_fallbacks(
    app, monkeypatch, function, args, fallback
):
    def unavailable():
        raise OSError("simulated unavailable database")

    with app.app_context():
        monkeypatch.setattr(database, "get_db_session", unavailable)
        assert getattr(database, function)(*args) == fallback


def test_failed_analysis_commit_rolls_back_and_leaves_database_usable(app, monkeypatch):
    from sqlalchemy.orm import Session

    with app.app_context():
        original_commit = Session.commit

        def reject_commit(self):
            raise OSError("simulated storage failure")

        monkeypatch.setattr(Session, "commit", reject_commit)
        assert database.save_analysis("A short analysis.", "style", [], {}) is None

        monkeypatch.setattr(Session, "commit", original_commit)
        assert database.get_recent_analyses() == []
        saved = database.save_analysis("Another short analysis.", "style", [], {})
        assert saved is not None
        assert database.get_analysis_by_id(saved).original_text == "Another short analysis."


def test_analysis_repr_and_concepts_mode_roundtrip(app):
    with app.app_context():
        saved = database.save_analysis(
            "Nature and science.",
            "concepts",
            [["nature", {"score": 2}]],
            {"total_words": 3},
        )
        assert saved is not None
        record = database.get_analysis_by_id(saved)
        assert record is not None
        assert record.word_frequency is None
        assert record.concepts_detected == [["nature", {"score": 2}]]
        assert f"Analysis(id={saved}, mode=concepts" in repr(record)
