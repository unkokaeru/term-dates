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

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / f"{digest}.json"

    def get(self, key: str) -> str | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if time.time() - payload["timestamp"] > self.ttl_seconds:
            return None
        return payload["body"]

    def set(self, key: str, body: str) -> None:
        path = self._path(key)
        path.write_text(
            json.dumps({"timestamp": time.time(), "key": key, "body": body}),
            encoding="utf-8",
        )

    def clear(self) -> None:
        for child in self.root.glob("*.json"):
            child.unlink(missing_ok=True)
