"""Free, local depth maps and product cut-outs for the company's own photos.

Models (downloaded once from GitHub releases, verified by SHA-256, run on CPU
with onnxruntime; no API, no account, no cost):

- Depth Anything V2 Small (Apache-2.0), ONNX export by fabio-sim:
  relative depth, about 1.3 s per photo on a CPU.
- U2-Net-p (Apache-2.0), from the rembg project: salient-object mask used to
  cut a product out of its background.

Every function returns None instead of raising when the runtime, the model or
the network is unavailable; callers then keep their non-depth fallback.
"""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import tempfile

MODELS = {
    "depth": {
        "url": "https://github.com/fabio-sim/Depth-Anything-ONNX/releases/download/"
               "v2.0.0/depth_anything_v2_vits.onnx",
        "sha256": "d2b11a11c1d4a12b47608fa65a17ee9a4c605b55ee1730c8e3b526304f2562be",
        "size": 518,
    },
    "mask": {
        "url": "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx",
        "sha256": "309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8",
        "size": 320,
    },
}
MAX_OUTPUT_WIDTH = 1024
_sessions: dict = {}


def disabled() -> bool:
    return os.getenv("KAURIVO_DEPTH_DISABLED") == "1"


def _cache_dir() -> Path:
    return Path(os.getenv("KAURIVO_MODEL_CACHE") or Path.home() / ".cache" / "kaurivo-models")


def _digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def model_path(name: str, *, download=None) -> Path | None:
    """Return a verified local model file, downloading it once if needed."""
    spec = MODELS[name]
    target = _cache_dir() / f"{name}-{spec['sha256'][:12]}.onnx"
    if target.is_file() and _digest(target) == spec["sha256"]:
        return target
    if disabled():
        return None
    try:
        if download is None:
            import requests

            def download(url, destination):
                with requests.get(url, stream=True, timeout=(15, 180)) as reply:
                    reply.raise_for_status()
                    with destination.open("wb") as handle:
                        for chunk in reply.iter_content(1 << 20):
                            handle.write(chunk)
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False, suffix=".part") as tmp:
            partial = Path(tmp.name)
        download(spec["url"], partial)
        if _digest(partial) != spec["sha256"]:
            partial.unlink(missing_ok=True)
            return None
        partial.replace(target)
        return target
    except Exception:  # network, disk or HTTP failure: caller keeps its fallback
        return None


def _session(name: str):
    if name in _sessions:
        return _sessions[name]
    path = model_path(name)
    if path is None:
        return None
    try:
        import onnxruntime
        session = onnxruntime.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    except Exception:
        return None
    _sessions[name] = session
    return session


def _prepare(image, size):
    import numpy as np
    from PIL import Image
    array = np.asarray(image.convert("RGB").resize((size, size), Image.BICUBIC), dtype=np.float32) / 255.0
    array = (array - (0.485, 0.456, 0.406)) / (0.229, 0.224, 0.225)
    return array.transpose(2, 0, 1)[None].astype(np.float32)


def _normalise(values):
    import numpy as np
    low, high = np.percentile(values, 1), np.percentile(values, 99)
    return np.clip((values - low) / max(1e-6, high - low), 0, 1)


def _output_size(image) -> tuple[int, int]:
    width, height = image.size
    if width > MAX_OUTPUT_WIDTH:
        return MAX_OUTPUT_WIDTH, round(height * MAX_OUTPUT_WIDTH / width)
    return width, height


def estimate_depth(photo: Path, destination: Path) -> Path | None:
    """Write an 8-bit depth map (white = near) beside ``destination``."""
    session = _session("depth")
    if session is None:
        return None
    try:
        import numpy as np
        from PIL import Image, ImageFilter
        with Image.open(photo) as image:
            size = _output_size(image)
            batch = _prepare(image, MODELS["depth"]["size"])
        raw = session.run(None, {session.get_inputs()[0].name: batch})[0]
        depth = _normalise(np.squeeze(raw))
        out = Image.fromarray((depth * 255).astype("uint8"), "L").resize(size, Image.BICUBIC)
        # A slight blur removes stair-steps that would tear during parallax.
        out = out.filter(ImageFilter.GaussianBlur(1.2))
        destination.parent.mkdir(parents=True, exist_ok=True)
        out.save(destination, "WEBP", lossless=True)
        return destination
    except Exception:
        return None


def estimate_mask(photo: Path, destination: Path) -> Path | None:
    """Write an 8-bit foreground mask (white = product) for a cut-out."""
    session = _session("mask")
    if session is None:
        return None
    try:
        import numpy as np
        from PIL import Image, ImageFilter
        with Image.open(photo) as image:
            size = _output_size(image)
            batch = _prepare(image, MODELS["mask"]["size"])
        raw = session.run(None, {session.get_inputs()[0].name: batch})[0]
        mask = _normalise(np.squeeze(raw))
        out = Image.fromarray((mask * 255).astype("uint8"), "L").resize(size, Image.BICUBIC)
        out = out.filter(ImageFilter.GaussianBlur(.8))
        destination.parent.mkdir(parents=True, exist_ok=True)
        out.save(destination, "WEBP", lossless=True)
        return destination
    except Exception:
        return None


def mask_coverage(mask: Path) -> float:
    """Share of the frame the product covers (0-1); used to accept a cut-out."""
    from PIL import Image
    with Image.open(mask) as image:
        histogram = image.convert("L").histogram()
    return sum(histogram[128:]) / max(1, sum(histogram))
