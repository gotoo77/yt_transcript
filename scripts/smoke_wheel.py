"""Install and run a built wheel outside the source tree."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    wheels = list((root / "dist").glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit("Expected exactly one wheel in dist/; run uv build first.")
    with tempfile.TemporaryDirectory(prefix="yt-wheel-") as temporary:
        directory = Path(temporary)
        environment = directory / "venv"
        subprocess.run(["uv", "venv", "--python", sys.executable, str(environment)], check=True)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            ["uv", "pip", "install", "--python", str(python), str(wheels[0])], check=True
        )
        code = """
import socket
from pathlib import Path
from urllib.request import urlopen
import yt_transcript
from yt_transcript.runtime import start, stop
assert 'site-packages' in yt_transcript.__file__, yt_transcript.__file__
directory = Path('data').resolve()
with socket.socket() as probe:
    probe.bind(('127.0.0.1', 0))
    port = probe.getsockname()[1]
try:
    start(directory, '127.0.0.1', port)
    for path in ('/', '/dashboard', '/static/app.js', '/static/dashboard.js', '/api/docs/', '/health'):
        with urlopen(f'http://127.0.0.1:{port}{path}', timeout=5) as response:
            assert response.status == 200, path
            assert response.read(), path
finally:
    stop(directory)
print('Installed wheel: HTTP, templates, static assets and process lifecycle OK')
"""
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env.pop("DATABASE_URL", None)
        env.pop("SECRET_KEY", None)
        subprocess.run([str(python), "-I", "-c", code], cwd=directory, env=env, check=True)


if __name__ == "__main__":
    main()
