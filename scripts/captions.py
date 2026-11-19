"""Generate AI captions (Whisper) and burn them into each rendered clip."""
import json
import os
import subprocess
import sys

OUT = "out"

try:
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except Exception:
    HAS_WHISPER = False


def transcribe(clip_path):
    if not HAS_WHISPER:
        return None
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(clip_path, beam_size=1)
    segs = []
    for s in segments:
        segs.append({"start": s.start, "end": s.end, "text": s.text.strip()})
    return segs


def write_srt(segs, srt_path):
    def fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{fmt(s['start'])} --> {fmt(s['end'])}\n{s['text']}\n\n")


def burn(clip_path, srt_path):
    out = clip_path.replace(".mp4", "_cap.mp4")
    # escape path for ffmpeg subtitles filter
    sp = srt_path.replace("\\", "/").replace(":", "\\:")
    cmd = [
        "ffmpeg", "-y", "-i", clip_path,
        "-vf", f"subtitles={sp}:force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2'",
        "-c:a", "copy", out,
    ]
    r = subprocess.run(cmd)
    if r.returncode == 0 and os.path.exists(out):
        os.replace(out, clip_path)
        return True
    return False


def main():
    clips = sorted(f for f in os.listdir(OUT) if f.endswith(".mp4"))
    for c in clips:
        path = os.path.join(OUT, c)
        print("Captioning", c)
        segs = transcribe(path)
        if not segs:
            print("  no transcription (whisper unavailable or no speech)")
            continue
        srt = os.path.join(OUT, c.replace(".mp4", ".srt"))
        write_srt(segs, srt)
        ok = burn(path, srt)
        print("  burned:", ok)


if __name__ == "__main__":
    main()
