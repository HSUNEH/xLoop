import hashlib
import json
import os
import time
from pathlib import Path

CACHE_DIR = Path(os.environ.get("SCOUT_CACHE_DIR", ".xloop/research/cache/opportunity-scout"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(source: str, query: str) -> str:
    raw = f"{source}:{query}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _cache_path(source: str, query: str) -> Path:
    return CACHE_DIR / f"{source}_{_cache_key(source, query)}.json"


def get_cached(source: str, query: str, max_age_days: int = 3) -> dict | None:
    path = _cache_path(source, query)
    if not path.exists():
        return None
    try:
        mtime = path.stat().st_mtime
        age_days = (time.time() - mtime) / 86400
        if age_days > max_age_days:
            return None
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_cache(source: str, query: str, data: dict) -> None:
    path = _cache_path(source, query)
    try:
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[cache] Failed to write cache: {e}")
