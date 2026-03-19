#!/usr/bin/env python3
"""Add YouTube/web URLs to a NotebookLM notebook."""

import asyncio
import sys


def parse_args(argv: list[str]) -> tuple[str, list[str]]:
    """Parse notebook title and URLs from argv or stdin.

    Usage:
        notebooklm_add.py <title> <url1> [url2 ...]
        echo "url1\\nurl2" | notebooklm_add.py <title> --stdin
    """
    args = argv[1:]
    if not args:
        print(
            "Usage: notebooklm_add.py <notebook_title> <url1> [url2 ...]\n"
            "       notebooklm_add.py <notebook_title> --stdin",
            file=sys.stderr,
        )
        sys.exit(1)

    title = args[0]
    use_stdin = "--stdin" in args
    urls: list[str] = []

    if use_stdin:
        for line in sys.stdin:
            line = line.strip()
            if line and line.startswith("http"):
                urls.append(line)
    else:
        urls = [a for a in args[1:] if a.startswith("http")]

    if not urls:
        print("Error: No URLs provided.", file=sys.stderr)
        sys.exit(1)

    return title, urls


async def add_to_notebook(title: str, urls: list[str]) -> None:
    """Create a notebook and add URLs as sources."""
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        print(
            "Error: notebooklm-py not installed. "
            "Run: pip install notebooklm-py[browser]",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f'Creating notebook: "{title}"', file=sys.stderr)

    try:
        async with (await NotebookLMClient.from_storage()) as client:
            notebook = await client.notebooks.create(title)
            print(f"Notebook created: {notebook.id}", file=sys.stderr)

            added = 0
            failed = 0
            for url in urls:
                try:
                    source = await client.sources.add_url(
                        notebook.id, url, wait=True, wait_timeout=120.0
                    )
                    added += 1
                    source_title = getattr(source, "title", url)
                    print(f"  [{added}] {source_title}", file=sys.stderr)
                except Exception as e:
                    failed += 1
                    print(f"  [FAIL] {url}: {e}", file=sys.stderr)

            print(
                f"\nDone: {added} source(s) added, {failed} failed.",
                file=sys.stderr,
            )
            print(f"Notebook ID: {notebook.id}")
            print(
                f"Open: https://notebooklm.google.com/notebook/{notebook.id}"
            )
    except FileNotFoundError:
        print(
            "Error: Not authenticated. Run 'notebooklm login' first.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    title, urls = parse_args(sys.argv)
    asyncio.run(add_to_notebook(title, urls))


if __name__ == "__main__":
    main()
