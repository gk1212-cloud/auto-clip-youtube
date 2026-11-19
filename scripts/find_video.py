"""Find a random long YouTube video by search query."""
import os
import random
import json
import urllib.request
import urllib.parse

API_KEY = os.environ.get("YOUTUBE_API_KEY", "")


def search_long_videos(query, max_results=25):
    if not API_KEY:
        # Fallback: use yt-dlp search
        return search_via_ytdlp(query, max_results)
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoDuration": "long",  # >20 min
        "maxResults": max_results,
        "key": API_KEY,
    }
    url = "https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as r:
        data = json.load(r)
    out = []
    for item in data.get("items", []):
        vid = item["id"].get("videoId")
        if vid:
            out.append({
                "id": vid,
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "url": f"https://www.youtube.com/watch?v={vid}",
            })
    return out


def search_via_ytdlp(query, max_results=25):
    import subprocess
    cmd = [
        "yt-dlp", f"ytsearch{max_results}:{query}",
        "--dump-json", "--flat-playlist", "--no-download",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = []
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        dur = d.get("duration") or 0
        if dur and dur < 600:  # at least 10 min
            continue
        vid = d.get("id")
        if vid:
            out.append({
                "id": vid,
                "title": d.get("title", ""),
                "channel": d.get("uploader", ""),
                "url": d.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}",
                "duration": dur,
            })
    return out


def pick_random(query):
    vids = search_long_videos(query)
    if not vids:
        raise RuntimeError("No long videos found for query: " + query)
    return random.choice(vids)


if __name__ == "__main__":
    q = os.environ.get("SEARCH_QUERY", "gameplay highlights")
    v = pick_random(q)
    print(json.dumps(v))
    with open("chosen_video.json", "w") as f:
        json.dump(v, f)
