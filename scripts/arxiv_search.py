#!/usr/bin/env python3
"""arXiv paper search with structured output."""

import json
import sys


def parse_args(argv):
    """Parse query, --count N, --sort (relevance|date), and --json from argv."""
    args = argv[1:]
    count = 10
    sort = "relevance"
    json_output = False
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
        elif args[i] == "--sort" and i + 1 < len(args):
            if args[i + 1] not in ("relevance", "date"):
                print(
                    f"Error: --sort must be 'relevance' or 'date', got '{args[i + 1]}'",
                    file=sys.stderr,
                )
                sys.exit(1)
            sort = args[i + 1]
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
            "Usage: arxiv_search.py <query> [--count N] [--sort relevance|date] [--json]",
            file=sys.stderr,
        )
        print(
            'Example: arxiv_search.py "transformer attention" --count 5 --sort date',
            file=sys.stderr,
        )
        sys.exit(1)
    return query, count, sort, json_output


def search_arxiv(query, count, sort):
    """Search arXiv and return parsed paper list."""
    try:
        import arxiv
    except ImportError:
        print(
            "Error: arxiv not installed. Install with: pip install arxiv",
            file=sys.stderr,
        )
        sys.exit(1)

    sort_criterion = (
        arxiv.SortCriterion.SubmittedDate
        if sort == "date"
        else arxiv.SortCriterion.Relevance
    )

    print(
        f'Searching arXiv for: "{query}" (top {count}, sort by {sort})...\n',
        file=sys.stderr,
    )

    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=count,
            sort_by=sort_criterion,
        )
        raw_results = list(client.results(search))
    except Exception as e:
        print(f"Error: arXiv search failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not raw_results:
        print("No results found.", file=sys.stderr)
        sys.exit(0)

    results = []
    for r in raw_results:
        results.append({
            "title": r.title,
            "url": r.entry_id,
            "pdf_url": r.pdf_url,
            "authors": ", ".join(a.name for a in r.authors[:5])
            + (" et al." if len(r.authors) > 5 else ""),
            "abstract": r.summary[:200].replace("\n", " ") + ("..." if len(r.summary) > 200 else ""),
            "date": r.published.strftime("%b %d, %Y") if r.published else "N/A",
            "categories": ", ".join(r.categories),
        })

    return results


def print_results(results):
    """Print formatted search results."""
    divider = "\u2500" * 60

    for i, r in enumerate(results, 1):
        print(divider)
        print(f" {i:>2}. {r['title']}")
        print(f"     {r['authors']}  \u00b7  {r['date']}")
        print(f"     {r['categories']}")
        print(f"     {r['pdf_url']}")
        print(f"     {r['abstract']}")

    print(divider)


def print_json_results(results):
    """Print search results as JSON array to stdout."""
    print(json.dumps(results, ensure_ascii=False))


def main():
    query, count, sort, json_output = parse_args(sys.argv)
    results = search_arxiv(query, count, sort)
    if json_output:
        print_json_results(results)
    else:
        print_results(results)


if __name__ == "__main__":
    main()
