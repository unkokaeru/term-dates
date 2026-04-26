"""Tiny filesystem cache for HTTP responses (TTL-based)."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_cache_dir

DEFAULT_TTL_SECONDS = 60 * 60 * 12  # 12h — councils update term dates rarely


def default_cache_dir() -> Path:
    return Path(user_cache_dir("term-dates", appauthor=False))


@dataclass(slots=True)
class FileCache:
    root: Path
    ttl_seconds: int = DEFAULT_TTL_SECONDS

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def _text_path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / f"{digest}.json"

    def _bin_path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / f"{digest}.bin"

    def get(self, key: str) -> str | None:
        path = self._text_path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if time.time() - payload["timestamp"] > self.ttl_seconds:
            return None
        body = payload["body"]
        return body if isinstance(body, str) else None

    def set(self, key: str, body: str) -> None:
        path = self._text_path(key)
        path.write_text(
            json.dumps({"timestamp": time.time(), "key": key, "body": body}),
            encoding="utf-8",
        )

    def get_bytes(self, key: str) -> bytes | None:
        path = self._bin_path(key)
        meta = self._text_path(key + "::bin")
        if not path.exists() or not meta.exists():
            return None
        try:
            ts = float(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if time.time() - ts > self.ttl_seconds:
            return None
        try:
            return path.read_bytes()
        except OSError:
            return None

    def set_bytes(self, key: str, body: bytes) -> None:
        path = self._bin_path(key)
        meta = self._text_path(key + "::bin")
        path.write_bytes(body)
        meta.write_text(str(time.time()), encoding="utf-8")

    def clear(self) -> None:
        for child in self.root.glob("*.json"):
            child.unlink(missing_ok=True)
        for child in self.root.glob("*.bin"):
            child.unlink(missing_ok=True)
