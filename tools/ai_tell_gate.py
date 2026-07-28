#!/usr/bin/env python3
"""Score a script against how market people actually talk, not against my judgment.

Operator, 2026-07-28: "The AI tell detector is not strong enough... it sounds like you
personally wrote it." The old detector was a hand-written pattern list, which cannot work:
the person writing the list is the person producing the tells. This one compares the script
to `corpus/profile.json` -- 452k words of real market-recap transcripts built by
`tools/vocab_corpus.py`.

    python tools/ai_tell_gate.py productions/daily-<date> [--json]
    python tools/ai_tell_gate.py --baseline      # re-derive thresholds from the corpus

Thresholds live in `corpus/thresholds.json`, written by `--baseline` and fingerprinted to the
corpus they came from -- scoring against a different corpus is a hard error, not a warning.
They are the corpus's OWN p95, LEAVE-ONE-OUT: each video is scored against a profile with its
own counts subtracted, so a document is never its own evidence. Roughly 5% of real market
transcripts exceed each limit by construction; the gate asks a script to phrase like the bulk
of market speech, not like every outlier in it.

Two measurement bugs, both of which produced confident wrong verdicts before they were found:

1. Self-inclusion. The first cut scored each document against a profile containing it and
   reported out-of-register max = 0 -- arithmetically guaranteed, and it told us nothing.
2. Duplicate documents. yt-dlp had written 2-3 caption variants per video, so 169 "documents"
   were 72 videos. Leave-one-out subtracted one copy and left the others still vouching for
   it, which put the real-transcript unseen-bigram rate at 15.9% when the true figure is
   ~40%. A correctly-written script was blocked at 47% against a threshold built on that
   fiction. `vocab_corpus.load_docs` now deduplicates by video id.

The lesson is the gate's own: a threshold is only meaningful against the exact corpus it was
measured on, which is why the fingerprint is checked on every run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "corpus" / "profile.json"
THRESHOLDS = ROOT / "corpus" / "thresholds.json"
WORD_RE = re.compile(r"[a-z][a-z'&-]*")
COPULA = {"is", "are", "was", "were", "be", "been"}

def load_thresholds() -> dict:
    """Thresholds, refusing to run if they were derived from a different corpus.

    Hard-coded constants were wrong twice in one day: once because the corpus counted every
    video 2-3 times, once because the corpus then grew. An unseen-bigram rate is only
    meaningful against the exact profile it was measured on, so the fingerprint is checked
    rather than trusted.
    """
    if not THRESHOLDS.is_file():
        sys.exit(f"no thresholds at {THRESHOLDS}; run tools/ai_tell_gate.py --baseline")
    t = json.loads(THRESHOLDS.read_text(encoding="utf-8"))
    p = load_profile()
    if (t["corpus"]["documents"], t["corpus"]["words"]) != (p["documents"], p["words"]):
        sys.exit(f"thresholds were derived from {t['corpus']['documents']} videos / "
                 f"{t['corpus']['words']:,} words but the corpus now holds "
                 f"{p['documents']} / {p['words']:,}. Re-run --baseline.")
    return t

# Tickers, outlets and proper nouns a transcript's captions spell differently. Absence from
# the corpus says nothing about register for these.
ALLOW = {"xlk", "spx", "ixic", "nvda", "s&p", "nasdaq", "nvidia", "vix", "tradercockpit",
         "iran", "monday", "tuesday", "friday", "february", "august", "december"}

# Sentence shapes that read as essay rather than desk talk. Kept SMALL on purpose: the
# corpus comparison is the real detector, and these only name what it cannot see.
ESSAY_PATTERNS = (
    (r"\b(?:that|this) is (?:the|a|what|why|where|how)\b", "definitional 'that is the ...'"),
    (r"\bwhat (?:matters|counts) (?:is|more)\b", "'what matters is' framing"),
    (r"\b(?:everything|nothing) else is\b", "aphoristic closer"),
    (r"\bboth of those (?:things )?are true\b", "essay balance line"),
    (r"\bthe (?:whole|entire) (?:tension|point|story) (?:in|of)\b", "thesis-statement voice"),
    (r"\bis the only honest\b", "moralising closer"),
)


def load_profile():
    if not PROFILE.is_file():
        sys.exit(f"no corpus at {PROFILE}; run tools/vocab_corpus.py --build")
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def script_body(production: Path) -> str:
    """Spoken lines only.

    This dropped `## slot` headers and kept EVERYTHING ELSE, including the `#` provenance
    header every vo.txt in this series opens with -- router order, ruling history, the
    not-negotiable list. That is engineering prose nobody says out loud, and measuring it as
    narration is what the two BLOCK verdicts on 2026-07-28 were made of: ep02 and ep03 both
    failed on unseen bigrams whose top offenders read `ep narration, narration v, v written,
    written against, the contract, contract router, router order, order gtm, gtm readme`.
    Those are header words. Neither episode's voice track contains one of them.

    This is not a relaxed threshold -- the bar is untouched. It is the gate finally reading its
    own stated subject. `#` never begins a spoken line; the TTS emitter skips them too.
    """
    vo = (production / "vo.txt").read_text(encoding="utf-8")
    return "\n".join(ln for ln in vo.splitlines()
                     if not ln.lstrip().startswith("#") and not ln.startswith("==="))


def score(text: str, profile: dict, limits: dict) -> dict:
    copula_max = limits["copula"]
    unseen_max = limits["unseen"]
    oor_max = limits["outOfRegister"]
    uni, bi = profile["unigrams"], profile["bigrams"]
    words = WORD_RE.findall(text.lower())
    if not words:
        return {"verdict": "BLOCK", "findings": [{"type": "empty", "detail": "no words"}]}
    copula = 100 * sum(1 for w in words if w in COPULA) / len(words)
    bigrams = [" ".join(words[i:i + 2]) for i in range(len(words) - 1)]
    unseen = [b for b in bigrams if b not in bi]
    unseen_pct = 100 * len(unseen) / len(bigrams)
    out_of_register = sorted({w for w in words if w not in uni and w not in ALLOW
                              and not w.isdigit() and len(w) > 3})
    essay = [(label, m.group(0)) for pattern, label in ESSAY_PATTERNS
             for m in re.finditer(pattern, text, re.I)]

    findings = []
    if copula > copula_max:
        findings.append({"type": "copula", "value": round(copula, 2), "limit": copula_max,
                         "detail": f"{copula:.2f}% of words are is/are/was/were against a "
                                   f"corpus p95 of {copula_max}%. Definitional sentences "
                                   f"('X is Y') are the essay register; desks narrate actions."})
    if unseen_pct > unseen_max:
        findings.append({"type": "unseen_bigrams", "value": round(unseen_pct, 1),
                         "limit": unseen_max,
                         "detail": f"{unseen_pct:.1f}% of word pairs never occur twice in the "
                                   f"corpus of market speech; 95% of real transcripts stay "
                                   f"under {unseen_max}%.",
                         "examples": unseen[:25]})
    if len(out_of_register) > oor_max:
        findings.append({"type": "out_of_register", "value": len(out_of_register),
                         "limit": oor_max,
                         "detail": "words that never appear in the corpus",
                         "examples": out_of_register})
    for label, hit in essay:
        findings.append({"type": "essay_shape", "detail": label, "examples": [hit]})

    return {
        "verdict": "BLOCK" if findings else "PASS",
        "metrics": {"words": len(words), "copulaPct": round(copula, 2),
                    "unseenBigramPct": round(unseen_pct, 1),
                    "outOfRegisterWords": len(out_of_register)},
        "corpus": {"documents": profile["documents"], "words": profile["words"]},
        "outOfRegister": out_of_register,
        "findings": findings,
    }


def baseline(sample_words: int = 1450):
    """Re-derive the thresholds from the corpus, leave-one-out.

    Each transcript is scored against the profile MINUS its own counts, so no document
    supports itself. Without that subtraction out-of-register measures 0 by construction.
    """
    import collections
    sys.path.insert(0, str(ROOT / "tools"))
    from vocab_corpus import CORPUS, load_docs  # noqa: E402

    # MUST be the same de-duplicated loader the profile uses. Baselining over raw *.vtt counted
    # each video 2-3 times, so subtracting one document still left its own copies supporting it
    # and "leave-one-out" measured nothing.
    docs = load_docs(CORPUS / "transcripts")
    if not docs:
        sys.exit("no transcripts to baseline against")
    g1, g2 = collections.Counter(), collections.Counter()
    for w in docs:
        g1.update(w)
        g2.update(" ".join(w[i:i + 2]) for i in range(len(w) - 1))
    # Retention thresholds mirror profile(): unigrams count >= 1, bigrams count >= 2, applied
    # AFTER the document's own counts come out.

    stats = {"copula": [], "unseen": [], "outOfRegister": []}
    for w in docs:
        if len(w) < sample_words - 250:
            continue
        d1, d2 = collections.Counter(w), collections.Counter(
            " ".join(w[i:i + 2]) for i in range(len(w) - 1))
        seg = w[:sample_words]
        bg = [" ".join(seg[i:i + 2]) for i in range(len(seg) - 1)]
        stats["copula"].append(100 * sum(1 for x in seg if x in COPULA) / len(seg))
        stats["unseen"].append(100 * sum(1 for b in bg if g2[b] - d2[b] < 2) / len(bg))
        stats["outOfRegister"].append(len({x for x in seg if len(x) > 3
                                           and g1[x] - d1[x] < 1}))
    print(f"leave-one-out over {len(stats['copula'])} videos at {sample_words} words")
    limits, dist = {}, {}
    for name, values in stats.items():
        v = sorted(values)
        q = lambda p: v[min(len(v) - 1, int(p * len(v)))]  # noqa: E731
        dist[name] = {"mean": round(sum(v) / len(v), 2), "p90": round(q(.90), 2),
                      "p95": round(q(.95), 2), "max": round(v[-1], 2)}
        # p95: the gate asks a script to phrase like 95% of real market speech. Rounding out
        # to whole numbers so a one-video corpus change does not move a published verdict.
        limits[name] = round(q(.95), 1) if name != "outOfRegister" else int(q(.95))
        print(f"  {name:14} mean {dist[name]['mean']:6.2f}  p90 {dist[name]['p90']:6.2f}  "
              f"p95 {dist[name]['p95']:6.2f}  max {dist[name]['max']:6.2f}   -> limit "
              f"{limits[name]}")
    profile = load_profile()
    THRESHOLDS.write_text(json.dumps({
        "limits": limits, "distribution": dist, "sampleWords": sample_words,
        "videos": len(stats["copula"]),
        "corpus": {"documents": profile["documents"], "words": profile["words"]},
    }, indent=2), encoding="utf-8")
    print(f"  -> {THRESHOLDS}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("production", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--baseline", action="store_true",
                    help="re-derive thresholds from the corpus, leave-one-out")
    a = ap.parse_args()
    if a.baseline:
        return baseline()
    if not a.production:
        ap.error("production is required")
    production = Path(a.production)
    limits = load_thresholds()
    report = score(script_body(production), load_profile(), limits["limits"])
    report["thresholdSource"] = {k: limits[k] for k in ("videos", "corpus", "sampleWords")}
    build = production / "build"
    build.mkdir(exist_ok=True)
    (build / "ai-tell-gate.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if a.json:
        print(json.dumps(report, indent=2))
    else:
        m = report["metrics"]
        lim = limits["limits"]
        print(f"ai_tell_gate: {report['verdict']} -- {m['words']} words, "
              f"copula {m['copulaPct']}% (max {lim['copula']}), "
              f"unseen bigrams {m['unseenBigramPct']}% (max {lim['unseen']}), "
              f"out-of-register {m['outOfRegisterWords']} (max {lim['outOfRegister']})")
        print(f"  thresholds from {limits['videos']} videos / "
              f"{limits['corpus']['words']:,} words")
        for f in report["findings"]:
            print(f"  - {f['type']}: {f['detail']}")
            if f.get("examples"):
                print(f"      {', '.join(map(str, f['examples'][:12]))}")
    return 1 if report["verdict"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
