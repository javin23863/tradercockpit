#!/usr/bin/env python3
"""
auto-reframe.py - convert a landscape clip to vertical 9:16, FOLLOWING the subject.

Turns a 16:9 source into a 9:16 short by tracking the subject and cropping dynamically (a moving crop
window), instead of a static center-crop that cuts people out of frame. 100% local, ffmpeg-based.

DESIGN: the reframe ENGINE is decoupled from the subject DETECTOR, so the "how do we find the subject" question
(build our own OpenCV/MediaPipe detector, or feed a vendor's subject data) doesn't block the engine. The engine takes
a subject TRAJECTORY - a list of {t, cx} (or {t, x_frac}) centers over time, from ANY source - smooths it, and drives
a time-varying ffmpeg crop. With no trajectory it degrades to a smart center-crop (zero extra deps, always works).

  # smart center-crop (no deps beyond ffmpeg):
  python auto-reframe.py --input in.mp4 --output out.mp4
  # follow a subject trajectory from any detector (cv2 / mediapipe / vendor):
  python auto-reframe.py --input in.mp4 --output out.mp4 --trajectory traj.json
  # use the OPTIONAL built-in OpenCV face detector if opencv-python is installed:
  python auto-reframe.py --input in.mp4 --output out.mp4 --track

traj.json: [{"t": 0.0, "cx": 640}, {"t": 0.5, "cx": 720}, ...]   cx in source pixels (or "x_frac" 0..1).
Dependency-free (stdlib + ffmpeg/ffprobe on PATH). White-label: no personal/brand strings. MIT-safe.
"""
import argparse, json, os, subprocess, sys, tempfile

def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-show_entries", "format=duration", "-of", "json", path], text=True)
    j = json.loads(out)
    st = (j.get("streams") or [{}])[0]
    w, h = int(st.get("width") or 0), int(st.get("height") or 0)
    dur = float(st.get("duration") or (j.get("format") or {}).get("duration") or 0) or 0.0
    if not (w and h):
        raise SystemExit("auto-reframe: could not read video dimensions")
    return w, h, dur

def load_trajectory(path, w):
    """-> sorted [(t, cx_px)] in source pixels."""
    data = json.load(open(path, encoding="utf-8"))
    pts = []
    for p in data:
        t = float(p.get("t", p.get("time", 0)))
        if "cx" in p: cx = float(p["cx"])
        elif "x_frac" in p: cx = float(p["x_frac"]) * w
        elif "x" in p: cx = float(p["x"])
        else: continue
        pts.append((t, cx))
    pts.sort(key=lambda x: x[0])
    return pts

def try_opencv_track(path, w, h, sample_fps=3.0):
    """OPTIONAL: built-in OpenCV Haar face detector -> trajectory. Returns [] if cv2 unavailable / no faces."""
    try:
        import cv2  # optional dep; absence is fine
    except Exception:
        sys.stderr.write("auto-reframe: opencv-python not installed; use --trajectory or center-crop.\n")
        return []
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(round(fps / sample_fps)))
    pts, i = [], 0
    while True:
        ok, frame = cap.read()
        if not ok: break
        if i % step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = casc.detectMultiScale(gray, 1.2, 5, minSize=(int(h * 0.06), int(h * 0.06)))
            if len(faces):
                fx, fy, fw, fh = max(faces, key=lambda r: r[2] * r[3])  # dominant (largest) face
                pts.append((i / fps, fx + fw / 2.0))
        i += 1
    cap.release()
    return pts

def smooth_fill(pts, dur, crop_w, w, keyframe_dt=0.5, win=5):
    """Resample the trajectory onto an even keyframe grid, clamp to valid crop range, moving-average smooth."""
    half = crop_w / 2.0
    lo, hi = half, w - half
    n = max(2, int(dur / keyframe_dt) + 1)
    grid = [k * keyframe_dt for k in range(n)]
    if not pts:
        return [(t, w / 2.0) for t in grid]  # center
    xs = []
    for t in grid:
        # linear interp / hold at ends
        if t <= pts[0][0]: cx = pts[0][1]
        elif t >= pts[-1][0]: cx = pts[-1][1]
        else:
            cx = pts[-1][1]
            for a, b in zip(pts, pts[1:]):
                if a[0] <= t <= b[0]:
                    r = (t - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 0
                    cx = a[1] + r * (b[1] - a[1]); break
        xs.append(min(hi, max(lo, cx)))
    sm = []
    for k in range(len(xs)):
        a = max(0, k - win); b = min(len(xs), k + win + 1)
        sm.append(sum(xs[a:b]) / (b - a))
    return list(zip(grid, sm))

def build_sendcmd(traj, crop_w, w):
    """ffmpeg sendcmd script: set crop x (top-left) at each keyframe. x = clamp(cx - crop_w/2, 0, w-crop_w)."""
    lines = []
    for t, cx in traj:
        x = int(round(min(w - crop_w, max(0, cx - crop_w / 2.0))))
        lines.append(f"{t:.3f} crop x {x};")
    return "\n".join(lines)

def reframe(inp, outp, aspect=(9, 16), out_w=1080, out_h=1920, trajectory=None, track=False, keyframe_dt=0.5):
    inp = os.path.abspath(inp); outp = os.path.abspath(outp)  # so a cwd change (below) can't break relative paths
    w, h, dur = probe(inp)
    crop_w = min(w, int(round(h * aspect[0] / aspect[1])))  # portrait window width from full height
    crop_h = h
    pts = []
    if trajectory: pts = load_trajectory(trajectory, w)
    elif track: pts = try_opencv_track(inp, w, h)
    vf_scale = f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,crop={out_w}:{out_h}"
    if not pts:
        # static center-crop -> scale (deterministic, no deps)
        x = int(round((w - crop_w) / 2.0))
        vf = f"crop={crop_w}:{crop_h}:{x}:0,{vf_scale}"
        cmd = ["ffmpeg", "-y", "-i", inp, "-vf", vf, "-c:a", "copy", "-loglevel", "error", outp]
        return _run(cmd, "center")
    traj = smooth_fill(pts, dur or (pts[-1][0] + keyframe_dt), crop_w, w, keyframe_dt)
    with tempfile.NamedTemporaryFile("w", suffix=".cmds", delete=False, encoding="utf-8") as f:
        f.write(build_sendcmd(traj, crop_w, w)); cmds = f.name
    x0 = int(round(min(w - crop_w, max(0, traj[0][1] - crop_w / 2.0))))
    # Reference the sendcmd file by BASENAME with ffmpeg's cwd = its dir — sidesteps all Windows drive-colon/backslash
    # filtergraph-escaping pain (abs input/output paths still resolve fine).
    vf = f"sendcmd=f={os.path.basename(cmds)},crop={crop_w}:{crop_h}:{x0}:0,{vf_scale}"
    try:
        subprocess.run(["ffmpeg", "-y", "-i", inp, "-vf", vf, "-c:a", "copy", "-loglevel", "error", outp],
                       check=True, cwd=os.path.dirname(cmds))
        print(f"OK auto-reframe [tracked] -> {outp}")
        return outp
    finally:
        try: os.unlink(cmds)
        except OSError: pass

def _run(cmd, mode):
    subprocess.run(cmd, check=True)
    print(f"OK auto-reframe [{mode}] -> {cmd[-1]}")
    return cmd[-1]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True); ap.add_argument("--output", required=True)
    ap.add_argument("--aspect", default="9:16"); ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--trajectory"); ap.add_argument("--track", action="store_true")
    a = ap.parse_args()
    aw, ah = (int(x) for x in a.aspect.split(":"))
    reframe(a.input, a.output, (aw, ah), a.width, a.height, a.trajectory, a.track)
