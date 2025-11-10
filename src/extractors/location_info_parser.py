# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

def parse_location_from_raw(post_raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize location info from raw post.
    Supports keys: location{id,name,slug,has_public_page} across shapes.
    """
    node = post_raw.get("node", post_raw)
    location = (
        node.get("location")
        or node.get("location_info")
        or {}
    )
    if not isinstance(location, dict):
        return {}

    return {
        "locationId": location.get("id") or location.get("pk") or node.get("locationId"),
        "locationName": location.get("name") or node.get("locationName"),
        "locationSlug": location.get("slug") or node.get("locationSlug"),
        "locationHasPublicPage": location.get("has_public_page") if "has_public_page" in location else node.get("locationHasPublicPage"),
    }