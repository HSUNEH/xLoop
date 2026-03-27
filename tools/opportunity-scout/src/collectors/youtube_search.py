import json
import re
import requests


def collect_youtube_trends(query: str, max_results: int = 10) -> dict:
    print(f"Fetching YouTube results for: '{query}'")
    result = {"videos": []}

    url = "https://www.youtube.com/results"
    params = {"search_query": query}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[youtube] Failed to fetch results: {e}")
        return result

    match = re.search(r"var ytInitialData\s*=\s*({.*?});\s*</script>", resp.text)
    if not match:
        match = re.search(r"ytInitialData\s*=\s*({.*?});\s*", resp.text)
    if not match:
        print("[youtube] Could not extract ytInitialData from page.")
        return result

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"[youtube] Failed to parse JSON: {e}")
        return result

    try:
        contents = (
            data["contents"]["twoColumnSearchResultsRenderer"]
            ["primaryContents"]["sectionListRenderer"]["contents"]
        )
    except (KeyError, TypeError):
        print("[youtube] Unexpected page structure.")
        return result

    videos = []
    for section in contents:
        items = (
            section.get("itemSectionRenderer", {})
            .get("contents", [])
        )
        for item in items:
            renderer = item.get("videoRenderer")
            if not renderer:
                continue

            title_runs = renderer.get("title", {}).get("runs", [])
            title = title_runs[0].get("text", "") if title_runs else ""

            view_text = renderer.get("viewCountText", {}).get("simpleText", "")

            channel_runs = (
                renderer.get("ownerText", {}).get("runs", [])
            )
            channel = channel_runs[0].get("text", "") if channel_runs else ""

            published = renderer.get("publishedTimeText", {}).get("simpleText", "")

            desc_snippets = renderer.get("detailedMetadataSnippets", [])
            description = ""
            if desc_snippets:
                snippet_runs = desc_snippets[0].get("snippetText", {}).get("runs", [])
                description = "".join(r.get("text", "") for r in snippet_runs)

            video_id = renderer.get("videoId", "")
            length_text = renderer.get("lengthText", {}).get("simpleText", "")

            videos.append({
                "title": title,
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
                "views": view_text,
                "channel": channel,
                "published": published,
                "description": description,
                "length": length_text,
            })

            if len(videos) >= max_results:
                break
        if len(videos) >= max_results:
            break

    result["videos"] = videos
    print(f"[youtube] Found {len(videos)} videos.")
    return result
