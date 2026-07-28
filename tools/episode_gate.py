#!/usr/bin/env python3
"""Run every gate an episode must pass, and refuse to certify a master when one blocks.

Operator, 2026-07-29: *"If they didn't pass the AI gate, how did they get mastered? That means
you're skipping a gate. That needs to get fixed."*

They are right, and the cause is structural rather than careless. **There was no place where
the chain ran.** Fifteen gates were fifteen hand-typed commands whose verdicts lived in
scrollback, and the master was a hand-typed ffmpeg mux that could not know about any of them.
The one fail-closed finisher this series had -- `tools/finish_master.sh`, whose own header says
*"if the presentation gate blocks, NOTHING downstream runs"* -- exists in series-01 and
series-02 and was **not copied into series-03 or series-04**. So ep03 and ep04 were muxed by
hand, and nothing downstream could tell that `ai_tell_gate` had said BLOCK.

A verdict nobody is forced to read is a suggestion. This file is the place that reads them.

    py tools/episode_gate.py run OpenMontage/projects/series-03-slippage --master <mp4>
    py tools/episode_gate.py verify <master.mp4>     # what the uploader calls
    py tools/episode_gate.py --list
    py tools/episode_gate.py --demo                  # must FAIL on purpose, twice

Three rules, and the first is the one that matters:

1. **A gate named in the chain but absent from disk BLOCKS.** Skipping a missing gate is the
   same bypass as deleting it, and deleting it is exactly what happened to `finish_master.sh`
   when series-03's tools were copied. A chain that quietly shrinks is not a chain.
2. **Non-zero exit, crash, or timeout all BLOCK.** A gate that cannot decide has not passed.
3. **A red is cleared only by a WAIVER carrying the operator's own words** -- see `waivers.json`.
   The point is that an accepted red becomes a durable, greppable record instead of silence.
   I cannot write one for myself: the ruling text is evidence, and inventing it is forgery.

The receipt is keyed to the **sha256 of the master it certified**, so it cannot outlive the file.
Re-mux the video and `verify` fails, which is the property that makes hand-mastering detectable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OM = ROOT / "OpenMontage"
AUDIO_PY = OM / ".venv-audio" / "Scripts" / "python.exe"
PY = sys.executable
TIMEOUT = 1800  # cut_census and motion_census walk an 11-minute render frame by frame

# The chain. THIS FILE IS THE SOURCE OF TRUTH for what an episode must pass.
#
# series-plan.md §10 lists gates in prose and is already stale -- it never named ai_tell_gate,
# slop_gate, lexicon_gate or intro_pace, all of which have blocked real work. Prose that is
# supposed to be a checklist decays silently; a list that executes cannot. §10 now cites this.
#
# (name, where, argv, needs_master)
#   repo  -- tools/ in this repo, version-controlled
#   ep    -- the episode's own tools/, which lives under the gitignored OpenMontage tree
#   node  -- npm, run inside hyperframes/
#   audio -- the episode's tools/ but under .venv-audio (DeepFilterNet/soundfile live there)
CHAIN = (
    # ---- source gates: the script, the packaging, the figures ----
    ("packaging_gate",   "repo",  ["tools/packaging_gate.py", "{art}/packaging.json"], False),
    ("script_arc_gate",  "repo",  ["tools/script_arc_gate.py", "{proj}"], False),
    ("script_style_gate", "repo", ["tools/script_style_gate.py", "{art}/vo.txt"], False),
    ("ai_writing_gate",  "repo",  ["tools/ai_writing_gate.py", "{art}"], False),
    # --register teach: this series is not the daily market-recap lane, and scoring it against
    # that corpus blocked 91% of real finance-education transcripts too. See ai_tell_gate.py.
    ("ai_tell_gate",     "repo",  ["tools/ai_tell_gate.py", "--register", "teach", "{art}"], False),
    ("check_figures",    "ep",    ["tools/check_figures.py"], False),
    ("term_gate",        "ep",    ["tools/term_gate.py", "--episode", "{syllabus_ep}"], False),
    # {proj}, not {art}: slop_gate globs <root>/hyperframes/compositions and <root>/artifacts.
    # Handed artifacts/ it matched nothing and printed "0 file(s) ... clean", and this chain
    # recorded a PASS for a gate that inspected nothing. It BLOCKs on zero files now too.
    ("slop_gate",        "ep",    ["tools/slop_gate.py", "{proj}"], False),
    ("lexicon_gate",     "ep",    ["tools/lexicon_gate.py"], False),
    ("thumb_gate",       "ep",    ["tools/thumb_gate.py", "{art}/thumbnail-ep{ep2}.html"], False),
    ("broll_conflicts",  "ep",    ["tools/broll_conflicts.py"], False),
    ("npm_check",        "node",  ["run", "check"], False),
    # ---- render gates: scored on the master, never on the source ----
    ("presentation_gate", "ep",   ["tools/presentation_gate.py", "{master}"], True),
    ("intro_pace",       "ep",    ["tools/intro_pace.py", "{master}"], True),
    ("cut_census",       "ep",    ["tools/cut_census.py", "{master}"], True),
    ("motion_census",    "ep",    ["tools/motion_census.py", "{master}"], True),
    ("check_bed",        "audio", ["tools/check_bed.py"], False),
    ("voice_consistency", "audio", ["tools/voice_consistency.py"], False),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_waivers(art: Path) -> dict[str, dict]:
    """Operator rulings that clear a red, keyed by gate name.

    A waiver must carry the ruling in the operator's own words. That is not ceremony: the
    alternative is a boolean, and a boolean is indistinguishable from me deciding I had a good
    reason. Malformed entries BLOCK rather than being ignored -- an unreadable waiver is the
    one shape that must never read as "no waiver, carry on".
    """
    path = art / "waivers.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data["waivers"]
    except Exception as exc:  # noqa: BLE001 - any unreadable waiver file is a hard stop
        sys.exit(f"BLOCK: {path} is unreadable ({exc}). Fix it or delete it; it cannot be skipped.")
    out = {}
    for i, w in enumerate(entries):
        for field in ("gate", "ruling", "date", "operator"):
            if not str(w.get(field, "")).strip():
                sys.exit(f"BLOCK: {path} waivers[{i}] is missing '{field}'. A waiver without "
                         f"the ruling that granted it is silence with extra steps.")
        if len(w["ruling"]) < 20:
            sys.exit(f"BLOCK: {path} waivers[{i}] ruling is {len(w['ruling'])} chars. Quote what "
                     f"the operator actually said, verbatim.")
        out[w["gate"]] = w
    return out


def covered(result: dict, waiver: dict) -> bool:
    """Does this waiver actually cover everything the gate objected to?

    A waiver keyed only by gate name is a blanket. `presentation_gate` checks first frame, first
    audio, first spoken word, speech gaps, dead spans, freezes and black tail; the operator's
    2026-07-29 ruling was about ONE of them, a 0.067s freeze overshoot. Waiving the gate would
    have silently also waived the 4.667s of head-black the same ruling was quoted alongside --
    the defect that ruling existed to stop mattering.

    So an optional `findings` list names the substrings being forgiven, and EVERY BLOCK line the
    gate emitted must match one of them. A new finding appearing later is not covered by an old
    waiver, which is the whole point. Omit `findings` and the waiver is a blanket, deliberately
    explicit rather than the default.
    """
    subs = waiver.get("findings")
    if not subs:
        return True
    blocks = [ln.strip() for ln in result.get("detail", "").splitlines()
              if ln.strip().startswith("BLOCK:") or ln.strip().startswith("FAIL")]
    if not blocks:
        return False  # nothing to match against; a waiver that cannot be checked does not apply
    return all(any(s.lower() in ln.lower() for s in subs) for ln in blocks)


def episode_meta(art: Path) -> dict:
    """Episode identity, with the syllabus number DECLARED rather than inferred.

    The first cut of this file defaulted `syllabus_episode` to the episode number and wrote a
    comment warning that an inferred wrong number makes term_gate check the wrong contract.
    It then did exactly that on the first real run: ep03 is `phase04_cost`, which is the
    syllabus's `## Ep04`, and the default sent term_gate to `## Ep03` (`phase03_timing`). The
    BLOCK it produced named split sample / session half / regime -- timing terms from an
    episode this one is not. A default that is right three times out of four is worse than no
    default, because the fourth is a confident wrong verdict. So: no default.
    """
    pkg = json.loads((art / "packaging.json").read_text(encoding="utf-8"))
    syl = str(pkg.get("syllabus_episode", "")).strip()
    if not syl:
        sys.exit(f"BLOCK: {art / 'packaging.json'} has no \"syllabus_episode\". term_gate reads "
                 f"the teaching contract out of docs/syllabus.md by that number, and this slate "
                 f"is offset from it (ep03 = phase04_cost = Ep04, ep04 = phase06_mc_param = "
                 f"Ep05). Declare it -- guessing it checks the wrong contract.")
    ep = int(pkg["episode"])
    return {"ep": ep, "ep2": f"{ep:02d}", "syllabus_ep": syl}


def run_gate(name, where, argv, proj: Path, subs: dict) -> dict:
    argv = [a.format(**subs) for a in argv]
    if where == "node":
        cwd, cmd = proj / "hyperframes", ["npm"] + argv
        script = cwd / "package.json"
    elif where == "repo":
        cwd, cmd, script = ROOT, [PY] + argv, ROOT / argv[0]
    else:
        interp = AUDIO_PY if where == "audio" else Path(PY)
        cwd, cmd, script = proj, [str(interp)] + argv, proj / argv[0]
        if where == "audio" and not AUDIO_PY.is_file():
            return {"verdict": "BLOCK", "rc": None,
                    "detail": f"{AUDIO_PY} not found. Falling back to a plain interpreter "
                              f"would run this gate without its audio stack and report a "
                              f"verdict it is not equipped to make."}
    # Rule 1. A gate that is not on disk BLOCKS. series-03/04 lost finish_master.sh exactly
    # this way -- by a copy that left it behind, with nothing to notice.
    if not script.exists():
        return {"verdict": "BLOCK", "rc": None,
                "detail": f"{script} does not exist. A gate you can delete is not a gate."}
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           timeout=TIMEOUT, shell=(where == "node"))
        rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return {"verdict": "BLOCK", "rc": None, "secs": TIMEOUT,
                "detail": f"timed out after {TIMEOUT}s -- a gate that cannot decide has not passed"}
    except Exception as exc:  # noqa: BLE001
        return {"verdict": "BLOCK", "rc": None, "detail": f"crashed: {exc}"}
    tail = "\n".join(l for l in out.strip().splitlines() if l.strip())[-1200:]
    return {"verdict": "PASS" if rc == 0 else "BLOCK", "rc": rc,
            "secs": round(time.time() - t0, 1), "detail": tail}


def run(proj: Path, master: Path | None, only: str | None) -> int:
    art = proj / "artifacts"
    if not (art / "packaging.json").is_file():
        sys.exit(f"BLOCK: no {art / 'packaging.json'} -- is {proj} an episode?")
    meta = episode_meta(art)
    waivers = load_waivers(art)
    subs = {"art": str(art), "proj": str(proj),
            "master": str(master) if master else "", **meta}

    results, blocked, waived = {}, [], []
    for name, where, argv, needs_master in CHAIN:
        if only and only != name:
            continue
        if needs_master and master is None:
            r = {"verdict": "BLOCK", "rc": None,
                 "detail": "render gate with no --master. Source-only runs cannot certify."}
        else:
            r = run_gate(name, where, argv, proj, subs)
        if r["verdict"] == "BLOCK" and name in waivers and covered(r, waivers[name]):
            r["verdict"], r["waiver"] = "WAIVED", waivers[name]
            waived.append(name)
        elif r["verdict"] == "BLOCK":
            blocked.append(name)
        results[name] = r
        mark = {"PASS": "  PASS ", "BLOCK": "> BLOCK", "WAIVED": "~WAIVED"}[r["verdict"]]
        secs = f"{r.get('secs', 0):>6.1f}s" if r.get("secs") else "       "
        print(f"{mark} {name:<19}{secs}")
        if r["verdict"] == "BLOCK":
            for line in r["detail"].splitlines()[-4:]:
                print(f"          {line}")
        if r["verdict"] == "WAIVED":
            print(f"          operator {r['waiver']['date']}: \"{r['waiver']['ruling'][:110]}\"")

    green = not blocked
    receipt = {
        "schema": "episode-gate/v1",
        "episode": meta["ep"],
        "verdict": "GREEN" if green else "BLOCKED",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "partial": bool(only),
        "master": str(master) if master else None,
        "master_sha256": sha256(master) if master and master.is_file() else None,
        "inputs": {p.name: sha256(p) for p in (art / "vo.txt", art / "scenes.json",
                                               proj / "hyperframes" / "index.html")
                   if p.is_file()},
        "blocked": blocked, "waived": waived, "gates": results,
    }
    (art / "build").mkdir(exist_ok=True)
    # A --only run writes BESIDE the real receipt, never over it. Marking a partial receipt as
    # partial is not enough: writing it to gate-receipt.json destroys a valid full certification
    # and the episode silently becomes uncertified. Debugging one gate must not decertify a
    # master.
    out = art / "build" / ("gate-receipt-partial.json" if only else "gate-receipt.json")
    out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"\n{len(results) - len(blocked) - len(waived)} pass · {len(waived)} waived · "
          f"{len(blocked)} BLOCKED -> {out}")
    if blocked:
        print("  " + ", ".join(blocked))
        print("  No master is certified. Fix the artifact, or record an operator waiver.")
    return 0 if green else 1


def verify(master: Path, quiet: bool = False) -> int:
    """Exit 0 only if this exact file was certified. Called by the uploader.

    Scoped to the series tree on purpose: the daily lane's own approval path
    (`script_approval` -> `social_batch`) governs there, and pretending otherwise would
    either block that lane or teach everyone to pass a flag that turns this off.
    """
    master = master.resolve()
    try:
        master.relative_to(OM / "projects")
    except ValueError:
        if not quiet:
            print(f"episode_gate: {master.name} is outside the series tree; "
                  f"social_batch approval governs it, not this receipt.")
        return 0
    proj = next((p for p in master.parents if (p / "artifacts" / "packaging.json").is_file()), None)
    if proj is None:
        print(f"BLOCK: {master} sits under the series tree but no episode owns it.")
        return 1
    r = proj / "artifacts" / "build" / "gate-receipt.json"
    if not r.is_file():
        print(f"BLOCK: {master.name} has no gate receipt. Run:\n"
              f"  py tools/episode_gate.py run {proj} --master {master}")
        return 1
    rec = json.loads(r.read_text(encoding="utf-8"))
    if rec.get("partial"):
        print(f"BLOCK: {r} is from a --only run and certifies one gate, not the chain.")
        return 1
    if rec.get("verdict") != "GREEN":
        print(f"BLOCK: gate receipt is {rec.get('verdict')} on {', '.join(rec.get('blocked', []))}")
        return 1
    actual = sha256(master)
    if rec.get("master_sha256") != actual:
        print(f"BLOCK: the receipt certifies {str(rec.get('master_sha256'))[:12]} but this file "
              f"is {actual[:12]}. Re-muxing invalidates the chain -- re-run it.")
        return 1
    print(f"episode_gate: {master.name} certified GREEN "
          f"({len(rec['gates'])} gates, {len(rec.get('waived', []))} waived)")
    return 0


def demo() -> int:
    """Prove this thing can say no. Two failures it must produce on demand.

    A gate never observed failing is void evidence -- the standing rule this series learned the
    hard way, from a conflict checker that passed by inspecting nothing.
    """
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # 1. missing gate script must BLOCK, not skip
        r = run_gate("ghost_gate", "ep", ["tools/ghost_gate.py"], td, {})
        hit = r["verdict"] == "BLOCK" and "does not exist" in r["detail"]
        print(f"  {'ok  ' if hit else 'FAIL'} missing gate script BLOCKS")
        ok &= hit
        # 2. a receipt must not survive the file it certified
        proj = td / "projects" / "ep"
        (proj / "artifacts" / "build").mkdir(parents=True)
        (proj / "artifacts" / "packaging.json").write_text('{"episode": 1}', encoding="utf-8")
        m = proj / "master.mp4"
        m.write_bytes(b"original")
        (proj / "artifacts" / "build" / "gate-receipt.json").write_text(json.dumps(
            {"verdict": "GREEN", "master_sha256": sha256(m), "gates": {}, "waived": []}),
            encoding="utf-8")
        global OM
        keep, OM = OM, td
        try:
            good = verify(m, quiet=True) == 0
            m.write_bytes(b"re-muxed by hand")          # exactly what happened to ep03/ep04
            caught = verify(m, quiet=True) == 1
        finally:
            OM = keep
        print(f"  {'ok  ' if good else 'FAIL'} matching master verifies")
        print(f"  {'ok  ' if caught else 'FAIL'} re-muxed master is REFUSED")
        ok &= good and caught
    print("demo: PASS" if ok else "demo: FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", nargs="?", choices=("run", "verify"))
    ap.add_argument("target", nargs="?", type=Path)
    ap.add_argument("--master", type=Path)
    ap.add_argument("--only", help="run one gate; the receipt is marked partial and cannot certify")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        return demo()
    if a.list:
        for name, where, argv, needs in CHAIN:
            print(f"  {name:<19} {where:<6} {'render' if needs else 'source':<7} {' '.join(argv)}")
        return 0
    if not a.mode or not a.target:
        ap.error("mode and target are required")
    if a.mode == "verify":
        return verify(a.target)
    if a.master and not a.master.is_file():
        sys.exit(f"BLOCK: master {a.master} not found")
    return run(a.target.resolve(), a.master.resolve() if a.master else None, a.only)


if __name__ == "__main__":
    raise SystemExit(main())
