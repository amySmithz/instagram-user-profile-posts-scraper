# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

def extract_tagged_from_raw(post_raw: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract tagged users from multiple possible shapes.
    Supports mock shape: post_raw["tags"] -> [{"username":, "fullName":, "profilePicUrl":}]
    And IG-like shapes under "edge_media_to_tagged_user".
    """
    # Already normalized?
    if isinstance(post_raw.get("taggedUsers"), list):
        return post_raw["taggedUsers"]

    # IG-like edge structure
    edge = (
        post_raw.get("edge_media_to_tagged_user")
        or post_raw.get("node", {}).get("edge_media_to_tagged_user")
        or {}
    )
    if isinstance(edge, dict) and "edges" in edge:
        results = []
        for e in edge.get("edges", []):
            user = e.get("node", {}).get("user", {})
            if not user:
                user = e.get("node", {})
            results.append(
                {
                    "fullName": user.get("full_name") or user.get("fullName") or "",
                    "profilePicUrl": user.get("profile_pic_url") or user.get("profilePicUrl") or "",
                    "username": user.get("username") or "",
                }
            )
        return results

    # Simple mock structure
    if isinstance(post_raw.get("tags"), list):
        res = []
        for t in post_raw["tags"]:
            res.append(
                {
                    "fullName": t.get("fullName", ""),
                    "profilePicUrl": t.get("profilePicUrl", ""),
                    "username": t.get("username", ""),
                }
            )
        return res

    return []