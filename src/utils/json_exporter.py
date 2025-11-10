# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

def export_json(rows: Iterable[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(list(rows), f, ensure_ascii=False, indent=2)

def export_csv(rows: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return
    # stable column order
    cols = [
        "id", "username", "shortcode", "caption", "timestamp",
        "likes", "comments", "mediaType", "displayUrl", "thumbnailUrl",
        "dimensions_width", "dimensions_height", "isAffiliate", "isPaidPartnership",
        "commentsDisabled", "pinned", "locationId", "locationName",
        "locationSlug", "locationHasPublicPage", "taggedUsers"
    ]
    # flatten taggedUsers as JSON string
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            r2 = dict(r)
            if isinstance(r2.get("taggedUsers"), (list, dict)):
                r2["taggedUsers"] = json.dumps(r2["taggedUsers"], ensure_ascii=False)
            writer.writerow(r2)