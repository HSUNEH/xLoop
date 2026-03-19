#!/usr/bin/env python3
"""Reddit and Hacker News search with structured output."""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime


REQUEST_TIMEOUT = 30
USER_AGENT = "xLoop/1.0"


VALID_TIME_VALUES = ("d", "w", "m", "y")


def parse_args(argv):
    """Parse platform, query, --count N, --subreddit, --min-score, --time, and --json from argv."""
    args = argv[1:]
    if not args:
        _print_usage()
        sys.exit(1)

    platform = args[0]
    if platform not in ("reddit", "hn", "all"):
        _print_usage()
        sys.exit(1)

    count = 10
    subreddit = None
    json_output = False
    min_score = 0
    time_filter = "year"
    query_parts = []
    i = 1
    while i < len(args):
        if args[i] == "--count" and i + 1 < len(args):
            try:
                count = int(args[i + 1])
            except ValueError:
                print(
                    f"Error: --count requires an integer, got '{args[i + 1]}'",
                    file=sys.stderr,
                )
                sys.exit(1)
            i += 2
        elif args[i] == "--subreddit" and i + 1 < len(args):
            subreddit = args[i + 1]
            i += 2
        elif args[i] == "--min-score" and i + 1 < len(args):
            try:
                min_score = int(args[i + 1])
            except ValueError:
                print(
                    f"Error: --min-score requires an integer, got '{args[i + 1]}'",
                    file=sys.stderr,
                )
                sys.exit(1)
            i += 2
        elif args[i] == "--time" and i + 1 < len(args):
            time_filter = args[i + 1]
            if time_filter not in VALID_TIME_VALUES:
                print(
                    f"Error: --time must be one of {VALID_TIME_VALUES}, got '{time_filter}'",
                    file=sys.stderr,
                )
                sys.exit(1)
            i += 2
        elif args[i] == "--json":
            json_output = True
            i += 1
        else:
            query_parts.append(args[i])
            i += 1

    query = " ".join(query_parts)
    if not query:
        _print_usage()
        sys.exit(1)

    return {
        "platform": platform,
        "query": query,
        "count": count,
        "subreddit": subreddit,
        "json_output": json_output,
        "min_score": min_score,
        "time": time_filter,
    }


def _print_usage():
    print(
        "Usage: community_search.py <reddit|hn|all> <query> [--count N] [--subreddit NAME]",
        file=sys.stderr,
    )
    print(
        "       [--min-score N] [--time d|w|m|y] [--json]",
        file=sys.stderr,
    )
    print(
        'Example: community_search.py reddit "AI agents" --count 5 --min-score 50 --time m',
        file=sys.stderr,
    )


def _fetch_json(url):
    """Fetch JSON from a URL with User-Agent header."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection failed: {e.reason}") from e
    except OSError as e:
        raise RuntimeError(f"Network error: {e}") from e


TIME_MAP_REDDIT = {"d": "day", "w": "week", "m": "month", "y": "year"}


def search_reddit(query, count, subreddit=None, time_filter="year"):
    """Search Reddit via old.reddit.com JSON API."""
    reddit_time = TIME_MAP_REDDIT.get(time_filter, time_filter)
    params = {
        "q": query,
        "sort": "relevance",
        "limit": min(count, 25),
        "t": reddit_time,
    }
    if subreddit:
        params["restrict_sr"] = "on"
        base = f"https://old.reddit.com/r/{urllib.parse.quote(subreddit)}/search.json"
    else:
        base = "https://old.reddit.com/search.json"

    url = f"{base}?{urllib.parse.urlencode(params)}"

    try:
        data = _fetch_json(url)
    except RuntimeError as e:
        print(f"Error: Reddit search failed: {e}", file=sys.stderr)
        return []

    results = []
    for child in data.get("data", {}).get("children", [])[:count]:
        post = child.get("data", {})
        created = post.get("created_utc")
        date = (
            datetime.utcfromtimestamp(created).strftime("%b %d, %Y")
            if created
            else "N/A"
        )
        results.append({
            "title": post.get("title", ""),
            "url": f"https://reddit.com{post.get('permalink', '')}",
            "subreddit": post.get("subreddit", ""),
            "score": post.get("score", 0),
            "comments": post.get("num_comments", 0),
            "date": date,
            "source": "reddit",
        })

    return results


TIME_MAP_HN_SECONDS = {"d": 86400, "w": 604800, "m": 2592000, "y": 31536000}


def search_hn(query, count, min_score=0, time_filter="year"):
    """Search Hacker News via Algolia API."""
    params = {
        "query": query,
        "tags": "story",
        "hitsPerPage": count,
    }
    numeric_filters = []
    if min_score > 0:
        numeric_filters.append(f"points>={min_score}")
    if time_filter in TIME_MAP_HN_SECONDS:
        cutoff = int(datetime.now().timestamp()) - TIME_MAP_HN_SECONDS[time_filter]
        numeric_filters.append(f"created_at_i>={cutoff}")
    if numeric_filters:
        params["numericFilters"] = ",".join(numeric_filters)
    url = f"https://hn.algolia.com/api/v1/search?{urllib.parse.urlencode(params)}"

    try:
        data = _fetch_json(url)
    except RuntimeError as e:
        print(f"Error: HN search failed: {e}", file=sys.stderr)
        return []

    results = []
    for hit in data.get("hits", [])[:count]:
        created = hit.get("created_at", "")
        try:
            date = datetime.fromisoformat(
                created.replace("Z", "+00:00")
            ).strftime("%b %d, %Y")
        except (ValueError, AttributeError):
            date = "N/A"

        story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
        results.append({
            "title": hit.get("title", ""),
            "url": story_url,
            "points": hit.get("points", 0),
            "comments": hit.get("num_comments", 0),
            "date": date,
            "source": "hn",
        })

    return results


def print_results(results):
    """Print formatted search results."""
    divider = "\u2500" * 60

    for i, r in enumerate(results, 1):
        print(divider)
        print(f" {i:>2}. [{r['source'].upper()}] {r['title']}")
        if r["source"] == "reddit":
            print(
                f"     r/{r['subreddit']}  \u00b7  "
                f"\u25b2 {r['score']}  \u00b7  {r['comments']} comments  \u00b7  {r['date']}"
            )
        else:
            print(
                f"     \u25b2 {r['points']}  \u00b7  "
                f"{r['comments']} comments  \u00b7  {r['date']}"
            )
        print(f"     {r['url']}")

    print(divider)


def print_json_results(results):
    """Print search results as JSON array to stdout."""
    print(json.dumps(results, ensure_ascii=False))


def main():
    opts = parse_args(sys.argv)
    platform = opts["platform"]
    query = opts["query"]
    count = opts["count"]

    label_parts = []
    if platform in ("reddit", "all"):
        label_parts.append("Reddit")
    if platform in ("hn", "all"):
        label_parts.append("Hacker News")
    print(
        f'Searching {" & ".join(label_parts)} for: "{query}" (top {count})...\n',
        file=sys.stderr,
    )

    min_score = opts["min_score"]
    time_filter = opts["time"]

    results = []
    if platform in ("reddit", "all"):
        fetch_count = count * 2 if min_score > 0 else count
        reddit_results = search_reddit(query, fetch_count, opts["subreddit"], time_filter)
        if min_score > 0:
            reddit_results = [r for r in reddit_results if r["score"] >= min_score]
        results.extend(reddit_results[:count])
    if platform in ("hn", "all"):
        results.extend(search_hn(query, count, min_score, time_filter))

    if not results:
        print("No results found.", file=sys.stderr)
        sys.exit(0)

    if opts["json_output"]:
        print_json_results(results)
    else:
        print_results(results)


if __name__ == "__main__":
    main()
