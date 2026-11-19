"""Upload rendered clips to YouTube via Data API v3."""
import json
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

OUT = "out"


def get_service():
    creds = Credentials(
        None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    return build("youtube", "v3", credentials=creds)


def upload_file(youtube, path, title, description, tags=None):
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": (tags or [])[:15],
            "categoryId": "20",  # Gaming
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(path, chunksize=-1, resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"  upload {int(status.progress() * 100)}%")
    print("  uploaded:", response.get("id"))
    return response.get("id")


def main():
    with open("chosen_video.json") as f:
        v = json.load(f)
    source_title = v.get("title", "Long video")
    meta = {}
    meta_path = os.path.join("work", "meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
    youtube = get_service()

    files = sorted(
        f for f in os.listdir(OUT) if f.endswith(".mp4")
    )
    for f in files:
        path = os.path.join(OUT, f)
        if f.startswith("clip_"):
            idx = int(f.replace("clip_", "").replace(".mp4", ""))
            titles = meta.get("titles", [])
            title = titles[idx] if idx < len(titles) else f"Best moment #{idx+1} - {source_title}"
        elif f == "compilation.mp4":
            title = meta.get("compilation_title", f"Best moments compilation - {source_title}")
        else:
            title = f"{source_title} - clip"
        desc = meta.get("description", f"Auto-clipped best moment from: {source_title}\nSource: {v.get('url')}\n\nGenerated automatically.")
        tags = meta.get("tags", [])
        print("Uploading", f, "tags:", tags)
        try:
            upload_file(youtube, path, title, desc, tags=tags)
        except Exception as e:
            print("Upload failed:", e)


if __name__ == "__main__":
    main()
