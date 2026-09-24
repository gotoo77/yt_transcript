import json
import os
import socket
import time
from urllib.request import urlopen

import psutil
import pytest

from yt_transcript.runtime import managed_process, start, stop


def test_reused_pid_is_not_ours(tmp_path):
    process = psutil.Process()
    (tmp_path / "server.json").write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "created": process.create_time() - 10,
                "command": process.cmdline(),
            }
        )
    )
    assert managed_process(tmp_path) is None
    assert stop(tmp_path) is False
    assert process.is_running()


def test_same_pid_with_different_command_is_not_ours(tmp_path):
    process = psutil.Process()
    (tmp_path / "server.json").write_text(
        json.dumps({"pid": os.getpid(), "created": process.create_time(), "command": ["foreign"]})
    )
    assert managed_process(tmp_path) is None
    assert process.is_running()


def test_corrupted_state_is_safe(tmp_path):
    (tmp_path / "server.json").write_text("broken json")
    assert managed_process(tmp_path) is None
    assert stop(tmp_path) is False


def test_real_server_lifecycle_and_occupied_port(tmp_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    try:
        process_id = start(tmp_path, "127.0.0.1", port)
        assert managed_process(tmp_path).pid == process_id
        assert start(tmp_path, "127.0.0.1", port) == process_id
        with urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as response:
            assert json.load(response)["status"] == "ok"
        with pytest.raises(OSError):
            start(tmp_path / "other", "127.0.0.1", port)
        assert managed_process(tmp_path).pid == process_id
        assert stop(tmp_path) is True
        # Windows may briefly retain the listener after the child exits.
        # Wait for the actual port to close; do not retry start against a live listener.
        deadline = time.monotonic() + 5
        while True:
            try:
                connection = socket.create_connection(("127.0.0.1", port), timeout=0.2)
            except OSError:
                break
            else:
                connection.close()
            if time.monotonic() >= deadline:
                pytest.fail("Server listener still accepts connections after stop()")
            time.sleep(0.05)
        process_id = start(tmp_path, "127.0.0.1", port)
        with urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as response:
            assert response.status == 200
    finally:
        stop(tmp_path)
    assert managed_process(tmp_path) is None
    assert not psutil.pid_exists(process_id)
