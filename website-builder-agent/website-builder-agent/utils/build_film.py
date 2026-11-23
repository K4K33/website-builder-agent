"""Build film: one real construction animation per trade, reused by every demo.

Reference sites (a house that builds itself on scroll) drive the hero with a
real video, not with image cross-fades. Kaurivo makes the same per TRADE:

1. keyframes of one room/house in its stages (same camera; FLUX klein edits of
   one finished image, see illustrated_sequence), e.g. old bathroom ->
   stripped to concrete -> waterproofed -> tiled -> finished;
2. an open first-last-frame video model (Wan 2.2 A14B FLF2V on a public
   Hugging Face ZeroGPU Space, free) animates each pair: the old tiles fall
   away, the membrane is rolled on, tiles are laid row by row;
3. the clips are joined and cut into a frame sequence that the hero scrubs on
   scroll (canvas, works on every phone).

The film is an illustration (labelled "Havainnevideo, tekoälyllä luotu") and
is made once per trade, then reused, so the free daily GPU quota is enough.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

SPACES = ("mcp-tools/wan-2-2-first-last-frame",)
NEGATIVE = ("people, hands, workers, text, watermark, logo, blurry, distorted geometry, warped lines, "
            "flicker, camera shake, cartoon, painting")

# Per trade: (stage label, how the change between this keyframe and the next happens).
SCRIPTS = {
    # Seen from inside, camera locked; every change progresses evenly and in order
    # (symmetric, layer by layer), like the reference sites, never patchy.
    "kylpyhuone": (
        ("Purku", "Locked-off camera inside the same bathroom. The old tiles, bathtub, sink, toilet and curtain "
                  "are removed in an orderly sequence from top to bottom, evenly on both sides, revealing bare grey "
                  "concrete. Smooth, calm, architectural animation, no people."),
        ("Vedeneristys", "Locked-off camera inside the same room. Off-white waterproofing rises evenly up all "
                         "walls at the same speed from the floor to the ceiling, a clean straight horizontal edge, "
                         "perfectly symmetric left and right. Smooth architectural animation, no people."),
        ("Laatoitus", "Locked-off camera inside the same room. Large grey tiles appear row by row from the floor "
                      "upwards, each row completing evenly across all walls, symmetric, straight grout lines. "
                      "Smooth architectural animation, no people."),
        ("Valmis", "Locked-off camera inside the same room. The glass shower wall, black rain shower and wall-hung "
                   "toilet glide gently into place one after another, then the light warms up; slow push-in. "
                   "Smooth architectural animation, no people."),
    ),
}


def keyframes(trade: str, root: Path) -> list[Path]:
    folder = Path(root) / trade / "keys"
    return sorted(p for p in folder.glob("k*.*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})


def animate_pair(start: Path, end: Path, prompt: str, target: Path, *, client=None,
                 seconds: float = 3.1, seed: int = 42) -> Path | None:
    """One clip from two keyframes via the free FLF2V Space; None on failure."""
    from gradio_client import Client, handle_file
    token = os.getenv("KAURIVO_HF_TOKEN", "").strip() or None
    errors = []
    for space in SPACES:
        try:
            api = client
            if api is None:
                try:
                    api = Client(space, token=token, verbose=False)
                except TypeError:  # older gradio_client
                    api = Client(space, hf_token=token, verbose=False)
            result = api.predict(handle_file(str(start)), handle_file(str(end)), prompt, NEGATIVE,
                                 seconds, 8, 1.0, 1.0, seed, False, api_name="/generate_video")
            video = result[0] if isinstance(result, (list, tuple)) else result
            if isinstance(video, dict):
                video = video.get("video") or video.get("path")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(video, target)
            return target
        except Exception as exc:  # report and try the next Space
            errors.append(f"{space}: {type(exc).__name__}: {str(exc)[:240]}")
    animate_pair.errors = errors
    return None


animate_pair.errors = []


def join_clips(clips: list[Path], target: Path, *, width: int = 1280) -> Path:
    """Concatenate clips (same size) into one H.264 film."""
    listing = target.with_suffix(".txt")
    listing.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-vf", f"scale={width}:-2:flags=lanczos,fps=24", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target)], check=True)
    listing.unlink()
    return target


def film_frames(film: Path, folder: Path, *, count: int = 120, width: int = 1280) -> list[Path]:
    """Cut the film into `count` evenly spaced WebP frames for the scroll hero."""
    folder.mkdir(parents=True, exist_ok=True)
    duration = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                     "csv=p=0", str(film)], capture_output=True, text=True, check=True).stdout)
    fps = count / max(.1, duration)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(film), "-vf",
                    f"fps={fps:.4f},scale={width}:-2:flags=lanczos", "-c:v", "libwebp", "-quality", "78",
                    str(folder / "f%03d.webp")], check=True)
    return sorted(folder.glob("f*.webp"))


def make_film(trade: str, root: Path, out: Path, *, limit: int = 0) -> dict | None:
    keys = keyframes(trade, root)
    script = SCRIPTS.get(trade)
    if script and len(keys) == len(script):   # no "before" keyframe: start from the bare shell
        script = script[1:]
    if not script or len(keys) != len(script) + 1:
        return None
    if limit:
        script = script[:limit]
    clips = []
    for index, (label, prompt) in enumerate(script):
        clip = animate_pair(keys[index], keys[index + 1], prompt, out / f"clip-{index + 1}.mp4")
        if clip is None:
            return {"error": getattr(animate_pair, "errors", []), "done": len(clips)}
        clips.append(clip)
    film = join_clips(clips, out / f"{trade}.mp4")
    meta = {"trade": trade, "labels": [label for label, _ in script], "clips": len(clips),
            "note": "Havainnevideo, tekoälyllä luotu"}
    (out / "film.json").write_text(json.dumps(meta, ensure_ascii=False))
    return {"film": str(film), **meta}


ASSETS = Path(__file__).resolve().parents[1] / "assets" / "sales_demo" / "film"
TRADES = {"kylpyhuone": r"kylpyhuone|laatoit|laatta|vedeneristy|märkätila"}


def film_for(text: str, root: Path | None = None) -> dict | None:
    """A finished, reviewed film for the trade (frames/ + film.json), or None."""
    import re
    text = str(text or "").casefold()
    for trade, pattern in TRADES.items():
        if not re.search(pattern, text):
            continue
        folder = Path(root or ASSETS) / trade
        frames = sorted((folder / "frames").glob("f*.webp"))
        meta = folder / "film.json"
        if len(frames) >= 24 and meta.is_file():
            data = json.loads(meta.read_text(encoding="utf-8"))
            return {"frames": frames, "labels": list(data.get("labels") or []),
                    "note": data.get("note") or "Havainnevideo, tekoälyllä luotu", "trade": trade}
    return None
