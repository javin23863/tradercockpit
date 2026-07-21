#!/usr/bin/env python3
"""Unattended post-close daily runner: gates -> machine approval -> render -> publish.

Production starts after the 16:00 US/Eastern cash close and publishes at 18:00,
which is ~05:00 Asia/Bangkok. Nobody is awake to hold the exact-hash approval, so
this runner chains the existing tools and decides fail-closed:

    all gates clean          -> machine-approve, render, publish PUBLIC
    warning or unsourced     -> machine-approve, render, publish PRIVATE + notify
    hard gate failure        -> no approval, no render, no publish + notify
    unexpected exception     -> no publish + notify

It weakens nothing. Every gate still blocks exactly as before; the approval it
writes is hash-bound to the same vo.txt and is stamped machine-approved so the
operator can audit it in the morning.

Usage:
    python tools/daily_postclose.py productions/<video>
    python tools/daily_postclose.py productions/<video> --dry-run   # decide, never publish
    python tools/daily_postclose.py --selftest
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from tools import claims_gate, editorial_gate, script_style_gate, visual_qa
    from tools.script_approval import machine_approve
    from tools.social_batch import approval_fingerprint, load as load_social_batch
except ModuleNotFoundError:  # direct `python tools/daily_postclose.py` execution
    sys.path.insert(0, str(Path(__file__).parent))
    import claims_gate, editorial_gate, script_style_gate, visual_qa
    from script_approval import machine_approve
    from social_batch import approval_fingerprint, load as load_social_batch

ROOT = Path(__file__).resolve().parents[1]
PUBLIC, PRIVATE, NO_PUBLISH = "publish-public", "publish-private", "no-publish"


def log(msg):
    print(f"[postclose] {msg}", flush=True)


def notify(text):
    """Best-effort operator ping. A dead Telegram never changes the decision."""
    try:
        from tools.notify_telegram import send
    except ModuleNotFoundError:
        from notify_telegram import send
    try:
        send(text)
    except (SystemExit, OSError) as error:
        log(f"WARN telegram notify failed: {error}")


# --- decision logic (pure; self-tested below) --------------------------------

def decide(gates):
    """gates -> (decision, reasons). Fail-closed at every branch."""
    if gates.get("hardFail"):
        return NO_PUBLISH, list(gates["hardFail"])
    reasons = list(gates.get("warnings", []))
    return (PRIVATE, reasons) if reasons else (PUBLIC, [])


def safe_decide(collect):
    """Run a gate collector; any unexpected exception routes to no-publish."""
    try:
        gates = collect()
    except Exception as error:  # noqa: BLE001 - never default to publishing
        return NO_PUBLISH, [f"unexpected exception: {error!r}"], {"hardFail": [repr(error)]}
    decision, reasons = decide(gates)
    return decision, reasons, gates


# --- gate collection ---------------------------------------------------------

def collect_gates(production):
    """Run claims, style, and editorial gates. Hard fails block; warnings go private."""
    hard, warnings = [], []

    claims = claims_gate.gate(str(production))
    if claims["verdict"] != "PASS":
        hard += [f"claims_gate {b['type']}: {b['detail']}" for b in claims["blocked"]]
    warnings += [f"claims staleness: {w['claim']} as_of={w['as_of']}" for w in claims["warns"]]

    # "unsourced claim" = anything the ledger does not call verified. claims_gate
    # already blocks unverified claims that reach the script; a merely single-
    # sourced one is not a block, but it is not public-grade either.
    ledger = production / "claims.yaml"
    if ledger.is_file():
        import yaml

        for claim in yaml.safe_load(ledger.read_text(encoding="utf-8")) or []:
            if claim.get("status") != "verified":
                warnings.append(f"unsourced claim: {claim.get('id')} status={claim.get('status')}")

    style = script_style_gate.audit_sections(
        script_style_gate.parse_voiceover(production / "vo.txt"))
    (production / "build").mkdir(parents=True, exist_ok=True)
    (production / "build" / "script-style-audit.json").write_text(
        json.dumps(style, indent=2), encoding="utf-8")
    # Deterministic style violations are hard stops; heuristic signals still route private.
    hard += [f"script_style_gate {b['type']}: {b['detail']}" for b in style["blocked"]]
    warnings += [f"style {w['type']} x{w['count']}" for w in style["warns"]]

    # editorial gate needs build/sections.json (VO stage output), so pre-render we
    # can only validate the plan's structure against the parsed script.
    try:
        from produce import parse_sections
    except ModuleNotFoundError:
        from tools.produce import parse_sections

    plan_path = production / "scene-plan.json"
    if not plan_path.is_file():
        hard.append(f"editorial_gate: missing {plan_path.name}")
    else:
        errors = editorial_gate.validate_scene_plan(
            json.loads(plan_path.read_text(encoding="utf-8")),
            parse_sections(production), production=production, require_files=True)
        hard += [f"editorial_gate: {error}" for error in errors]

    return {
        "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "claimsVerdict": claims["verdict"],
        "styleStatus": style["verdict"],
        "hardFail": hard,
        "warnings": warnings,
    }


def collect_visual_gates(production):
    """Post-render geometry gate on the burned-in captions. Same shape as collect_gates.

    Runs only after produce.py has rendered — the captions have to exist as pixels
    before their geometry can be measured. Hard fails (safe-zone breach, caption
    over a chart, caption out of frame) block publishing; everything else is a
    warning that routes to publish-private like any other warning.
    """
    report = visual_qa.gate(production)
    return {
        "checkedAt": report["generated_at"],
        "visualStatus": report["status"],
        "contactSheets": report["contactSheets"],
        "hardFail": [f"visual_qa {f['clip']} @{f['t']:.2f}s: {f['problem']}" for f in report["hardFail"]],
        "warnings": [f"visual_qa: {w}" for w in report["warnings"]],
    }


# --- publish -----------------------------------------------------------------

def approve_batch(batch_path, privacy, gates):
    """Machine-approve every draft item at the decided privacy, exact-hash bound."""
    data = json.loads(batch_path.read_text(encoding="utf-8"))
    if data.get("schema") != "social-batch/v2":
        raise ValueError("post-close publishing requires social-batch/v2")
    stamp = gates["checkedAt"]
    for item in data["items"]:
        if item.get("status") != "draft":
            continue  # never touch an item the operator already ruled on
        item.update({
            "status": "approved", "privacy": privacy, "publicationAuthorized": True,
            "reviewedBy": "machine:daily-postclose-runner", "reviewedAt": stamp,
        })
        item["approvalSha256"] = approval_fingerprint(
            data["batchId"], item, data.get("containsSyntheticMedia", False), data["schema"])
    batch_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return load_social_batch(batch_path)  # re-validate through the unmodified validator


def publish_all(batch_path, data):
    """Publish each approved item. An unauthorized lane (TikTok) is skipped, not fatal."""
    try:
        from tools.publish import publish_batch_item, readiness_report
    except ModuleNotFoundError:
        from publish import publish_batch_item, readiness_report

    report, results = readiness_report(), []
    for item in [i for i in data["items"] if i["status"] == "approved"]:
        channel = item["channel"]
        if not report.get(channel, {}).get("ready"):
            log(f"SKIP {channel}: {report.get(channel, {}).get('status', 'unknown')}")
            results.append({"item": item["id"], "platform": channel, "status": "skipped"})
            continue
        try:
            entry = publish_batch_item(batch_path, item["id"])
            log(f"published {channel}: {entry['url']}")
            results.append({"item": item["id"], "platform": channel, "status": "published",
                            "url": entry["url"]})
        except (OSError, ValueError, RuntimeError) as error:
            log(f"FAIL {channel}: {error}")
            results.append({"item": item["id"], "platform": channel, "status": "failed",
                            "error": str(error)})
    return results


# --- run ---------------------------------------------------------------------

def _second_sunday(year, month):
    first = datetime(year, month, 1)
    return 1 + (6 - first.weekday()) % 7 + 7


def _first_sunday(year, month):
    first = datetime(year, month, 1)
    return 1 + (6 - first.weekday()) % 7


def eastern_now(utc=None):
    """US/Eastern without tzdata: this box has no zoneinfo database (ZoneInfoNotFoundError).
    US DST = 02:00 local on the 2nd Sunday of March through the 1st Sunday of November.
    """
    utc = utc or datetime.now(timezone.utc)
    naive = utc.replace(tzinfo=None)
    start = datetime(naive.year, 3, _second_sunday(naive.year, 3), 7)   # 02:00 EST = 07:00 UTC
    end = datetime(naive.year, 11, _first_sunday(naive.year, 11), 6)    # 02:00 EDT = 06:00 UTC
    return naive - timedelta(hours=4 if start <= naive < end else 5)


def is_publish_hour(utc=None):
    """18:00 US/Eastern. Windows tasks fire in local time, so the two ICT triggers
    that straddle US DST both exist and this guard drops the wrong one."""
    return eastern_now(utc).hour == 18


def run(production, dry_run=False, allow_public=False):
    production = Path(production).resolve()
    decision, reasons, gates = safe_decide(lambda: collect_gates(production))

    # Operator ruling 2026-07-20: a clean gate run still publishes PRIVATE unless
    # --allow-public is passed. editorial-gate.json's own doesNotProve list says the
    # gates cannot prove "the visual declaration matches the pixels", "full-size text
    # legibility", or "editorial quality" — so a machine-clean run is not evidence a
    # human would ship it. Morning promotion is the default public path. Flipping this
    # on trades ~14h of freshness for nobody having seen a frame before it goes live.
    if decision == PUBLIC and not allow_public:
        decision = PRIVATE
        reasons = ["public auto-publish not armed (--allow-public); gates were clean"]
    gates["decision"] = decision
    gates["allowPublic"] = allow_public
    log(f"decision: {decision}")
    for reason in reasons:
        log(f"  - {reason}")

    if decision == NO_PUBLISH:
        notify(f"TraderCockpit {production.name}: BLOCKED, nothing published.\n"
               + "\n".join(reasons[:20]))
        return 1

    if dry_run:
        log("dry run: stopping before approval, render, and publish")
        return 0

    try:
        machine_approve(production, gates)
        log("machine approval written (script + production), hash-bound to vo.txt")
        subprocess.run([sys.executable, str(ROOT / "tools" / "produce.py"), str(production),
                        "--stage", "all"], check=True)

        # Captions now exist as pixels, so their geometry can finally be checked.
        # This is the gap editorial-gate.json's own doesNotProve list named.
        visual_decision, visual_reasons, visual = safe_decide(
            lambda: collect_visual_gates(production))
        gates["visual"] = visual
        for reason in visual_reasons:
            log(f"  - {reason}")
        if visual_decision == NO_PUBLISH:
            gates.setdefault("hardFail", []).extend(visual["hardFail"])
            notify(f"TraderCockpit {production.name}: rendered, but VISUAL QA BLOCKED it. "
                   f"Nothing published.\nContact sheets: {', '.join(visual['contactSheets'][:3])}\n"
                   + "\n".join(visual_reasons[:20]))
            return 1
        if visual_decision == PRIVATE and decision == PUBLIC:
            decision = PRIVATE  # visual warnings route to private like any other warning
            gates["decision"] = decision
        gates.setdefault("warnings", []).extend(visual["warnings"])
        reasons += visual_reasons

        batch_path = production / "social-batch.json"
        data = approve_batch(batch_path, "public" if decision == PUBLIC else "private", gates)
        results = publish_all(batch_path, data)
    except Exception as error:  # noqa: BLE001 - never default to publishing
        log(f"ERROR after decision: {error!r}")
        notify(f"TraderCockpit {production.name}: run failed after {decision}: {error!r}")
        return 1

    summary = ", ".join(f"{r['platform']}={r['status']}" for r in results)
    if decision == PRIVATE:
        urls = ", ".join(r["url"] for r in results if r.get("url"))
        notify(f"TraderCockpit {production.name}: published PRIVATE, needs your review.\n"
               f"{summary}\n{urls}\n" + "\n".join(reasons[:20]))
        # The operator cannot judge a ping without the artifact (2026-07-21): attach the
        # master itself. Best-effort like notify(); a failed send never changes the decision.
        try:
            from tools.notify_telegram import send_video
        except ModuleNotFoundError:
            from notify_telegram import send_video
        try:
            send_video(production / "build" / "master.mp4",
                       f"REVIEW {production.name}: reply with approval to promote public, "
                       f"or notes to fix. {urls}")
        except (SystemExit, OSError) as error:
            log(f"WARN telegram video attach failed: {error}")
    elif any(r["status"] != "published" for r in results):
        notify(f"TraderCockpit {production.name}: public run, partial delivery.\n{summary}")
    log(f"done: {summary}")
    return 0


def selftest():
    # decide() is the pure gate verdict; run() downgrades PUBLIC->PRIVATE unless armed.
    assert decide({"hardFail": [], "warnings": []})[0] == PUBLIC
    assert decide({"hardFail": [], "warnings": ["style uniform rhythm"]})[0] == PRIVATE
    assert decide({"hardFail": [], "warnings": ["unsourced claim: c1 status=single_source"]})[0] == PRIVATE
    assert decide({"hardFail": ["claims_gate number_coverage"], "warnings": []})[0] == NO_PUBLISH
    # a hard fail outranks warnings, and reasons carry the blocking detail
    decision, reasons = decide({"hardFail": ["boom"], "warnings": ["style x1"]})
    assert (decision, reasons) == (NO_PUBLISH, ["boom"]), (decision, reasons)

    assert safe_decide(lambda: {"hardFail": [], "warnings": []})[0] == PUBLIC
    assert safe_decide(lambda: {"hardFail": [], "warnings": ["w"]})[0] == PRIVATE
    assert safe_decide(lambda: {"hardFail": ["b"], "warnings": []})[0] == NO_PUBLISH

    # visual gate bundles use the same shape, so decide() routes them identically:
    # a geometry hard fail is no-publish, a visual warning is private.
    assert decide({"hardFail": ["visual_qa clip.mp4 @1.00s: caption bottom breaches safe zone"],
                   "warnings": []})[0] == NO_PUBLISH
    assert decide({"hardFail": [], "warnings": ["visual_qa: no caption-free twin"]})[0] == PRIVATE
    assert visual_qa.safe_zone_breaches((100, 1850, 900, 1900), (1080, 1920),
                                        visual_qa.SAFE_ZONES["vertical"]), "vertical zones must bite"

    def explode():
        raise RuntimeError("gate crashed")

    decision, reasons, gates = safe_decide(explode)
    assert decision == NO_PUBLISH, decision
    assert "gate crashed" in reasons[0] and gates["hardFail"], (reasons, gates)

    # machine_approve is fail-closed on hard failures
    try:
        machine_approve(Path("."), {"hardFail": ["b"]})
        raise AssertionError("machine approval must refuse a hard failure")
    except ValueError:
        pass

    # publish-hour guard: 18:00 ET is 22:00 UTC in summer (EDT) and 23:00 UTC in winter (EST)
    assert is_publish_hour(datetime(2026, 7, 20, 22, 0, tzinfo=timezone.utc))
    assert not is_publish_hour(datetime(2026, 7, 20, 23, 0, tzinfo=timezone.utc))
    assert is_publish_hour(datetime(2026, 1, 20, 23, 0, tzinfo=timezone.utc))
    assert not is_publish_hour(datetime(2026, 1, 20, 22, 0, tzinfo=timezone.utc))

    print("daily-postclose self-test: 17/17 PASS")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("production", nargs="?",
                        help="production folder (contains vo.txt). Omit to resolve today's folder "
                             "by convention via daily_production_init — that is how the scheduled "
                             "task runs, so the trigger never carries a stale hardcoded path.")
    parser.add_argument("--dry-run", action="store_true", help="decide only; never publish")
    parser.add_argument("--at-publish-hour", action="store_true",
                        help="no-op unless it is currently the 18:00 US/Eastern hour")
    parser.add_argument("--allow-public", action="store_true",
                        help="arm public auto-publish on a clean gate run. Default is PRIVATE + "
                             "morning operator promotion: the gates cannot prove the pixels are "
                             "right (see editorial-gate doesNotProve).")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        selftest()
        return 0
    # Resolve today's production by convention when no path is given, and REFUSE to proceed
    # on an unready folder. A scheduled task pointed at a hardcoded path silently republishes
    # yesterday or no-ops on a missing folder, and from outside those look identical to a
    # working lane. The content step is an AGENT action (research -> vo.txt -> claims ->
    # scene-plan); no script produces it, so "not ready" means that step did not run.
    if not args.production:
        try:
            from tools.daily_production_init import check as production_check
        except ModuleNotFoundError:
            from daily_production_init import check as production_check
        readiness = production_check()
        if not readiness["ready"]:
            owed = ", ".join(item["file"] for item in readiness["missing"])
            log(f"production not ready: {readiness['slug']} missing {owed}")
            notify(f"TraderCockpit {readiness['slug']}: NO VIDEO — the content step did not "
                   f"finish. Missing: {owed}. Nothing was published.")
            return 1
        args.production = readiness["production"]
        log(f"resolved today's production: {readiness['slug']}")

    if args.at_publish_hour and not is_publish_hour():
        log("not the 18:00 US/Eastern hour; standing down")
        notify("TraderCockpit: post-close lane stood down — fired outside the 18:00 ET hour "
               "(box asleep or late trigger). No video today unless run manually.")
        return 0
    return run(args.production, args.dry_run, args.allow_public)


if __name__ == "__main__":
    raise SystemExit(main())
