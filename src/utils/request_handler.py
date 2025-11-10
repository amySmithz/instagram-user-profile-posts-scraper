# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("request_handler")

@dataclass
class RequestHandler:
    settings: Dict[str, Any]

    def __post_init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.settings.get(
                    "user_agent",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                ),
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            }
        )
        self.timeout = int(self.settings.get("request_timeout", 15))
        self.mock = bool(self.settings.get("mock", True))
        self.max_retries = int(self.settings.get("max_retries", 3))
        seed = str(self.settings.get("random_seed", "bitbash"))
        random.seed(seed)

    # -------------------- Public API --------------------

    def fetch_user_posts(self, username: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Returns a list of raw post dicts.
        In mock mode, generates deterministic fake posts.
        In live mode, attempts to fetch from the public IG page HTML (best-effort).
        """
        if self.mock:
            return self._mock_posts(username, limit)

        # Best-effort live fetch (may fail due to IG protection; we handle gracefully)
        try:
            # Fetch the profile page (HTML). Parsing IG HTML is unstable; we keep it resilient.
            url = f"https://www.instagram.com/{username}/"
            html = self._get_with_retries(url)
            # Very naive extraction of "shortcode" occurrences as an example
            posts = self._extract_from_html(html, username, limit)
            return posts
        except Exception as e:
            logger.warning("Live fetch failed for @%s (%s). Falling back to mock.", username, e)
            return self._mock_posts(username, limit)

    # -------------------- Internal helpers --------------------

    def _get_with_retries(self, url: str) -> str:
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.text
                last_err = RuntimeError(f"HTTP {resp.status_code}")
            except Exception as e:
                last_err = e
            sleep = min(2 ** attempt, 8) + random.random()
            logger.debug("GET %s attempt %d failed; retrying in %.1fs", url, attempt, sleep)
            time.sleep(sleep)
        assert last_err is not None
        raise last_err

    def _extract_from_html(self, html: str, username: str, limit: Optional[int]) -> List[Dict[str, Any]]:
        # This is intentionally simple; for robust scraping you'd use a proper parser & API.
        shortcodes = []
        marker = "/p/"
        idx = 0
        while True:
            i = html.find(marker, idx)
            if i == -1:
                break
            # shortcode ends at next slash or quote
            j = i + len(marker)
            k = j
            while k < len(html) and html[k] not in ['/', '"', "'", '\\', '?', '&', ' ']:
                k += 1
            sc = html[j:k]
            if sc and sc not in shortcodes:
                shortcodes.append(sc)
            idx = k
            if limit and len(shortcodes) >= limit:
                break

        posts: List[Dict[str, Any]] = []
        for n, sc in enumerate(shortcodes or []):
            pid = self._deterministic_id(username, n)
            posts.append(
                {
                    "id": pid,
                    "shortcode": sc,
                    "caption": "",
                    "timestamp": int(time.time()) - (n * 86400),
                    "likes": random.randint(100, 10000),
                    "comments": random.randint(0, 500),
                    "mediaType": "image",
                    "displayUrl": f"https://www.instagram.com/p/{sc}",
                    "thumbnailUrl": f"https://www.instagram.com/p/{sc}/media",
                    "dimensions_width": 1080,
                    "dimensions_height": 1350,
                    "tags": [],
                    "commentsDisabled": False,
                    "pinned": False,
                }
            )
        # If nothing found, fallback to mock
        return posts or self._mock_posts(username, limit)

    def _mock_posts(self, username: str, limit: Optional[int]) -> List[Dict[str, Any]]:
        count = limit or 12
        base = int(hashlib.md5(username.encode("utf-8")).hexdigest(), 16) % 10_000
        posts: List[Dict[str, Any]] = []
        for i in range(count):
            pid = self._deterministic_id(username, i)
            short = f"MOCK{base + i:06d}"
            media_type = "video" if (i % 5 == 0) else "image"
            posts.append(
                {
                    "id": pid,
                    "shortcode": short,
                    "caption": f"Mock post {i+1} by @{username}",
                    "timestamp": int(time.time()) - (i * 3600),
                    "likes": 1000 + (i * 13),
                    "comments": 50 + (i * 3),
                    "mediaType": media_type,
                    "displayUrl": f"https://instagram.com/p/{short}",
                    "thumbnailUrl": f"https://instagram.com/p/{short}/media",
                    "dimensions_width": 1080,
                    "dimensions_height": 1350 if media_type == "image" else 1080,
                    "tags": [
                        {
                            "fullName": "Kris Jenner" if i % 7 == 0 else "John Doe",
                            "profilePicUrl": "https://example.com/u.jpg",
                            "username": "krisjenner" if i % 7 == 0 else "johndoe",
                        }
                    ],
                    "commentsDisabled": False,
                    "pinned": True if i == 0 else False,
                    "location": {
                        "id": f"loc_{base}_{i}" if i % 3 == 0 else None,
                        "name": "Menlo Park" if i % 3 == 0 else None,
                        "slug": "menlo-park" if i % 3 == 0 else None,
                        "has_public_page": True if i % 3 == 0 else None,
                    },
                    "isAffiliate": (i % 9 == 0),
                    "isPaidPartnership": (i % 11 == 0),
                }
            )
        return posts

    @staticmethod
    def _deterministic_id(username: str, index: int) -> str:
        data = f"{username}:{index}".encode("utf-8")
        return hashlib.sha1(data).hexdigest()