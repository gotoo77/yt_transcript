import pytest

from yt_transcript.video import extract_video_id


@pytest.mark.parametrize(
    "value",
    [
        "dQw4w9WgXcQ",
        " https://youtu.be/dQw4w9WgXcQ?t=10 ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=123",
        "youtube.com/shorts/dQw4w9WgXcQ",
        "https://m.youtube.com/embed/dQw4w9WgXcQ",
        "https://youtube.com/live/dQw4w9WgXcQ",
    ],
)
def test_extract_supported_video(value):
    assert extract_video_id(value) == "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "é" * 11,
        "https://youtube.com.evil.org/watch?v=dQw4w9WgXcQ",
        "https://evil.com/youtube.com/dQw4w9WgXcQ",
        "https://youtube.com@evil.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQextra",
        "ftp://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=short",
        None,
    ],
)
def test_reject_invalid_or_deceptive_video(value):
    with pytest.raises(ValueError):
        extract_video_id(value)
