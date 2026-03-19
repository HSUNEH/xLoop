#!/usr/bin/env python3
"""Web search via duckduckgo-search with structured output."""

import json
import sys


VALID_TIME_VALUES = ("d", "w", "m", "y")


def parse_args(argv):
    """Parse query, --count N, --time d/w/m/y, and --json from argv."""
    args = argv[1:]
    count = 10
    json_output = False
    time_filter = None
    query_parts = []
    i = 0
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
        print(
            "Usage: web_search.py <query> [--count N] [--time d|w|m|y] [--json]",
            file=sys.stderr,
        )
        print(
            'Example: web_search.py "AI agents framework" --count 5 --time w',
            file=sys.stderr,
        )
        sys.exit(1)
    return query, count, json_output, time_filter


def search_web(query, count, timelimit=None):
    """Search the web using duckduckgo-search and return results."""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        print(
            "Error: duckduckgo-search not installed. "
            "Install with: pip install duckduckgo-search",
            file=sys.stderr,
        )
        sys.exit(1)

    time_labels = {"d": "past day", "w": "past week", "m": "past month", "y": "past year"}
    time_label = f", {time_labels[timelimit]}" if timelimit else ""
    print(
        f'Searching the web for: "{query}" (top {count} results{time_label})...\n',
        file=sys.stderr,
    )

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=count, timelimit=timelimit))
    except Exception as e:
        print(f"Error: Search failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not raw_results:
        print("No results found.", file=sys.stderr)
        sys.exit(0)

    results = []
    for r in raw_results:
        results.append({
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "snippet": r.get("body", ""),
            "source": r.get("href", "").split("/")[2] if r.get("href") else "",
        })

    return results


def print_results(results):
    """Print formatted search results."""
    divider = "\u2500" * 60

    for i, r in enumerate(results, 1):
        print(divider)
        print(f" {i:>2}. {r['title']}")
        print(f"     {r['source']}")
        print(f"     {r['url']}")
        if r["snippet"]:
            print(f"     {r['snippet'][:200]}")

    print(divider)


def print_json_results(results):
    """Print search results as JSON array to stdout."""
    print(json.dumps(results, ensure_ascii=False))


def main():
    query, count, json_output, time_filter = parse_args(sys.argv)
    results = search_web(query, count, timelimit=time_filter)
    if json_output:
        print_json_results(results)
    else:
        print_results(results)


if __name__ == "__main__":
    main()
