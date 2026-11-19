"""Orchestrate the whole pipeline."""
import os
import subprocess
import sys

def run(script):
    r = subprocess.run([sys.executable, script])
    if r.returncode != 0:
        print(f"Step failed: {script}")
        sys.exit(r.returncode)

def main():
    run("scripts/find_video.py")
    run("scripts/download.py")
    run("scripts/detect.py")
    run("scripts/render.py")
    # AI captions (Whisper) burned into each clip
    run("scripts/captions.py")
    # AI-generated titles/descriptions (uses OpenAI if OPENAI_API_KEY present)
    run("scripts/ai_meta.py")
    # upload only if creds present
    if os.environ.get("YOUTUBE_REFRESH_TOKEN"):
        run("scripts/upload_youtube.py")
    else:
        print("No YouTube creds; skipping upload.")

if __name__ == "__main__":
    main()
