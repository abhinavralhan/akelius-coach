"""Top 3 YouTube videos per topic, from the official YouTube Data API, each confirmed via oEmbed.
Run: YOUTUBE_API_KEY=... python -m coach.videos [concept-id ...]   (all sheets if none given)
Titles and channels come from YouTube, never from the model; videos are labelled as not reviewed by us."""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date

from coach import sheet

SEARCH = "https://www.googleapis.com/youtube/v3/search"
OEMBED = "https://www.youtube.com/oembed"


def _get_json(url):
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r)


def top_videos(title, grade, key, get=_get_json, n=3):
    q = urllib.parse.urlencode({"part": "snippet", "type": "video", "maxResults": n + 2, "q": f"{title} grade {grade} math",
                                "safeSearch": "strict", "videoEmbeddable": "true", "relevanceLanguage": "en", "key": key})
    found = []
    for item in get(f"{SEARCH}?{q}").get("items", []):
        vid = item.get("id", {}).get("videoId", "")
        if not re.fullmatch(r"[\w-]{11}", vid):
            continue
        url = f"https://www.youtube.com/watch?v={vid}"
        try:  # confirms the video exists and is public; its title/author are YouTube's own
            o = get(f"{OEMBED}?{urllib.parse.urlencode({'url': url, 'format': 'json'})}")
        except Exception:
            continue
        found.append({"title": o["title"], "channel": o["author_name"], "url": url})
        if len(found) == n:
            break
    return found


def attach(concept_ids, key):
    grades = {m["concept"]: m["grade"] for m in __import__("yaml").safe_load(
        (sheet.ROOT / "curriculum/standards/ccss.yaml").read_text())["map"]}
    for cid in concept_ids:
        path = sheet.CONTENT / f"{cid}.json"
        if not path.exists():
            continue
        s = json.loads(path.read_text())
        s["videos"] = top_videos(sheet.CONCEPTS[cid]["title"], grades[cid], key)
        s["meta"]["videos_fetched"] = date.today().isoformat()
        sheet.save(cid, s)
        print(cid, len(s["videos"]), "videos")


if __name__ == "__main__":
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        sys.exit("Set YOUTUBE_API_KEY (YouTube Data API v3, free quota: ~100 topics/day at 100 units per search).")
    attach(sys.argv[1:] or sorted(sheet.CONCEPTS), key)
