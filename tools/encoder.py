"""Pick a working H.264 encoder for this machine.

The operator's box has an RTX 3080 and every ffmpeg call was written against
`h264_nvenc`. ffmpeg ADVERTISES nvenc even with no NVIDIA GPU present, so the failure
is not a missing-encoder error at startup — it is exit 255 mid-render, which is how a
GPU-less box (Lenox) lost a chart capture that had already been screenshotted.

Probe once, cache, and fall back to libx264. Override with TRADERCOCKPIT_VIDEO_ENCODER
(`nvenc` or `x264`) when the probe is wrong or you want to force one.
"""

import os
import subprocess

_cached: bool | None = None


def nvenc_available() -> bool:
    """True only if nvenc actually ENCODES here — not merely if ffmpeg lists it."""
    global _cached
    forced = (os.getenv("TRADERCOCKPIT_VIDEO_ENCODER") or "").strip().lower()
    if forced in ("nvenc", "h264_nvenc"):
        return True
    if forced in ("x264", "libx264", "cpu"):
        return False
    if _cached is None:
        try:
            p = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                 "-i", "color=c=black:s=64x64:d=0.1", "-c:v", "h264_nvenc",
                 "-f", "null", os.devnull],
                capture_output=True, timeout=60)
            _cached = p.returncode == 0
        except Exception:
            _cached = False
    return _cached


def encoder_args(cq: int = 19, preset: str = "p5") -> list[str]:
    """ffmpeg output args for H.264. `cq` carries over as CRF on the CPU path —
    both are 0-51 lower-is-better, so the quality intent survives the fallback."""
    if nvenc_available():
        return ["-c:v", "h264_nvenc", "-cq", str(cq), "-preset", preset]
    return ["-c:v", "libx264", "-crf", str(cq), "-preset", "medium"]


if __name__ == "__main__":
    print("nvenc usable:", nvenc_available())
    print("args:", " ".join(encoder_args()))
