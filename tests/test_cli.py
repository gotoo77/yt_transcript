import pytest

from yt_transcript.cli import main


def test_info_and_stopped_status(tmp_path, capsys):
    prefix = ["--data-dir", str(tmp_path)]
    assert main([*prefix, "info"]) == 0
    assert str(tmp_path) in capsys.readouterr().out
    assert main([*prefix, "status"]) == 1
    assert main([*prefix, "stop"]) == 0


@pytest.mark.parametrize("port", ["0", "65536", "abc", "-1"])
def test_bad_port_fails_before_start(port):
    with pytest.raises(SystemExit) as error:
        main(["serve", "--port", port])
    assert error.value.code == 2


def test_logs_tail_and_missing_file(tmp_path, capsys):
    prefix = ["--data-dir", str(tmp_path)]
    assert main([*prefix, "logs"]) == 1
    (tmp_path / "server.log").write_text("first\nsecond\nthird\n", encoding="utf-8")
    assert main([*prefix, "logs", "--lines", "2"]) == 0
    assert capsys.readouterr().out == "second\nthird\n"
