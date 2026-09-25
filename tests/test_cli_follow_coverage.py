"""Coverage for CLI log-follow behavior."""

import yt_transcript.cli as cli_module
from yt_transcript.cli import main


class FakeLog:
    def __init__(self, readline):
        self._readline = readline

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def __iter__(self):
        return iter(["tail\n"])

    def readline(self):
        return self._readline()


def test_logs_follow_prints_new_line_then_handles_interrupt(tmp_path, monkeypatch, capsys):
    reads = iter(["follow\n"])

    def readline():
        try:
            return next(reads)
        except StopIteration:
            raise KeyboardInterrupt

    monkeypatch.setattr(
        cli_module.Path,
        "open",
        lambda self, **kwargs: FakeLog(readline),
    )

    result = main(["--data-dir", str(tmp_path), "logs", "--follow"])
    assert result == 130
    assert capsys.readouterr().out == "tail\nfollow\n"


def test_logs_follow_waits_when_no_line_is_available(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        cli_module.Path,
        "open",
        lambda self, **kwargs: FakeLog(lambda: ""),
    )

    def interrupt_sleep(_seconds):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli_module.time, "sleep", interrupt_sleep)

    result = main(["--data-dir", str(tmp_path), "logs", "--follow"])
    assert result == 130
    assert capsys.readouterr().out == "tail\n"
