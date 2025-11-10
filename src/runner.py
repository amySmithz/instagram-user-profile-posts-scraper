# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .utils.request_handler import RequestHandler
from .utils.json_exporter import export_json, export_csv
from .extractors.profile_posts_parser import normalize_posts
from .extractors.tagged_users_extractor import extract_tagged_from_raw
from .extractors.location_info_parser import parse_location_from_raw

logger = logging.getLogger("runner")

@dataclass
class Runner:
    settings: Dict[str, Any]
    repo_root: str

    def _resolve_output_path(self) -> Path:
        out_path = self.settings.get("output_path", "data/sample_output.json")
        p = Path(self.repo_root) / out_path
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def _max_posts(self) -> int | None:
        val = self.settings.get("max_posts_per_profile")
        if val in (None, "", 0):
            return None
        try:
            return int(val)
        except Exception:
            logger.warning("Invalid max_posts_per_profile in settings; ignoring.")
            return None

    def run(self, usernames: Iterable[str]) -> None:
        logger.info("Starting runner for %d usernames", len(list(usernames)))
        rh = RequestHandler(self.settings)

        final_rows: List[Dict[str, Any]] = []
        for username in usernames:
            try:
                logger.info("Fetching posts for @%s ...", username)
                raw_posts = rh.fetch_user_posts(username, self._max_posts())
                # Enrich raw posts with tagged users and location fields if present
                for post in raw_posts:
                    post["taggedUsers"] = extract_tagged_from_raw(post)
                    post.update(parse_location_from_raw(post))
                normalized = normalize_posts(username, raw_posts)
                final_rows.extend(normalized)
                logger.info("Fetched %d posts for @%s", len(normalized), username)
            except Exception as e:
                logger.exception("Failed to fetch/parse posts for @%s: %s", username, e)

        output_path = self._resolve_output_path()
        fmt = (self.settings.get("output_format") or "json").lower()

        if fmt == "csv":
            export_csv(final_rows, output_path.with_suffix(".csv"))
            logger.info("Exported %d rows to %s", len(final_rows), output_path.with_suffix(".csv"))
        else:
            export_json(final_rows, output_path)
            logger.info("Exported %d rows to %s", len(final_rows), output_path)

        # Optionally also write a machine-friendly 'latest.json' snapshot in data/
        snapshot_path = Path(self.repo_root) / "data" / "latest.json"
        try:
            snapshot_path.write_text(json.dumps(final_rows, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            logger.debug("Could not write snapshot to %s", snapshot_path)