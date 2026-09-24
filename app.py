"""Compatibility launcher. Install first with `uv sync` or `pip install .`."""

from yt_transcript.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["serve"]))
