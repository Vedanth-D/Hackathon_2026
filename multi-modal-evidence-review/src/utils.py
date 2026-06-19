"""Utility helpers."""

import hashlib
import json
import re
import time
from pathlib import Path
from typing import List

from src.config import CACHE_DIR, REQUESTS_PER_MINUTE


def parse_image_paths(image_paths: str) -> List[str]:
    return [p.strip() for p in image_paths.split(";") if p.strip()]


def image_id_from_path(path: str) -> str:
    return Path(path).stem


def normalize_issue_family(issue_type: str) -> str:
    """Map issue types to evidence requirement families."""
    mapping = {
        "dent": "dent or scratch",
        "scratch": "dent or scratch",
        "crack": "crack",
        "glass_shatter": "glass shatter",
        "broken_part": "broken part",
        "missing_part": "missing part",
        "torn_packaging": "torn packaging",
        "crushed_packaging": "crushed packaging",
        "water_damage": "water damage",
        "stain": "stain",
    }
    return mapping.get(issue_type, issue_type)


class RateLimiter:
    """Simple token-bucket style rate limiter for API calls."""

    def __init__(self, requests_per_minute: int = REQUESTS_PER_MINUTE):
        self.interval = 60.0 / max(requests_per_minute, 1)
        self.last_call = 0.0

    def wait(self):
        elapsed = time.time() - self.last_call
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self.last_call = time.time()


class UsageTracker:
    """Track API usage for operational reporting."""

    def __init__(self):
        self.model_calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.images_processed = 0
        self.cache_hits = 0

    def record(self, input_tokens: int = 0, output_tokens: int = 0, images: int = 0):
        self.model_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.images_processed += images

    def to_dict(self) -> dict:
        return {
            "model_calls": self.model_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "images_processed": self.images_processed,
            "cache_hits": self.cache_hits,
        }


def cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode()).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def read_cache(key: str) -> dict | None:
    path = cache_path(key)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def write_cache(key: str, data: dict):
    path = cache_path(key)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def join_flags(flags: List[str]) -> str:
    unique = []
    seen = set()
    for f in flags:
        f = f.strip()
        if f and f not in seen:
            unique.append(f)
            seen.add(f)
    if not unique:
        return "none"
    if "none" in unique and len(unique) > 1:
        unique = [f for f in unique if f != "none"]
    return ";".join(unique) if unique else "none"


def closest_allowed(value: str, allowed: set) -> str:
    if value in allowed:
        return value
    value_lower = value.lower().replace(" ", "_").replace("-", "_")
    if value_lower in allowed:
        return value_lower
    for a in allowed:
        if a in value_lower or value_lower in a:
            return a
    return "unknown"
