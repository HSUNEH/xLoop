from src.cache.cache_manager import get_cached, save_cache
from src.collectors.google_trends import collect_trends
from src.collectors.github_trending import collect_trending, collect_repo_stats
from src.collectors.youtube_search import collect_youtube_trends

DOMAIN_SOURCES = {
    "tech": ["google_trends", "github", "youtube"],
    "saas": ["google_trends", "github", "youtube"],
    "dev_tools": ["google_trends", "github"],
    "content": ["google_trends", "youtube"],
    "auto": ["google_trends", "github", "youtube"],
}


def collect_all(query: str, domain: str = "auto") -> dict:
    sources = DOMAIN_SOURCES.get(domain, DOMAIN_SOURCES["auto"])
    results = {}

    if "google_trends" in sources:
        cached = get_cached("google_trends", query)
        if cached:
            print("[collect_all] Using cached Google Trends data.")
            results["google_trends"] = cached
        else:
            try:
                data = collect_trends([query])
                results["google_trends"] = data
                save_cache("google_trends", query, data)
            except Exception as e:
                print(f"[collect_all] Google Trends failed: {e}")
                results["google_trends"] = {}

    if "github" in sources:
        cached_trending = get_cached("github_trending", query)
        cached_repos = get_cached("github_repos", query)

        if cached_trending:
            print("[collect_all] Using cached GitHub trending data.")
            results["github_trending"] = cached_trending
        else:
            try:
                data = collect_trending()
                results["github_trending"] = data
                save_cache("github_trending", query, data)
            except Exception as e:
                print(f"[collect_all] GitHub trending failed: {e}")
                results["github_trending"] = {}

        if cached_repos:
            print("[collect_all] Using cached GitHub repo stats.")
            results["github_repos"] = cached_repos
        else:
            try:
                data = collect_repo_stats(query)
                results["github_repos"] = data
                save_cache("github_repos", query, data)
            except Exception as e:
                print(f"[collect_all] GitHub repo search failed: {e}")
                results["github_repos"] = {}

    if "youtube" in sources:
        cached = get_cached("youtube", query)
        if cached:
            print("[collect_all] Using cached YouTube data.")
            results["youtube"] = cached
        else:
            try:
                data = collect_youtube_trends(query)
                results["youtube"] = data
                save_cache("youtube", query, data)
            except Exception as e:
                print(f"[collect_all] YouTube search failed: {e}")
                results["youtube"] = {}

    return results
