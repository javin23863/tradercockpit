#!/usr/bin/env python3
"""Build a reference corpus of how market people ACTUALLY talk, from their own transcripts.

Operator, 2026-07-28: "You're using unnatural words and combinations together that people who
read and understand and listen to financial markets don't speak... it sounds like you
personally wrote it." A hand-written banned-phrase list cannot fix that, because the author of
the list is the same writer producing the tells. The only honest reference is what the
professionals said, in their own words, at length.

Source is YouTube auto-captions from named market outlets (Bloomberg, Reuters and the daily
market-wrap channels the operator pointed at). Captions only -- no video is downloaded.

    python tools/vocab_corpus.py --build            # fetch + profile into corpus/
    python tools/vocab_corpus.py --add <url|id>     # add one more source
    python tools/vocab_corpus.py --stats

The profile is n-gram frequency, not a rulebook. `tools/ai_tell_gate.py` reads it.
"""
from __future__ import annotations

import argparse
import collections
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus"
YTDLP = Path(r"C:\Users\MSI\.claude\skills\see-video\bin\yt-dlp.exe")

# Channels the operator named plus the daily-recap format the show competes with. Playlists
# and channel tabs are fine -- --max is what bounds the pull.
# Channel front pages were the first attempt and they are the WRONG slice: the latest uploads
# from a broadcaster are mostly general news, and the resulting 203k-word corpus contained no
# "vix", no "s&p", no "resistance" and no "bid". A corpus that never says VIX cannot judge
# whether a market script sounds like market people. Search the format instead of the outlet.
SOURCES = [
    "ytsearch14:stock market today recap S&P 500 close",
    "ytsearch14:closing bell market wrap today stocks",
    "ytsearch14:technical analysis S&P 500 support resistance daily",
    "ytsearch14:SPX levels to watch tomorrow trading",
    "ytsearch14:nasdaq nvidia selloff market analysis",
    "ytsearch10:bloomberg markets close stocks bonds",
    "https://www.youtube.com/@markets/videos",          # Bloomberg Television / Markets
    # Second pass 2026-07-28. The first pass looked like 169 documents and was 72 videos
    # (caption variants -- see load_docs). 72 is too thin to set a percentile threshold on, so
    # widen the format queries rather than the outlet list.
    "ytsearch20:daily market recap stocks close today analysis",
    "ytsearch20:market wrap up today what happened stocks",
    "ytsearch20:S&P 500 technical analysis today key levels",
    "ytsearch20:nasdaq technical analysis today levels to watch",
    "ytsearch20:stock market outlook tomorrow trading plan",
    "ytsearch20:VIX volatility analysis market today",
    "ytsearch20:where is the market going support resistance trade setup",
    "ytsearch20:after hours market recap earnings reaction stocks",
]
TAG_RE = re.compile(r"<[^>]+>")
CUE_RE = re.compile(r"^\d\d:\d\d:\d\d[.,]\d+\s+-->")
WORD_RE = re.compile(r"[a-z][a-z'&-]*")


def fetch(target: str, limit: int, out_dir: Path) -> int:
    """Pull auto-captions for up to `limit` videos. Returns how many vtt files landed."""
    before = len(list(out_dir.glob("*.vtt")))
    subprocess.run([
        str(YTDLP), "--skip-download", "--write-auto-subs", "--write-subs",
        "--sub-langs", "en.*", "--sub-format", "vtt",
        "--playlist-end", str(limit), "--ignore-errors", "--no-warnings",
        "--match-filter", "duration > 120 & duration < 3600",
        "-o", str(out_dir / "%(id)s.%(ext)s"), target,
    ], capture_output=True, text=True, timeout=1800)
    return len(list(out_dir.glob("*.vtt"))) - before


def vtt_text(path: Path) -> str:
    """Caption text with cue timings, markup and the duplicate rolling lines removed."""
    lines, seen = [], None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        # Entities MUST die before tokenising: unescaped, "S&P" arrives as "s &amp; p" and the
        # corpus ends up with no token "s&p" at all -- which made the gate flag the single most
        # common phrase in market speech as out-of-register. `&gt;&gt;` speaker markers likewise
        # became the corpus's top bigram ("gt gt", 1691).
        line = TAG_RE.sub("", html.unescape(raw)).strip()
        if not line or line == "WEBVTT" or CUE_RE.match(line) or "-->" in line:
            continue
        if line.startswith(("Kind:", "Language:")) or line.isdigit():
            continue
        if line == seen:            # auto-captions repeat the previous line as they scroll
            continue
        seen = line
        lines.append(line)
    return " ".join(lines)


def load_docs(raw: Path) -> list[list[str]]:
    """One token list per VIDEO, deduplicated across caption variants.

    yt-dlp writes `<id>.en.vtt`, `<id>.en-orig.vtt` and `<id>.en-en.vtt` for the same
    captions. Counting all three was a silent corpus poisoning: 169 files were 72 videos, every
    count was tripled, real singletons vanished so the top-N truncation discarded genuinely
    common bigrams ("takes a", "biggest name"), and leave-one-out stopped being leave-one-out --
    a document's own duplicates kept supporting it after its counts were subtracted. That is
    what made real transcripts look 3x more idiomatic than they are.
    """
    by_id: dict[str, list[Path]] = {}
    for vtt in sorted(raw.glob("*.vtt")):
        by_id.setdefault(vtt.name.split(".")[0], []).append(vtt)
    docs = []
    for variants in by_id.values():
        pick = min(variants, key=lambda p: (".en.vtt" not in p.name, len(p.name)))
        words = WORD_RE.findall(vtt_text(pick).lower())
        if len(words) > 200:
            docs.append(words)
    return docs


def profile(docs: list[list[str]]) -> dict:
    grams = {n: collections.Counter() for n in (1, 2, 3)}
    total = 0
    for words in docs:
        total += len(words)
        for n in grams:
            for i in range(len(words) - n + 1):
                grams[n][" ".join(words[i:i + n])] += 1
    # Retain by EVIDENCE, not by rank. A top-N cut silently drops common phrasing once the
    # corpus grows, and the size of the cut then decides the gate's verdict. Count >= 2 keeps
    # anything two speakers (or one speaker twice) actually said and drops caption noise.
    keep = lambda counter, floor: {k: v for k, v in counter.items() if v >= floor}  # noqa: E731
    return {
        "documents": len(docs),
        "words": total,
        "unigrams": keep(grams[1], 1),
        "bigrams": keep(grams[2], 2),
        "trigrams": keep(grams[3], 2),
    }


def build(targets: list[str], limit: int) -> dict:
    CORPUS.mkdir(exist_ok=True)
    raw = CORPUS / "transcripts"
    raw.mkdir(exist_ok=True)
    for target in targets:          # empty when re-profiling the cached transcripts
        got = fetch(target, limit, raw)
        print(f"  {target} -> {got} new transcript(s)")
    docs = load_docs(raw)
    if not docs:
        sys.exit("no transcripts collected; check network or yt-dlp")
    data = profile(docs)
    (CORPUS / "profile.json").write_text(json.dumps(data), encoding="utf-8")
    print(f"  corpus: {data['documents']} videos, {data['words']:,} words, "
          f"{len(data['bigrams']):,} bigrams")
    return data


def selftest():
    """The dedupe and the entity-unescape are what two wrong verdicts came from. Pin both."""
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp)
        body = "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n" + "the s&amp;p held its level today " * 40
        for name in ("vid1.en.vtt", "vid1.en-orig.vtt", "vid1.en-en.vtt", "vid2.en-orig.vtt"):
            (raw / name).write_text(body, encoding="utf-8")
        docs = load_docs(raw)
        assert len(docs) == 2, f"3 caption variants of vid1 must collapse to 1 doc, got {docs and len(docs)}"
        assert "s&p" in docs[0], "HTML entities must be unescaped before tokenising"
        assert "amp" not in docs[0], "&amp; leaked into the token stream"
        data = profile(docs)
        assert data["documents"] == 2, data["documents"]
        # count >= 2 retention: a bigram said 80 times survives, a one-off does not.
        assert data["bigrams"]["s&p held"] >= 2
        (raw / "vid3.en.vtt").write_text("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\ntoo short\n",
                                         encoding="utf-8")
        assert len(load_docs(raw)) == 2, "documents under 200 words must be dropped"
    print("vocab_corpus selftest: 6/6")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--add", metavar="URL")
    ap.add_argument("--limit", type=int, default=12, help="videos per source")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--reprofile", action="store_true",
                    help="re-derive profile.json from cached transcripts, no fetching")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.reprofile:
        build([], a.limit); return 0
    if a.stats:
        data = json.loads((CORPUS / "profile.json").read_text(encoding="utf-8"))
        print(f"{data['documents']} transcripts, {data['words']:,} words")
        for gram in ("unigrams", "bigrams", "trigrams"):
            top = list(data[gram].items())[:12]
            print(f"  {gram}: " + ", ".join(f"{k}({v})" for k, v in top))
        return 0
    build([a.add] if a.add else SOURCES, a.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
