"""Validation of supported YouTube URLs and identifiers."""

import re
from urllib.parse import parse_qs, urlsplit


def extract_video_id(url_or_id: str) -> str:
    if not isinstance(url_or_id, str) or not url_or_id.strip():
        raise ValueError("URL ou ID vidéo invalide")
    value = url_or_id.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    if "://" not in value:
        value = "https://" + value
    url = urlsplit(value)
    if url.scheme not in {"http", "https"} or url.username or url.password:
        raise ValueError("URL YouTube invalide")
    host = url.hostname
    parts = url.path.strip("/").split("/")
    candidate = ""
    if host in {"youtu.be", "www.youtu.be"} and len(parts) == 1:
        candidate = parts[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if url.path == "/watch":
            candidate = parse_qs(url.query).get("v", [""])[0]
        elif len(parts) == 2 and parts[0] in {"embed", "shorts", "live"}:
            candidate = parts[1]
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        raise ValueError("URL YouTube ou ID vidéo invalide")
    return candidate
