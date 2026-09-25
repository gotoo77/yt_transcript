"""Focused coverage for CLI command dispatch and error handling."""

from types import SimpleNamespace

import pytest

from yt_transcript.cli import main, port_number


def test_valid_port_number():
    assert port_number("5001") == 5001
    assert port_number("1") == 1
    assert port_number("65535") == 65535


def test_start_restart_and_active_status(tmp_path, monkeypatch, capsys):
    prefix = ["--data-dir", str(tmp_path)]

    monkeypatch.setattr("yt_transcript.runtime.start", lambda directory, host, port: 4242)
    monkeypatch.setattr("yt_transcript.runtime.stop", lambda directory: True)
    monkeypatch.setattr(
        "yt_transcript.runtime.managed_process",
        lambda directory: SimpleNamespace(pid=4242),
    )

    assert main([*prefix, "start", "--host", "127.0.0.1", "--port", "5002"]) == 0
    assert "PID 4242" in capsys.readouterr().out

    assert main([*prefix, "restart", "--port", "5003"]) == 0
    output = capsys.readouterr().out
    assert "Serveur arrêté." in output
    assert "PID 4242" in output

    assert main([*prefix, "status"]) == 0
    assert "Serveur actif (PID 4242)." in capsys.readouterr().out


def test_stop_reports_already_stopped(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("yt_transcript.runtime.stop", lambda directory: False)
    assert main(["--data-dir", str(tmp_path), "stop"]) == 0
    assert "Serveur déjà arrêté." in capsys.readouterr().out


def test_serve_dispatches_to_waitress(tmp_path, monkeypatch):
    calls = {}

    class App:
        pass

    app = App()

    def create_app(config):
        calls["config"] = config
        return app

    def serve(received_app, host, port, threads):
        calls["serve"] = (received_app, host, port, threads)

    monkeypatch.setattr("yt_transcript.create_app", create_app)
    monkeypatch.setattr("waitress.serve", serve)

    assert (
        main(
            [
                "--data-dir",
                str(tmp_path),
                "serve",
                "--host",
                "0.0.0.0",
                "--port",
                "5004",
            ]
        )
        == 0
    )
    assert calls["config"]["DATA_DIR"] == tmp_path.resolve()
    assert calls["serve"] == (app, "0.0.0.0", 5004, 4)


def test_dev_dispatches_to_flask_runner(tmp_path, monkeypatch):
    calls = {}

    class App:
        def run(self, **kwargs):
            calls.update(kwargs)

    monkeypatch.setattr("yt_transcript.create_app", lambda config: App())

    assert main(["--data-dir", str(tmp_path), "dev", "--port", "5005"]) == 0
    assert calls == {"host": "127.0.0.1", "port": 5005, "debug": True}


def test_logs_reject_non_positive_line_count(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["--data-dir", str(tmp_path), "logs", "--lines", "0"])
    assert error.value.code == 2


def test_runtime_error_is_reported_generically(tmp_path, monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise RuntimeError("simulated startup failure")

    monkeypatch.setattr("yt_transcript.runtime.start", fail)
    assert main(["--data-dir", str(tmp_path), "start"]) == 1
    assert "Erreur : simulated startup failure" in capsys.readouterr().err


def test_keyboard_interrupt_returns_shell_interrupt_code(tmp_path, monkeypatch):
    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr("yt_transcript.runtime.start", interrupt)
    assert main(["--data-dir", str(tmp_path), "start"]) == 130
