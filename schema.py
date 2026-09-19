"""
Common data format for FootprintAI.

All discovered accounts are represented as candidate dictionaries following this schema.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List


# Candidate schema - the standard format for all discovered accounts
CANDIDATE_SCHEMA = {
    "platform": "github",  # github / linkedin / x / youtube / instagram / web
    "username": "tech_guru99",
    "display_name": "Johnathan Doe",
    "profile_url": "https://github.com/tech_guru99",
    "bio": "ML engineer. Building NLP tools.",
    "photo_url": "https://avatars.githubusercontent.com/u/123",
    "links": ["https://johndoe.dev"],  # URLs found on the profile
    "location": "Hyderabad",
    "extra": {"repos": [...], "orgs": [...]},  # anything else useful
    "retrieved_at": "2026-01-15T10:32:00Z"
}


def make_candidate(
    platform: str = "",
    username: str = "",
    display_name: str = "",
    profile_url: str = "",
    bio: str = "",
    photo_url: str = "",
    links: List[str] = None,
    location: str = "",
    extra: Dict[str, Any] = None,
    retrieved_at: str = None
) -> Dict[str, Any]:
    """
    Create a candidate dictionary with default values.
    
    Args:
        platform: Platform name (github, linkedin, x, youtube, instagram, web)
        username: Username/handle on the platform
        display_name: Full display name
        profile_url: URL to the profile
        bio: Profile bio/description
        photo_url: URL to profile photo
        links: List of external URLs found on profile
        location: Geographic location
        extra: Additional platform-specific data
        retrieved_at: ISO 8601 timestamp (defaults to current UTC time)
    
    Returns:
        A candidate dictionary following the standard schema
    """
    if links is None:
        links = []
    if extra is None:
        extra = {}
    if retrieved_at is None:
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return {
        "platform": platform,
        "username": username,
        "display_name": display_name,
        "profile_url": profile_url,
        "bio": bio,
        "photo_url": photo_url,
        "links": links,
        "location": location,
        "extra": extra,
        "retrieved_at": retrieved_at
    }
