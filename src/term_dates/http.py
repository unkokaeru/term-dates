"""Polite HTTP client with caching, retries, and a real browser User-Agent.

Many UK council and school sites are behind WAFs (Cloudflare etc.) that reject
the default httpx User-Agent. We send a realistic UA and respect a small
retry/backoff schedule.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from term_dates.cache import DEFAULT_TTL_SECONDS, FileCache, default_cache_dir

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 term-dates/0.1"
)


@dataclass(slots=True)
class Fetcher:
    """A small wrapper around httpx that caches GETs to disk."""

    cache: FileCache
    user_agent: str = DEFAULT_UA
    timeout_seconds: float = 25.0
    retries: int = 3
    backoff_seconds: float = 1.5

    @classmethod
    def default(
        cls, cache_dir: Path | None = None, ttl_seconds: int = DEFAULT_TTL_SECONDS
    ) -> Fetcher:
        return cls(cache=FileCache(cache_dir or default_cache_dir(), ttl_seconds=ttl_seconds))

    def get_text(self, url: str, *, force_refresh: bool = False) -> str:
        if not force_refresh:
            cached = self.cache.get(url)
            if cached is not None:
                return cached
        response = self._get(url)
        body = response.text
        self.cache.set(url, body)
        return body

    def get_bytes(self, url: str, *, force_refresh: bool = False) -> bytes:
        """Fetch a URL as raw bytes (for binary content like PDFs)."""
        if not force_refresh:
            cached = self.cache.get_bytes(url)
            if cached is not None:
                return cached
        response = self._get(url)
        body = response.content
        self.cache.set_bytes(url, body)
        return body

    def _get(self, url: str) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self.retries):
            try:
                with httpx.Client(
                    follow_redirects=True,
                    timeout=self.timeout_seconds,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": (
                            "text/html,application/xhtml+xml,application/xml;q=0.9,"
                            "application/pdf;q=0.9,*/*;q=0.8"
                        ),
                        "Accept-Language": "en-GB,en;q=0.9",
                    },
                ) as client:
                    response = client.get(url)
                response.raise_for_status()
                return response
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt + 1 < self.retries:
                    time.sleep(self.backoff_seconds * (2**attempt))
        assert last_exc is not None
        raise last_exc
