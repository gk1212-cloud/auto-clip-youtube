"""Generate titles/descriptions using a FREE local AI model (no API keys).

Uses a small HuggingFace text-generation model when available; otherwise falls
back to a deterministic heuristic. No network API is required at runtime (the
model is downloaded once and cached by HuggingFace).
"""
import json
import os

OUT = "out"


def _local_llm(source_title, n_clips):
    try:
        from transformers import pipeline
    except Exception:
        return None
    try:
        gen = pipeline(
            "text-generation",
            model="Qwen/Qwen2.5-0.5B-Instruct",
            device="cpu",
            max_new_tokens=256,
        )
    except Exception as e:
        print("Could not load local LLM:", e)
        return None
    prompt = (
        f"Generate {n_clips} short catchy YouTube Shorts titles (max 60 chars), "
        f"one shared description, and 12 relevant YouTube tags for clips from a long video titled: "
        f"'{source_title}'. Reply ONLY as JSON: "
        '{"titles":["..."],"description":"...","tags":["..."]}'
    )
    try:
        out = gen(prompt, do_sample=True, temperature=0.7)[0]["generated_text"]
    except Exception as e:
        print("Local LLM generation failed:", e)
        return None
    # extract JSON
    import re
    m = re.search(r"\{.*\}", out, re.S)
    if not m:
        return None
    try:
        parsed = json.loads(m.group(0))
    except Exception:
        return None
    titles = parsed.get("titles", [])
    desc = parsed.get("description", "")
    tags = parsed.get("tags", [])
    if not isinstance(titles, list) or not titles:
        return None
    if not isinstance(tags, list):
        tags = []
    return titles, desc, tags


def _fallback_tags(source_title):
    words = [w.strip(".,!?") for w in source_title.split()]
    tags = []
    for w in words:
        if len(w) > 3 and w.lower() not in ("video", "gameplay", "highlights"):
            tags.append(w)
    base = ["shorts", "gaming", "highlights", "best moments", "viral", "trending"]
    tags = list(dict.fromkeys(tags + base))
    return tags[:15]


def generate_meta(source_title, source_url, n_clips):
    res = _local_llm(source_title, n_clips)
    if res is not None:
        titles, desc = res
        tags = res[2] if len(res) > 2 else []
        if not desc:
            desc = f"Auto-clipped best moments from: {source_title}\nSource: {source_url}"
        if not tags:
            tags = _fallback_tags(source_title)
        return titles, desc, tags
    # fallback (no AI)
    titles = [f"Best moment #{i+1} - {source_title}" for i in range(n_clips)]
    desc = f"Auto-clipped best moments from: {source_title}\nSource: {source_url}\n\nGenerated automatically."
    tags = _fallback_tags(source_title)
    return titles, desc, tags


def main():
    with open("chosen_video.json") as f:
        v = json.load(f)
    clips = sorted(f for f in os.listdir(OUT) if f.startswith("clip_") and f.endswith(".mp4"))
    titles, desc, tags = generate_meta(v.get("title", "Long video"), v.get("url", ""), len(clips))
    # add shorts hashtags for feed discovery
    if "#shorts" not in desc.lower():
        desc = desc + "\n\n#Shorts #shorts #viral #trending"
    meta = {
        "titles": titles,
        "description": desc,
        "tags": tags,
        "compilation_title": f"Best moments compilation - {v.get('title','')}",
    }
    os.makedirs("work", exist_ok=True)
    with open(os.path.join("work", "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
