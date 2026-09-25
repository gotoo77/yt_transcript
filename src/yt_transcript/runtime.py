"""Manage only the server whose PID, creation time and command we recorded."""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4

import psutil
from filelock import FileLock

_children: dict[int, subprocess.Popen[bytes]] = {}


def managed_process(directory: Path) -> psutil.Process | None:
    try:
        state = json.loads((directory / "server.json").read_text(encoding="utf-8"))
        process = psutil.Process(state["pid"])
        if process.create_time() != state["created"] or process.cmdline() != state["command"]:
            return None
        command = process.cmdline()
        if "yt_transcript" not in command or "serve" not in command:
            return None
        return (
            process if process.is_running() and process.status() != psutil.STATUS_ZOMBIE else None
        )
    except (OSError, ValueError, KeyError, TypeError, psutil.Error):
        return None


def start(directory: Path, host: str, port: int) -> int:
    directory.mkdir(parents=True, exist_ok=True)
    with FileLock(str(directory / "server.lock"), timeout=10):
        existing = managed_process(directory)
        if existing:
            return existing.pid
        # Probe a listener rather than binding: TIME_WAIT must not prevent restart.
        target = "127.0.0.1" if host == "0.0.0.0" else ("::1" if host == "::" else host)
        try:
            probe = socket.create_connection((target, port), timeout=0.5)
        except OSError:
            pass
        else:
            probe.close()
            raise OSError(f"Le port {port} est déjà utilisé")
        command = [
            sys.executable,
            "-m",
            "yt_transcript",
            "--data-dir",
            str(directory),
            "serve",
            "--host",
            host,
            "--port",
            str(port),
        ]
        instance = uuid4().hex
        environment = dict(
            os.environ,
            PYTHONIOENCODING="utf-8",
            PYTHONUNBUFFERED="1",
            YT_TRANSCRIPT_INSTANCE_ID=instance,
        )
        with (directory / "server.log").open("ab") as log:
            child = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                env=environment,
                creationflags=(
                    getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                )
                if os.name == "nt"
                else 0,
                start_new_session=os.name != "nt",
            )
        try:
            process = psutil.Process(child.pid)
            state = {
                "pid": child.pid,
                "created": process.create_time(),
                "command": command,
                "host": host,
                "port": port,
            }
            # Record immediately so a parent interrupted during startup can still be stopped.
            state_path = directory / "server.json"
            temporary = directory / "server.json.tmp"
            temporary.write_text(json.dumps(state), encoding="utf-8")
            temporary.replace(state_path)
            url_host = f"[{target}]" if ":" in target else target
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if child.poll() is not None:
                    raise RuntimeError(
                        f"Le serveur a quitté avec le code {child.returncode}. Voir {directory / 'server.log'}"
                    )
                try:
                    with urlopen(f"http://{url_host}:{port}/health", timeout=0.5) as response:
                        payload = json.load(response)
                        if payload.get("instance") == instance and child.poll() is None:
                            _children[child.pid] = child
                            return child.pid
                except (URLError, OSError):
                    pass
                time.sleep(0.15)
            raise RuntimeError("Le serveur ne répond pas après 30 secondes")
        except BaseException:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=10)
            (directory / "server.json").unlink(missing_ok=True)
            raise


def stop(directory: Path) -> bool:
    directory.mkdir(parents=True, exist_ok=True)
    with FileLock(str(directory / "server.lock"), timeout=10):
        process = managed_process(directory)
        if process is None:
            (directory / "server.json").unlink(missing_ok=True)
            return False
        try:
            process.terminate()
            child = _children.pop(process.pid, None)
            if child is not None:
                child.wait(timeout=10)
            else:
                process.wait(timeout=10)
        except psutil.NoSuchProcess:
            pass
        except psutil.TimeoutExpired as error:
            raise RuntimeError("Le serveur ne s'est pas arrêté ; consultez les logs") from error
        (directory / "server.json").unlink(missing_ok=True)
        return True
