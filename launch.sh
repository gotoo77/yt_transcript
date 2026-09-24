#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
action="${1:-serve}"
if [[ $# -gt 0 ]]; then shift; fi
if [[ "$action" == "install" ]]; then exec uv sync --locked "$@"; fi
if [[ "$action" == "help" ]]; then exec uv run yt-transcript --help; fi
exec uv run yt-transcript "$action" "$@"
