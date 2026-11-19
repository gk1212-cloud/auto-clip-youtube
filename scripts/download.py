"""Download the chosen video with yt-dlp."""
import json
import os
import subprocess
import sys

os.makedirs("out", exist_ok=True)
os.makedirs("work", exist_ok=True)

with open("chosen_video.json") as f:
    v = json.load(f)

out_path = "work/source.mp4"
cmd = [
    "yt-dlp",
    "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
    "--merge-output-format", "mp4",
    "-o", out_path,
    v["url"],
]
print("Downloading:", v["url"])
r = subprocess.run(cmd)
if r.returncode != 0:
    print("Download failed")
    sys.exit(1)
print("Saved to", out_path)
