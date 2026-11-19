"""Render each detected moment to a 9:16 vertical short, plus a compilation."""
import json
import os
import subprocess
import sys

WORK = "work"
SOURCE = os.path.join(WORK, "source.mp4")
MOMENTS = os.path.join(WORK, "moments.json")
OUT = "out"
os.makedirs(OUT, exist_ok=True)


def render_clip(start, end, idx):
    dur = end - start
    out = os.path.join(OUT, f"clip_{idx:02d}.mp4")
    # blur-fill vertical 9:16
    vf = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-t", str(dur), "-i", SOURCE,
        "-filter_complex", vf,
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        out,
    ]
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print("Render failed for clip", idx)
        return None
    return out


def render_compilation(moment_list):
    # concat clips
    listfile = os.path.join(WORK, "concat.txt")
    clips = []
    for i in range(len(moment_list)):
        p = os.path.join(OUT, f"clip_{i:02d}.mp4")
        if os.path.exists(p):
            clips.append(p)
    if not clips:
        return None
    with open(listfile, "w") as f:
        for p in clips:
            f.write(f"file '{os.path.abspath(p)}'\n")
    out = os.path.join(OUT, "compilation.mp4")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
        "-c", "copy", out,
    ]
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print("Compilation failed")
        return None
    return out


def main():
    with open(MOMENTS) as f:
        data = json.load(f)
    moments = data["moments"]
    print(f"Rendering {len(moments)} clips...")
    for i, m in enumerate(moments):
        p = render_clip(m["start"], m["end"], i)
        print("  ", p)
    comp = render_compilation(moments)
    print("  compilation:", comp)


if __name__ == "__main__":
    main()
