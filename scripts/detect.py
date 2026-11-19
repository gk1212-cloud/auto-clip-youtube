"""Detect best moments in a long video.

Approximates ClipIt Studio's approach: loud bursts, sudden sounds, motion, scene cuts.
Produces work/moments.json: list of {start, end, score}.
"""
import json
import os
import subprocess
import sys

import cv2
import librosa
import numpy as np
from scipy.signal import find_peaks

WORK = "work"
SOURCE = os.path.join(WORK, "source.mp4")
AUDIO = os.path.join(WORK, "audio.wav")
MOMENTS = os.path.join(WORK, "moments.json")

CLIP_SECONDS = int(os.environ.get("CLIP_SECONDS", "60"))
CLIP_SECONDS = max(45, min(70, CLIP_SECONDS))
MAX_CLIPS = int(os.environ.get("MAX_CLIPS", "3"))


def extract_audio():
    subprocess.run(
        ["ffmpeg", "-y", "-i", SOURCE, "-vn", "-ac", "1", "-ar", "22050", AUDIO],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def audio_scores():
    y, sr = librosa.load(AUDIO, sr=22050)
    hop = 512
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop)[0]
    # spectral flux (sudden sounds)
    spec = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    flux = np.concatenate([[0], np.sum(np.diff(spec, axis=1) ** 2 * (np.diff(spec, axis=1) > 0), axis=0)])
    # normalize
    def norm(a):
        a = a - a.min()
        mx = a.max()
        return a / mx if mx > 0 else a
    rms_n = norm(rms)
    flux_n = norm(flux[: len(rms_n)])
    # peaks
    peaks_rms, _ = find_peaks(rms_n, height=0.6, distance=int(sr / hop * 2))
    peaks_flux, _ = find_peaks(flux_n, height=0.5, distance=int(sr / hop * 2))
    # build per-second score arrays
    fps_audio = sr / hop
    duration = len(y) / sr
    nsec = int(duration) + 1
    score = np.zeros(nsec)
    for p in peaks_rms:
        t = int(p / fps_audio)
        if 0 <= t < nsec:
            score[t] += 2.0
    for p in peaks_flux:
        t = int(p / fps_audio)
        if 0 <= t < nsec:
            score[t] += 1.5
    return score, duration


def scene_changes():
    # use ffmpeg scene detection
    cmd = [
        "ffmpeg", "-i", SOURCE,
        "-vf", "select='gt(scene,0.3)',showinfo",
        "-f", "null", "-",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    times = []
    for line in (r.stderr or "").splitlines():
        if "pts_time" in line:
            # parse pts_time:X
            import re
            m = re.search(r"pts_time:([\d.]+)", line)
            if m:
                times.append(float(m.group(1)))
    return times


def motion_scores(duration):
    cap = cv2.VideoCapture(SOURCE)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    nsec = int(duration) + 1
    motion = np.zeros(nsec)
    prev = None
    frame_idx = 0
    # sample ~5 fps for speed
    sample_every = max(1, int(fps / 5))
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % sample_every != 0:
            frame_idx += 1
            continue
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        g = cv2.resize(g, (320, 180))
        if prev is not None:
            diff = cv2.absdiff(g, prev)
            val = float(diff.mean())
            t = int(frame_idx / fps)
            if 0 <= t < nsec:
                motion[t] = max(motion[t], val)
        prev = g
        frame_idx += 1
    cap.release()
    # normalize
    mx = motion.max()
    if mx > 0:
        motion = motion / mx
    # peaks in motion
    peaks, _ = find_peaks(motion, height=0.5, distance=3)
    score = np.zeros(nsec)
    for p in peaks:
        score[p] += 1.5
    return score


def main():
    print("Extracting audio...")
    extract_audio()
    print("Audio scoring...")
    ascore, duration = audio_scores()
    print("Scene detection...")
    scenes = scene_changes()
    print(f"  {len(scenes)} scene changes")
    sscene = np.zeros(int(duration) + 1)
    for t in scenes:
        i = int(t)
        if 0 <= i < len(sscene):
            sscene[i] += 1.0
    print("Motion scoring...")
    mscore = motion_scores(duration)

    total = ascore + sscene * 1.0 + mscore * 1.0

    # pick top non-overlapping windows with a minimum score threshold
    half = CLIP_SECONDS // 2
    threshold = max(2.0, float(np.median(total) + np.std(total)))
    candidates = sorted(range(len(total)), key=lambda i: total[i], reverse=True)
    chosen = []
    for c in candidates:
        if len(chosen) >= MAX_CLIPS:
            break
        if total[c] < threshold:
            continue
        if any(abs(c - x[0]) < CLIP_SECONDS for x in chosen):
            continue
        # snap start to nearest scene change before the peak
        prev_scenes = [s for s in scenes if s <= c]
        snap_start = prev_scenes[-1] if prev_scenes else max(0, c - half)
        if snap_start > c:
            snap_start = max(0, c - half)
        start = max(0, int(snap_start))
        end = min(duration, start + CLIP_SECONDS)
        if end - start < 45:
            continue
        chosen.append((start, end, float(total[c])))
    # if too few, relax threshold
    if len(chosen) < MAX_CLIPS:
        for c in candidates:
            if len(chosen) >= MAX_CLIPS:
                break
            if any(abs(c - x[0]) < CLIP_SECONDS for x in chosen):
                continue
            start = max(0, c - half)
            end = min(duration, start + CLIP_SECONDS)
            if end - start < 45:
                continue
            chosen.append((start, end, float(total[c])))
            chosen.sort(key=lambda x: x[0])
    chosen.sort()

    moments = [{"start": s, "end": e, "score": sc} for (s, e, sc) in chosen]
    with open(MOMENTS, "w") as f:
        json.dump({"duration": duration, "moments": moments}, f, indent=2)
    print(json.dumps(moments, indent=2))


if __name__ == "__main__":
    main()
