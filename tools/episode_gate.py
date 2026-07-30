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
    py tools/episode_gate.py source OpenMontage/projects/series-03-slippage
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
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OM = Path(os.environ.get("OPENMONTAGE_ROOT", ROOT / "OpenMontage")).resolve()
_AUDIO_DEFAULT = OM / ".venv-audio" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
AUDIO_PY = Path(os.environ.get("OPENMONTAGE_AUDIO_PY", _AUDIO_DEFAULT))
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
    ("teaching_claim_gate", "repo", ["tools/teaching_claim_gate.py",
                                     "--script", "{art}/vo.txt",
                                     "--ontology", "{art}/claims.json"], False),
    ("human_narration",  "repo",  ["tools/human_facing_gate.py",
                                   "teaching_narration", "{art}/vo.txt"], False),
    ("human_title",      "repo",  ["tools/human_facing_gate.py",
                                   "youtube_title", "{art}/packaging.json",
                                   "--json-key", "title"], False),
    ("human_description", "repo", ["tools/human_facing_gate.py",
                                   "youtube_description", "{art}/_yt_desc.txt"], False),
    ("script_style_gate", "repo", ["tools/script_style_gate.py", "{art}/vo.txt"], False),
    # --register teach: this series is not the daily market-recap lane, and scoring it against
    # that corpus blocked 91% of real finance-education transcripts too. See ai_tell_gate.py.
    ("ai_tell_gate",     "repo",  ["tools/ai_tell_gate.py", "--register", "teach", "{art}"], False),
    ("check_figures",    "ep",    ["tools/check_figures.py"], False),
    ("term_gate",        "repo",  ["tools/term_gate.py", "--production", "{proj}",
                                   "--episode", "{syllabus_ep}", "--strict"], False),
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

SOURCE_GATES = {
    "packaging_gate",
    "script_arc_gate",
    "teaching_claim_gate",
    "human_narration",
    "human_title",
    "human_description",
    "script_style_gate",
    "ai_tell_gate",
    "term_gate",
}


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


def _relative(proj: Path, path: Path) -> str:
    return path.resolve().relative_to(proj.resolve()).as_posix()


def _nonempty(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return False


def _operator_receipt(path: Path, schema: str) -> dict:
    if not path.is_file():
        raise ValueError(f"required operator approval missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != schema:
        raise ValueError(f"{path} must use {schema}")
    if (data.get("status") != "approved" or data.get("approvalKind") != "operator" or
            data.get("operatorReviewed") is not True or not _nonempty(data.get("reviewedBy"))):
        raise ValueError(f"{path} must be an operator-reviewed approval")
    try:
        reviewed_at = datetime.fromisoformat(data["reviewedAt"].replace("Z", "+00:00"))
    except (KeyError, AttributeError, ValueError) as exc:
        raise ValueError(f"{path} reviewedAt must be ISO-8601") from exc
    if reviewed_at.tzinfo is None:
        raise ValueError(f"{path} reviewedAt must include a timezone")
    return data


def quality_review_contract(art: Path) -> tuple[Path, Path, Path, Path]:
    """Require a complete strategy passport and hash-bound human review receipt."""
    script = art / "vo.txt"
    capture = art / "operator-capture.txt"
    passport_path = art / "strategy-passport.json"
    review_path = art / "human-facing-review.json"
    for path in (script, capture, passport_path, review_path):
        if not path.is_file():
            raise ValueError(f"required quality artifact missing: {path}")

    passport = json.loads(passport_path.read_text(encoding="utf-8"))
    if not isinstance(passport, dict) or passport.get("schema") != "strategy-passport/v1":
        raise ValueError(f"{passport_path} must use strategy-passport/v1")
    strategy = passport.get("strategy")
    validation = passport.get("validation")
    if not isinstance(strategy, dict) or not isinstance(validation, dict):
        raise ValueError(f"{passport_path} needs strategy and validation objects")
    strategy_fields = ("asset_class", "instrument", "venue", "timeframe", "session_timezone",
                       "entry", "exits", "sizing", "costs", "parameters")
    validation_fields = ("phase", "test_window", "settings", "thresholds", "result")
    missing = [f"strategy.{key}" for key in strategy_fields if not _nonempty(strategy.get(key))]
    missing += [
        f"validation.{key}" for key in validation_fields if not _nonempty(validation.get(key))
    ]
    sources = passport.get("sources")
    limitations = passport.get("limitations")
    if not isinstance(sources, list) or not sources or any(
        not isinstance(source, dict) or
        any(not _nonempty(source.get(field))
            for field in ("citation", "locator", "supports", "limitations"))
        for source in sources
    ):
        missing.append("sources")
    if (not isinstance(limitations, list) or not limitations or
            any(not _nonempty(item) for item in limitations)):
        missing.append("limitations")
    if missing:
        raise ValueError(f"{passport_path} has empty required fields: {missing}")

    review = json.loads(review_path.read_text(encoding="utf-8"))
    if not isinstance(review, dict) or review.get("schema") != "human-facing-review/v1":
        raise ValueError(f"{review_path} must use human-facing-review/v1")
    expected_hashes = {
        "script_sha256": sha256(script),
        "operator_capture_sha256": sha256(capture),
        "strategy_passport_sha256": sha256(passport_path),
    }
    for key, expected in expected_hashes.items():
        if review.get(key) != expected:
            raise ValueError(f"{review_path} {key} does not match its artifact")
    if review.get("protected_items_status") != "PASS":
        raise ValueError(f"{review_path} protected_items_status must be PASS")
    if review.get("disclosure_status") != "PASS":
        raise ValueError(f"{review_path} disclosure_status must be PASS")
    critic = review.get("independent_critic")
    if (not isinstance(critic, dict) or critic.get("status") != "PASS" or
            not _nonempty(critic.get("reviewer")) or critic.get("unresolved_findings") != []):
        raise ValueError(f"{review_path} needs a named PASS critic with no unresolved findings")
    read_aloud = review.get("operator_read_aloud")
    if (not isinstance(read_aloud, dict) or read_aloud.get("status") != "APPROVED" or
            not _nonempty(read_aloud.get("operator")) or not _nonempty(read_aloud.get("date"))):
        raise ValueError(f"{review_path} needs dated operator read-aloud approval")

    approval_path = art / "operator-script-approval.json"
    approval = _operator_receipt(approval_path, "tradercockpit-series-script-approval/v1")
    approved_script = (art / str(approval.get("script", ""))).resolve()
    if approved_script != script.resolve() or approval.get("scriptSha256") != sha256(script):
        raise ValueError(f"{approval_path} does not approve this exact vo.txt")
    attestations = approval.get("attestations")
    required_attestations = (
        "readAloud",
        "phrasingATraderWouldSay",
        "factSeparatedFromJudgment",
    )
    if not isinstance(attestations, dict) or any(
        attestations.get(name) is not True for name in required_attestations
    ):
        raise ValueError(f"{approval_path} is missing operator attestations")
    return capture, passport_path, review_path, approval_path


def release_contract(proj: Path, art: Path, meta: dict, *,
                     final: bool = True, master: Path | None = None) -> tuple[dict, dict[str, str]]:
    """Load and hash the exact public copy/settings that certification must bind."""
    package_path = art / "packaging.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    settings = package.get("release")
    if not isinstance(settings, dict):
        raise ValueError(f"{package_path} needs a release object")
    required = (
        "privacy", "category", "containsSyntheticMedia", "captionLanguage", "captionName"
    )
    missing = [key for key in required if key not in settings]
    if missing:
        raise ValueError(f"{package_path} release is missing {missing}")
    if settings["privacy"] not in {"private", "unlisted", "public"}:
        raise ValueError(f"{package_path} release.privacy is invalid")
    if not isinstance(settings["category"], str) or not settings["category"].strip():
        raise ValueError(f"{package_path} release.category must be a non-empty string")
    if not isinstance(settings["containsSyntheticMedia"], bool):
        raise ValueError(f"{package_path} release.containsSyntheticMedia must be boolean")
    for key in ("captionLanguage", "captionName"):
        if not isinstance(settings[key], str) or not settings[key].strip():
            raise ValueError(f"{package_path} release.{key} must be a non-empty string")

    title = package.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"{package_path} title must be a non-empty string")
    description_path = art / "_yt_desc.txt"
    tags_path = art / "_yt_tags.json"
    thumbnail_html = art / f"thumbnail-ep{meta['ep2']}.html"
    thumbnail_png = art / f"thumbnail-ep{meta['ep2']}.png"
    captions_path = proj / "assets" / "subtitles.srt"
    capture, passport_path, review_path, script_approval_path = quality_review_contract(art)
    paths = [
        art / "vo.txt",
        package_path,
        art / "claims.json",
        capture,
        passport_path,
        review_path,
        script_approval_path,
        description_path,
        tags_path,
    ]
    waiver_path = art / "waivers.json"
    if waiver_path.is_file():
        paths.append(waiver_path)
    if final:
        if master is None or not master.is_file():
            raise ValueError("a final release contract requires the exact rendered master")
        master_approval_path = art / "operator-master-approval.json"
        master_approval = _operator_receipt(
            master_approval_path, "tradercockpit-series-master-approval/v1"
        )
        approved_master = (proj / str(master_approval.get("master", ""))).resolve()
        if approved_master != master.resolve() or master_approval.get("sha256") != sha256(master):
            raise ValueError(f"{master_approval_path} does not approve this exact master")
        if master_approval.get("publicationAuthorized") is not False:
            raise ValueError(f"{master_approval_path} must keep publication as a separate action")
        paths.extend((
            art / "scenes.json",
            thumbnail_html,
            thumbnail_png,
            captions_path,
            proj / "hyperframes" / "index.html",
            master_approval_path,
        ))
    absent = [str(path) for path in paths if not path.is_file()]
    if absent:
        raise ValueError("required public/source file(s) missing: " + ", ".join(absent))

    description = description_path.read_text(encoding="utf-8")
    if not description.strip():
        raise ValueError(f"{description_path} must not be empty")
    tags = json.loads(tags_path.read_text(encoding="utf-8"))
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        raise ValueError(f"{tags_path} must be a JSON array of non-empty strings")

    inputs = {_relative(proj, path): sha256(path) for path in paths}
    release = {
        "title": title,
        "description": description,
        "tags": tags,
        "category": settings["category"],
        "privacy": settings["privacy"],
        "containsSyntheticMedia": settings["containsSyntheticMedia"],
        "madeForKids": False,
        "captionLanguage": settings["captionLanguage"],
        "captionName": settings["captionName"],
    }
    if final:
        release.update({
            "thumbnail": _relative(proj, thumbnail_png),
            "thumbnail_sha256": sha256(thumbnail_png),
            "captions": _relative(proj, captions_path),
            "captions_sha256": sha256(captions_path),
        })
    return release, inputs


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
        env = os.environ.copy()
        if where == "node":
            npm_cache = proj / "artifacts" / "build" / "npm-cache"
            npm_cache.mkdir(parents=True, exist_ok=True)
            env["NPM_CONFIG_CACHE"] = str(npm_cache)
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env,
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


def run(proj: Path, master: Path | None, only: str | None, source_only: bool = False) -> int:
    art = proj / "artifacts"
    if not (art / "packaging.json").is_file():
        sys.exit(f"BLOCK: no {art / 'packaging.json'} -- is {proj} an episode?")
    meta = episode_meta(art)
    waivers = load_waivers(art)
    subs = {"art": str(art), "proj": str(proj),
            "master": str(master) if master else "", **meta}

    results, blocked, waived = {}, [], []
    if source_only and only and only not in SOURCE_GATES:
        sys.exit(f"BLOCK: {only} is not a pre-TTS source gate")
    try:
        release, inputs = release_contract(
            proj, art, meta, final=not source_only, master=master
        )
        results["release_contract"] = {
            "verdict": "PASS", "rc": 0,
            "detail": f"{len(inputs)} public/source files exact-hash bound",
        }
        print(f"  PASS  {'release_contract':<19}       ")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        release, inputs = None, {}
        results["release_contract"] = {
            "verdict": "BLOCK", "rc": 1, "detail": str(exc),
        }
        blocked.append("release_contract")
        print(f"> BLOCK {'release_contract':<19}       ")
        print(f"          {exc}")

    for name, where, argv, needs_master in CHAIN:
        if only and only != name:
            continue
        if source_only and name not in SOURCE_GATES:
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
        "schema": "episode-gate/v2",
        "episode": meta["ep"],
        "verdict": "GREEN" if green else "BLOCKED",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "partial": bool(only),
        "source_only": source_only,
        "master": str(master) if master else None,
        "master_sha256": sha256(master) if master and master.is_file() else None,
        "inputs": inputs,
        "release": release,
        "blocked": blocked, "waived": waived, "gates": results,
    }
    (art / "build").mkdir(exist_ok=True)
    # A --only run writes BESIDE the real receipt, never over it. Marking a partial receipt as
    # partial is not enough: writing it to gate-receipt.json destroys a valid full certification
    # and the episode silently becomes uncertified. Debugging one gate must not decertify a
    # master.
    if source_only:
        name = "source-gate-receipt-partial.json" if only else "source-gate-receipt.json"
    else:
        name = "gate-receipt-partial.json" if only else "gate-receipt.json"
    out = art / "build" / name
    out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"\n{len(results) - len(blocked) - len(waived)} pass · {len(waived)} waived · "
          f"{len(blocked)} BLOCKED -> {out}")
    if blocked:
        print("  " + ", ".join(blocked))
        print("  No master is certified. Fix the artifact, or record an operator waiver.")
    return 0 if green else 1


def verify(master: Path, quiet: bool = False) -> int:
    """Exit 0 only if this exact file was certified. Called by the uploader.

    This verifier is series-only and therefore refuses paths outside the series tree.
    Other lanes must enter the uploader through their own explicit approval path.
    """
    master = master.resolve()
    try:
        master.relative_to(OM / "projects")
    except ValueError:
        print(f"BLOCK: {master} is outside the series tree; no episode receipt can certify it.")
        return 1
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
    if rec.get("schema") != "episode-gate/v2":
        print(f"BLOCK: {r} is not an episode-gate/v2 receipt.")
        return 1
    if rec.get("partial") or rec.get("source_only"):
        print(f"BLOCK: {r} is partial/source-only and does not certify the rendered chain.")
        return 1
    if rec.get("verdict") != "GREEN":
        print(f"BLOCK: gate receipt is {rec.get('verdict')} on {', '.join(rec.get('blocked', []))}")
        return 1
    gates = rec.get("gates")
    expected_gates = {"release_contract", *(name for name, *_ in CHAIN)}
    if not isinstance(gates, dict) or set(gates) != expected_gates:
        missing = sorted(expected_gates - set(gates or {}))
        extra = sorted(set(gates or {}) - expected_gates)
        print(f"BLOCK: gate receipt has the wrong executable gate set; "
              f"missing={missing}, extra={extra}.")
        return 1
    if rec.get("blocked") != []:
        print(f"BLOCK: GREEN receipt still records blocked gates: {rec.get('blocked')}")
        return 1
    bad_verdicts = sorted(
        name for name, result in gates.items()
        if not isinstance(result, dict) or result.get("verdict") not in {"PASS", "WAIVED"}
    )
    waived = sorted(name for name, result in gates.items()
                    if result.get("verdict") == "WAIVED")
    try:
        current_waivers = load_waivers(proj / "artifacts")
    except SystemExit as exc:
        print(f"BLOCK: current waiver contract is invalid: {exc}")
        return 1
    bad_waivers = sorted(
        name for name in waived
        if name == "release_contract" or
        not isinstance(gates[name].get("waiver"), dict) or
        any(not _nonempty(gates[name]["waiver"].get(field))
            for field in ("gate", "ruling", "date", "operator")) or
        gates[name]["waiver"].get("gate") != name or
        len(gates[name]["waiver"].get("ruling", "")) < 20 or
        gates[name]["waiver"] != current_waivers.get(name) or
        not covered(gates[name], gates[name]["waiver"])
    )
    if bad_verdicts or bad_waivers or waived != sorted(rec.get("waived") or []):
        print(f"BLOCK: gate verdict inventory is inconsistent; "
              f"bad={bad_verdicts}, bad_waivers={bad_waivers}, waived={waived}.")
        return 1
    actual = sha256(master)
    if rec.get("master_sha256") != actual:
        print(f"BLOCK: the receipt certifies {str(rec.get('master_sha256'))[:12]} but this file "
              f"is {actual[:12]}. Re-muxing invalidates the chain -- re-run it.")
        return 1
    try:
        meta = episode_meta(proj / "artifacts")
        expected_release, expected_inputs = release_contract(
            proj, proj / "artifacts", meta, final=True, master=master
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, SystemExit) as exc:
        print(f"BLOCK: current release contract no longer validates: {exc}")
        return 1
    if rec.get("inputs") != expected_inputs or rec.get("release") != expected_release:
        print("BLOCK: receipt source/release inventory differs from the current complete contract.")
        return 1
    inputs = rec.get("inputs")
    if not isinstance(inputs, dict) or not inputs:
        print(f"BLOCK: {r} has no exact-hash source inventory.")
        return 1
    for relative, expected in inputs.items():
        path = (proj / relative).resolve()
        try:
            path.relative_to(proj.resolve())
        except ValueError:
            print(f"BLOCK: certified source path escapes the episode: {relative}")
            return 1
        if not path.is_file():
            print(f"BLOCK: certified source {relative} is missing.")
            return 1
        observed = sha256(path)
        if observed != expected:
            print(f"BLOCK: certified source {relative} changed "
                  f"({str(expected)[:12]} -> {observed[:12]}). Re-run the chain.")
            return 1
    release = rec.get("release")
    release_fields = {
        "title", "description", "tags", "category", "privacy",
        "containsSyntheticMedia", "madeForKids",
        "captionLanguage", "captionName",
        "thumbnail", "thumbnail_sha256", "captions", "captions_sha256",
    }
    if not isinstance(release, dict) or not release_fields <= release.keys():
        print(f"BLOCK: {r} has no complete certified release contract.")
        return 1
    print(f"episode_gate: {master.name} certified GREEN "
          f"({len(gates)} gates, {len(waived)} waived)")
    return 0


def read_release_receipt(master: Path) -> tuple[Path, dict]:
    """Read the release object after verify(); callers must not use it as verification."""
    proj = next((p for p in master.resolve().parents
                 if (p / "artifacts" / "packaging.json").is_file()), None)
    if proj is None:
        raise ValueError(f"no episode owns {master}")
    receipt_path = proj / "artifacts" / "build" / "gate-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    return proj, receipt["release"]


def verify_release(master: Path, *, title: str, description: str, tags: list[str] | None,
                   category: str, privacy: str, thumbnail: str | Path | None,
                   synthetic: bool) -> int:
    """Verify exact public upload values for a series master; leave other lanes unchanged."""
    master = master.resolve()
    if verify(master) != 0:
        return 1
    try:
        _proj, release = read_release_receipt(master)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return 1
    actual = {
        "title": title,
        "description": description,
        "tags": tags or [],
        "category": str(category),
        "privacy": privacy,
        "containsSyntheticMedia": bool(synthetic),
        "madeForKids": False,
    }
    mismatches = [
        key for key, value in actual.items()
        if release.get(key) != value
    ]
    if thumbnail is None:
        mismatches.append("thumbnail")
    else:
        path = Path(thumbnail)
        if not path.is_file() or sha256(path) != release.get("thumbnail_sha256"):
            mismatches.append("thumbnail")
    if mismatches:
        print("BLOCK: upload values differ from certification: " +
              ", ".join(sorted(set(mismatches))))
        return 1
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
        source = proj / "source.txt"
        source.write_text("certified source", encoding="utf-8")
        (proj / "artifacts" / "build" / "gate-receipt.json").write_text(json.dumps(
            {"schema": "episode-gate/v2", "verdict": "GREEN", "partial": False,
             "source_only": False, "master_sha256": sha256(m),
             "inputs": {"source.txt": sha256(source)}, "release": {
                 "title": "Demo", "description": "Demo", "tags": [], "category": "22",
                 "privacy": "private", "containsSyntheticMedia": True, "madeForKids": False,
                 "captionLanguage": "en", "captionName": "English",
                 "thumbnail": "source.txt", "thumbnail_sha256": sha256(source),
                 "captions": "source.txt", "captions_sha256": sha256(source),
             },
             "blocked": [], "gates": {
                 "release_contract": {"verdict": "PASS"},
                 **{name: {"verdict": "PASS"} for name, *_ in CHAIN},
             }, "waived": []}),
            encoding="utf-8")
        global OM
        keep, OM = OM, td
        try:
            incomplete_caught = verify(m, quiet=True) == 1
            m.write_bytes(b"re-muxed by hand")          # exactly what happened to ep03/ep04
            remux_caught = verify(m, quiet=True) == 1
        finally:
            OM = keep
        print(f"  {'ok  ' if incomplete_caught else 'FAIL'} incomplete hand-built receipt is REFUSED")
        print(f"  {'ok  ' if remux_caught else 'FAIL'} re-muxed master is REFUSED")
        ok &= incomplete_caught and remux_caught
    print("demo: PASS" if ok else "demo: FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", nargs="?", choices=("source", "run", "verify"))
    ap.add_argument("target", nargs="?", type=Path)
    ap.add_argument("--master", type=Path)
    ap.add_argument("--only", help="run one gate; the receipt is marked partial and cannot certify")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        return demo()
    if a.list:
        for name, where, argv, _needs in CHAIN:
            stage = "pre-tts" if name in SOURCE_GATES else "final"
            print(f"  {name:<19} {where:<6} {stage:<7} {' '.join(argv)}")
        return 0
    if not a.mode or not a.target:
        ap.error("mode and target are required")
    if a.mode == "verify":
        return verify(a.target)
    if a.mode == "source":
        if a.master:
            ap.error("source mode does not accept --master")
        return run(a.target.resolve(), None, a.only, source_only=True)
    if a.master and not a.master.is_file():
        sys.exit(f"BLOCK: master {a.master} not found")
    return run(a.target.resolve(), a.master.resolve() if a.master else None, a.only)


if __name__ == "__main__":
    raise SystemExit(main())
