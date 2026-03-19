#!/usr/bin/env python3
"""YouTube search via yt-dlp with structured output."""

import io
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta

def _ensure_utf8():
    """Force UTF-8 output on Windows to handle emoji in video titles."""
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )


def _parse_int_option(args, i, name):
    """Parse an integer option value, exit on error."""
    try:
        return int(args[i + 1])
    except ValueError:
        print(
            f"Error: {name} requires an integer, got '{args[i + 1]}'",
            file=sys.stderr,
        )
        sys.exit(1)


def parse_args(argv):
    """Parse query, options, and filters from argv."""
    args = argv[1:]
    count = 20
    months = 6
    json_output = False
    filters = {
        "min_views": 0,
        "min_duration": 0,
        "max_duration": 0,
        "channels": [],
        "exclude_channels": [],
    }
    query_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--count" and i + 1 < len(args):
            count = _parse_int_option(args, i, "--count")
            i += 2
        elif args[i] == "--months" and i + 1 < len(args):
            months = _parse_int_option(args, i, "--months")
            i += 2
        elif args[i] == "--no-date-filter":
            months = 0
            i += 1
        elif args[i] == "--json":
            json_output = True
            i += 1
        elif args[i] == "--min-views" and i + 1 < len(args):
            filters["min_views"] = _parse_int_option(args, i, "--min-views")
            i += 2
        elif args[i] == "--min-duration" and i + 1 < len(args):
            filters["min_duration"] = _parse_int_option(args, i, "--min-duration")
            i += 2
        elif args[i] == "--max-duration" and i + 1 < len(args):
            filters["max_duration"] = _parse_int_option(args, i, "--max-duration")
            i += 2
        elif args[i] == "--channel" and i + 1 < len(args):
            filters["channels"].append(args[i + 1])
            i += 2
        elif args[i] == "--exclude-channel" and i + 1 < len(args):
            filters["exclude_channels"].append(args[i + 1])
            i += 2
        else:
            query_parts.append(args[i])
            i += 1
    query = " ".join(query_parts)
    if not query:
        print(
            "Usage: yt_search.py <query> [--count N] [--months N] [--no-date-filter] [--json]",
            file=sys.stderr,
        )
        print(
            "  Filters: [--min-views N] [--min-duration M] [--max-duration M]",
            file=sys.stderr,
        )
        print(
            "           [--channel NAME] [--exclude-channel NAME]",
            file=sys.stderr,
        )
        print(
            "Example: yt_search.py claude code tutorial --count 5 --min-views 1000",
            file=sys.stderr,
        )
        sys.exit(1)
    return query, count, months, json_output, filters


def format_subscribers(n):
    """Format subscriber count as human-readable (e.g., 45.2K, 1.2M)."""
    if n is None:
        return "N/A"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def format_views(n):
    """Format view count with commas."""
    if n is None:
        return "N/A"
    return f"{n:,}"


def format_duration(info):
    """Extract human-readable duration from yt-dlp info."""
    if info.get("duration_string"):
        return info["duration_string"]
    dur = info.get("duration")
    if dur is None:
        return "N/A"
    dur = int(dur)
    hours, remainder = divmod(dur, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_date(raw):
    """Convert YYYYMMDD to human-readable date (e.g., Jan 10, 2026)."""
    if not raw or len(raw) != 8:
        return "N/A"
    try:
        dt = datetime.strptime(raw, "%Y%m%d")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"


def get_cutoff_date(months):
    """Get the cutoff date as YYYYMMDD string, N months ago from today."""
    if months <= 0:
        return None
    cutoff = datetime.now() - timedelta(days=months * 30)
    return cutoff.strftime("%Y%m%d")


def _has_active_filters(filters):
    """Check if any post-search filter is active."""
    return (
        filters["min_views"] > 0
        or filters["min_duration"] > 0
        or filters["max_duration"] > 0
        or filters["channels"]
        or filters["exclude_channels"]
    )


def filter_videos(videos, filters):
    """Apply post-search filters: views, duration, channel."""
    result = []
    for v in videos:
        view_count = v.get("view_count")
        if filters["min_views"] > 0 and view_count is not None:
            if view_count < filters["min_views"]:
                continue

        duration = v.get("duration")
        if filters["min_duration"] > 0 and duration is not None:
            if duration < filters["min_duration"] * 60:
                continue
        if filters["max_duration"] > 0 and duration is not None:
            if duration > filters["max_duration"] * 60:
                continue

        channel = (v.get("channel") or v.get("uploader") or "").lower()
        if filters["channels"]:
            allowed = [c.lower() for c in filters["channels"]]
            if channel not in allowed:
                continue
        if filters["exclude_channels"]:
            excluded = [c.lower() for c in filters["exclude_channels"]]
            if channel in excluded:
                continue

        result.append(v)
    return result


def search_youtube(query, count, months, filters=None):
    """Run yt-dlp search and return parsed video list."""
    if filters is None:
        filters = {
            "min_views": 0, "min_duration": 0, "max_duration": 0,
            "channels": [], "exclude_channels": [],
        }

    if not shutil.which("yt-dlp"):
        print(
            "Error: yt-dlp not found on PATH. Install with: pip install yt-dlp",
            file=sys.stderr,
        )
        sys.exit(1)

    has_filters = _has_active_filters(filters)
    base_multiplier = 2 if months > 0 else 1
    fetch_count = count * (base_multiplier + (1 if has_filters else 0))
    search_query = f"ytsearch{fetch_count}:{query}"
    cmd = [
        "yt-dlp",
        search_query,
        "--dump-json",
        "--no-download",
        "--no-warnings",
        "--quiet",
    ]

    date_label = f", last {months} months" if months > 0 else ""
    print(
        f'Searching YouTube for: "{query}" (top {count} results{date_label})...\n',
        file=sys.stderr,
    )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        print("Error: Search timed out after 120 seconds.", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0 and not result.stdout.strip():
        print(f"Error: yt-dlp failed:\n{result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    videos = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        try:
            videos.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not videos:
        print("No results found.", file=sys.stderr)
        sys.exit(0)

    cutoff = get_cutoff_date(months)
    if cutoff:
        filtered = [
            v for v in videos if (v.get("upload_date") or "00000000") >= cutoff
        ]
        skipped = len(videos) - len(filtered)
        videos = filtered
        if skipped > 0:
            print(
                f"(Filtered out {skipped} video(s) older than {months} months)\n",
                file=sys.stderr,
            )

    if not videos:
        print(f"No results found within the last {months} months.", file=sys.stderr)
        sys.exit(0)

    if has_filters:
        before_filter = len(videos)
        videos = filter_videos(videos, filters)
        skipped_by_filter = before_filter - len(videos)
        if skipped_by_filter > 0:
            print(
                f"(Filtered out {skipped_by_filter} video(s) by search filters)\n",
                file=sys.stderr,
            )
        if not videos:
            print(
                "No results match the given filters. Try relaxing filter criteria.",
                file=sys.stderr,
            )
            sys.exit(0)

    return videos[:count]


def print_results(videos):
    """Print formatted search results."""
    divider = "\u2500" * 60

    for i, info in enumerate(videos, 1):
        title = info.get("title", "Unknown Title")
        channel = info.get("channel", info.get("uploader", "Unknown"))
        views = info.get("view_count")
        subs = info.get("channel_follower_count")
        duration = format_duration(info)
        date = format_date(info.get("upload_date", ""))
        video_id = info.get("id", "")
        url = f"https://youtube.com/watch?v={video_id}" if video_id else "N/A"

        views_str = format_views(views)
        subs_str = format_subscribers(subs)
        meta = (
            f"{channel} ({subs_str} subs)  \u00b7  "
            f"{views_str} views  \u00b7  {duration}  \u00b7  {date}"
        )

        print(divider)
        print(f" {i:>2}. {title}")
        print(f"     {meta}")
        print(f"     {url}")

    print(divider)


def print_json_results(videos):
    """Print search results as JSON array to stdout."""
    results = []
    for info in videos:
        video_id = info.get("id", "")
        results.append({
            "url": f"https://youtube.com/watch?v={video_id}" if video_id else None,
            "title": info.get("title", "Unknown Title"),
            "channel": info.get("channel", info.get("uploader", "Unknown")),
            "views": info.get("view_count"),
            "date": format_date(info.get("upload_date", "")),
        })
    print(json.dumps(results, ensure_ascii=False))


def main():
    query, count, months, json_output, filters = parse_args(sys.argv)
    videos = search_youtube(query, count, months, filters)
    if json_output:
        print_json_results(videos)
    else:
        print_results(videos)


if __name__ == "__main__":
    _ensure_utf8()
    main()
