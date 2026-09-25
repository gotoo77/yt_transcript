"""Focused coverage for runtime startup and shutdown failure paths."""

import json
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest

import yt_transcript.runtime as runtime


class FakeProcess:
    def __init__(self, *, created=1.0, command=None, running=True, status="running", pid=1234):
        self._created = created
        self._command = command or ["python", "-m", "yt_transcript", "serve"]
        self._running = running
        self._status = status
        self.pid = pid

    def create_time(self):
        return self._created

    def cmdline(self):
        return self._command

    def is_running(self):
        return self._running

    def status(self):
        return self._status

    def terminate(self):
        pass

    def wait(self, timeout=None):
        return 0


def test_managed_process_rejects_non_server_command(tmp_path, monkeypatch):
    state = {
        "pid": 1234,
        "created": 1.0,
        "command": ["python", "-m", "yt_transcript", "info"],
    }
    (tmp_path / "server.json").write_text(json.dumps(state), encoding="utf-8")
    monkeypatch.setattr(runtime.psutil, "Process", lambda pid: FakeProcess(command=state["command"]))
    assert runtime.managed_process(tmp_path) is None


def test_managed_process_rejects_zombie(tmp_path, monkeypatch):
    state = {
        "pid": 1234,
        "created": 1.0,
        "command": ["python", "-m", "yt_transcript", "serve"],
    }
    (tmp_path / "server.json").write_text(json.dumps(state), encoding="utf-8")
    monkeypatch.setattr(
        runtime.psutil,
        "Process",
        lambda pid: FakeProcess(status=psutil.STATUS_ZOMBIE),
    )
    assert runtime.managed_process(tmp_path) is None


def test_start_cleans_up_when_child_exits_before_ready(tmp_path, monkeypatch):
    child = SimpleNamespace(
        pid=4321,
        returncode=7,
        poll=lambda: 7,
        terminate=lambda: None,
        wait=lambda timeout=None: 0,
    )

    monkeypatch.setattr(runtime, "managed_process", lambda directory: None)
    monkeypatch.setattr(runtime.socket, "create_connection", lambda *args, **kwargs: (_ for _ in ()).throw(OSError()))
    monkeypatch.setattr(runtime.subprocess, "Popen", lambda *args, **kwargs: child)
    monkeypatch.setattr(runtime.psutil, "Process", lambda pid: FakeProcess(pid=pid))

    with pytest.raises(RuntimeError, match="quitté avec le code 7"):
        runtime.start(tmp_path, "127.0.0.1", 5001)

    assert not (tmp_path / "server.json").exists()


def test_start_timeout_terminates_child_and_removes_state(tmp_path, monkeypatch):
    terminated = {"value": False}

    class Child:
        pid = 4321
        returncode = None

        def poll(self):
            return None

        def terminate(self):
            terminated["value"] = True

        def wait(self, timeout=None):
            return 0

    ticks = iter([0.0, 31.0, 31.0])

    monkeypatch.setattr(runtime, "managed_process", lambda directory: None)
    monkeypatch.setattr(runtime.socket, "create_connection", lambda *args, **kwargs: (_ for _ in ()).throw(OSError()))
    monkeypatch.setattr(runtime.subprocess, "Popen", lambda *args, **kwargs: Child())
    monkeypatch.setattr(runtime.psutil, "Process", lambda pid: FakeProcess(pid=pid))
    monkeypatch.setattr(runtime.time, "monotonic", lambda: next(ticks))

    with pytest.raises(RuntimeError, match="ne répond pas après 30 secondes"):
        runtime.start(tmp_path, "127.0.0.1", 5001)

    assert terminated["value"] is True
    assert not (tmp_path / "server.json").exists()


def test_stop_handles_process_disappearing(tmp_path, monkeypatch):
    process = FakeProcess()

    def vanish():
        raise psutil.NoSuchProcess(process.pid)

    process.terminate = vanish
    monkeypatch.setattr(runtime, "managed_process", lambda directory: process)

    assert runtime.stop(tmp_path) is True
    assert not (tmp_path / "server.json").exists()


def test_stop_timeout_becomes_runtime_error(tmp_path, monkeypatch):
    process = FakeProcess()

    def timeout(timeout=None):
        raise psutil.TimeoutExpired(process.pid)

    process.wait = timeout
    monkeypatch.setattr(runtime, "managed_process", lambda directory: process)

    with pytest.raises(RuntimeError, match="ne s'est pas arrêté"):
        runtime.stop(tmp_path)
