# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List

def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default

def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in ("true", "True", "1", 1):
        return True
    if value in ("false", "False", "0", 0):
        return False
    return default

def normalize_posts(username: str, raw_posts: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize diverse raw post structures to a unified schema."""
    rows: List[Dict[str, Any]] = []
    for p in raw_posts:
        # Support keys from mock or potential IG JSON shapes
        node = p.get("node", p)  # sometimes IG nests under 'node'
        id_ = str(node.get("id", node.get("pk", node.get("post_id", ""))))
        shortcode = node.get("shortcode") or node.get("code") or f"{id_[:5]}-{username}"
        caption = node.get("caption") or node.get("edge_media_to_caption", {}).get("text") or node.get("text") or ""
        ts = _coerce_int(node.get("taken_at_timestamp") or node.get("timestamp") or node.get("taken_at") or 0)
        likes = _coerce_int(
            node.get("edge_liked_by", {}).get("count")
            or node.get("like_count")
            or node.get("likes")
            or 0
        )
        comments = _coerce_int(
            node.get("edge_media_to_comment", {}).get("count")
            or node.get("comment_count")
            or node.get("comments")
            or 0
        )
        media_type = node.get("media_type") or node.get("__typename", "").lower().replace("graph", "") or node.get("mediaType") or "image"
        display_url = node.get("display_url") or node.get("displayUrl") or node.get("image_versions2", {}).get("candidates", [{}])[0].get("url") or ""
        thumb_url = node.get("thumbnail_src") or node.get("thumbnailUrl") or node.get("thumbnail_srcset", "").split(" ")[0] if node.get("thumbnail_srcset") else node.get("thumbnailUrl", "")
        dims = node.get("dimensions") or {}
        width = _coerce_int(dims.get("width") or node.get("dimensions_width") or 0)
        height = _coerce_int(dims.get("height") or node.get("dimensions_height") or 0)

        tagged_users = node.get("taggedUsers") or p.get("taggedUsers") or []
        comments_disabled = _coerce_bool(node.get("comments_disabled") or node.get("commentsDisabled") or False)
        pinned = _coerce_bool(node.get("pinned") or False)

        is_affiliate = _coerce_bool(node.get("isAffiliate") or node.get("is_affiliate") or False)
        is_paid = _coerce_bool(node.get("isPaidPartnership") or node.get("is_paid_partnership") or False)

        loc_id = node.get("locationId") or node.get("location_id")
        loc_name = node.get("locationName") or node.get("location_name")
        loc_slug = node.get("locationSlug") or node.get("location_slug")
        loc_public = node.get("locationHasPublicPage") if "locationHasPublicPage" in node else node.get("location_has_public_page")

        row = {
            "id": id_,
            "username": username,
            "shortcode": shortcode,
            "caption": caption,
            "timestamp": ts,
            "likes": likes,
            "comments": comments,
            "mediaType": "video" if "video" in media_type else "image",
            "displayUrl": display_url,
            "thumbnailUrl": thumb_url or display_url,
            "dimensions_width": width,
            "dimensions_height": height,
            "taggedUsers": tagged_users,
            "isAffiliate": is_affiliate,
            "isPaidPartnership": is_paid,
            "commentsDisabled": comments_disabled,
            "pinned": pinned,
            "locationId": loc_id,
            "locationName": loc_name,
            "locationSlug": loc_slug,
            "locationHasPublicPage": bool(loc_public) if loc_public is not None else None,
        }
        rows.append(row)
    return rows