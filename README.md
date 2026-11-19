# Auto-Clip & Publish (GitHub Actions)

Automatically finds a random long YouTube video, detects its best moments
(loud bursts, sudden sounds, motion, scene cuts — the same signals ClipIt Studio
uses), renders them as 9:16 Shorts plus a compilation, and uploads them to YouTube.
Runs on GitHub Actions, so it works even when your PC is off.

## Setup

1. Create a YouTube Data API v3 project + OAuth client (desktop app type).
2. Get a refresh token with `youtube.upload` scope (use
   `google-auth-oauthlib` flow or the YouTube OAuth playground).
3. Add repository secrets:
   - `YOUTUBE_API_KEY` (Data API key, for search)
   - `YOUTUBE_CLIENT_ID`
   - `YOUTUBE_CLIENT_SECRET`
   - `YOUTUBE_REFRESH_TOKEN`
4. (Optional) set `SEARCH_QUERY` default in the workflow or pass via dispatch.

## Run

- Manual: Actions tab -> "Clip & Publish" -> Run workflow.
- Scheduled: daily 06:00 UTC.

## Tuning

- `MAX_CLIPS`, `CLIP_SECONDS` via workflow_dispatch inputs.
- Detection thresholds in `scripts/detect.py`.

## Notes

- Free YouTube API quota: uploads cost 1600 units each; default daily quota 10k.
- Captions: each clip is transcribed with faster-whisper (AI speech-to-text) and
  burned in as subtitles.
- Titles/descriptions: generated with a FREE local AI model (Qwen2.5-0.5B via
  HuggingFace transformers, runs on CPU, no API key). Falls back to a
  deterministic heuristic if the model cannot be loaded.
- This reimplements ClipIt Studio's moment detection with open-source tools
  (ffmpeg + librosa + OpenCV) because ClipIt Studio has no API/headless mode.
