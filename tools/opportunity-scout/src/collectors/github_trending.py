import os
import time
import requests
from bs4 import BeautifulSoup

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def _handle_rate_limit(resp: requests.Response) -> None:
    remaining = resp.headers.get("X-RateLimit-Remaining")
    if remaining is not None and int(remaining) < 5:
        reset_at = int(resp.headers.get("X-RateLimit-Reset", 0))
        wait = max(reset_at - int(time.time()), 1)
        print(f"[github] Rate limit near, sleeping {wait}s")
        time.sleep(min(wait, 60))


def collect_trending(language: str = None, since: str = "weekly") -> dict:
    print(f"Fetching GitHub trending repos (language={language}, since={since})")
    result = {"repos": []}

    url = "https://github.com/trending"
    if language:
        url += f"/{language}"
    params = {"since": since}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[github] Failed to fetch trending page: {e}")
        return result

    soup = BeautifulSoup(resp.text, "lxml")
    articles = soup.select("article.Box-row")

    for article in articles:
        repo = {}

        h2 = article.select_one("h2 a")
        if h2:
            full_name = h2.get("href", "").strip("/")
            repo["full_name"] = full_name
            parts = full_name.split("/")
            repo["owner"] = parts[0] if len(parts) > 0 else ""
            repo["name"] = parts[1] if len(parts) > 1 else ""

        desc_p = article.select_one("p")
        repo["description"] = desc_p.get_text(strip=True) if desc_p else ""

        lang_span = article.select_one("[itemprop='programmingLanguage']")
        repo["language"] = lang_span.get_text(strip=True) if lang_span else ""

        stars_link = article.select("a.Link--muted")
        repo["stars"] = ""
        repo["forks"] = ""
        if len(stars_link) >= 1:
            repo["stars"] = stars_link[0].get_text(strip=True).replace(",", "")
        if len(stars_link) >= 2:
            repo["forks"] = stars_link[1].get_text(strip=True).replace(",", "")

        period_stars = article.select_one("span.d-inline-block.float-sm-right")
        repo["period_stars"] = period_stars.get_text(strip=True) if period_stars else ""

        result["repos"].append(repo)

    print(f"[github] Found {len(result['repos'])} trending repos.")
    return result


def collect_repo_stats(query: str) -> dict:
    print(f"Fetching GitHub repo stats for query: '{query}'")
    result = {"repos": [], "total_count": 0}

    url = f"{GITHUB_API}/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 20}

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=15)
        _handle_rate_limit(resp)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[github] Repo search failed: {e}")
        return result

    result["total_count"] = data.get("total_count", 0)

    for item in data.get("items", []):
        result["repos"].append({
            "full_name": item.get("full_name", ""),
            "description": item.get("description", ""),
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "open_issues": item.get("open_issues_count", 0),
            "language": item.get("language", ""),
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
            "pushed_at": item.get("pushed_at", ""),
            "topics": item.get("topics", []),
        })

    print(f"[github] Found {len(result['repos'])} repos for '{query}'.")
    return result
