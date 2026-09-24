"""Cross-platform application and maintenance commands."""

import argparse
import logging
import os
import sys
import time
from collections import deque
from pathlib import Path

from .config import data_directory


def port_number(value: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Le port doit être un entier") from error
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("Le port doit être compris entre 1 et 65535")
    return port


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="yt-transcript")
    parser.add_argument("--data-dir", type=Path, default=data_directory())
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("serve", "dev", "start", "restart"):
        command = commands.add_parser(name)
        command.add_argument("--host", default=os.environ.get("YT_TRANSCRIPT_HOST", "127.0.0.1"))
        command.add_argument(
            "--port", type=port_number, default=os.environ.get("YT_TRANSCRIPT_PORT", "5001")
        )
    for name in ("stop", "status", "info"):
        commands.add_parser(name)
    logs = commands.add_parser("logs")
    logs.add_argument("--lines", type=int, default=50)
    logs.add_argument("--follow", action="store_true")
    args = parser.parse_args(argv)
    directory = args.data_dir.expanduser().resolve()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    try:
        if args.command in {"serve", "dev"}:
            from . import create_app

            app = create_app({"DATA_DIR": directory})
            if args.command == "dev":
                app.run(host=args.host, port=args.port, debug=True)
            else:
                from waitress import serve

                serve(app, host=args.host, port=args.port, threads=4)
        elif args.command in {"start", "restart", "stop", "status"}:
            from .runtime import managed_process, start, stop

            if args.command in {"stop", "restart"}:
                print("Serveur arrêté." if stop(directory) else "Serveur déjà arrêté.")
            if args.command in {"start", "restart"}:
                process_id = start(directory, args.host, args.port)
                print(f"Serveur démarré (PID {process_id}) : http://{args.host}:{args.port}")
            if args.command == "status":
                process = managed_process(directory)
                print(f"Serveur actif (PID {process.pid})." if process else "Serveur arrêté.")
                return 0 if process else 1
        elif args.command == "logs":
            if args.lines < 1:
                parser.error("--lines doit être positif")
            with (directory / "server.log").open(encoding="utf-8", errors="replace") as log:
                print("".join(deque(log, maxlen=args.lines)), end="")
                while args.follow:
                    line = log.readline()
                    if line:
                        print(line, end="", flush=True)
                    else:
                        time.sleep(0.25)
        else:
            print(
                f"Python : {sys.version.split()[0]}\nDonnées : {directory}\nBase : {directory / 'yt_analyzer.db'}\nLogs : {directory / 'server.log'}"
            )
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Erreur : {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0
