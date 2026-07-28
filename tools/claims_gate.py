#!/usr/bin/env python
"""claims_gate.py -- fail-closed ontology-receipt gate for the TraderCockpit news pipeline.

Binary PASS/BLOCK. No soft state. Independent of the script-writing LLM.
Modeled on Palantir OAG + hft3 truth-layer discipline.

Usage:
    python tools/claims_gate.py productions/<vid>
    python tools/claims_gate.py --selftest
"""
import sys, os, re, json, glob, datetime
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # ponytail: Windows console mangles em-dashes otherwise

REQUIRED_CLAIM_FIELDS = ("id", "value", "as_of", "source", "retrieved_at", "status")
STATUSES = {"verified", "single_source", "unverified"}

CARDINALS = set("""zero one two three four five six seven eight nine ten eleven twelve
thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty
sixty seventy eighty ninety hundred thousand million billion trillion""".split())
FRACTIONS = {"half", "quarter", "fifth"}
ORDINALS = set("""first second third fourth fifth sixth seventh eighth ninth tenth
eleventh twelfth thirteenth fourteenth fifteenth sixteenth seventeenth eighteenth
nineteenth twentieth thirtieth fortieth fiftieth sixtieth seventieth eightieth
ninetieth hundredth thousandth""".split())
NUMBER_WORDS = CARDINALS | FRACTIONS | ORDINALS
# ponytail: small hand-picked unit list for the "one"-as-pronoun allowlist exception, not exhaustive
UNIT_WORDS = {"percent", "cent", "dollars", "dollar", "miles", "kilometres", "kilometers", "barrels", "cents"}
STALE_PREDICATE_RE = re.compile(r"close|price|level|yield", re.I)

TOKEN_RE = re.compile(r"\d+|[A-Za-z]+")
WS_RE = re.compile(r"\s+")

FEED_SOURCE_RE = re.compile(r"ohlcv-feed-receipts")
# Closed vocabulary for feed-sourced claims. The tuple is the path inside dashboard.<SYMBOL>
# that the claim's value must match; None = arithmetic over two fields, nothing single to
# cross-check. An unlisted predicate BLOCKS: it would otherwise be a free hole in check 6.
FEED_PREDICATES = {
    "prior_open": ("prior", "open"), "prior_high": ("prior", "high"),
    "prior_low": ("prior", "low"), "prior_close": ("prior", "close"),
    "session_open": ("session", "open"), "session_high": ("session", "high"),
    "session_low": ("session", "low"), "session_close": ("session", "close"),
    "session_return": ("returnPercent",),
    "close_minus_prior": None, "open_minus_prior_close": None, "close_minus_open": None,
    "open_minus_close": None, "high_minus_low": None, "close_minus_low": None,
    "high_minus_close": None, "low_minus_prior_close": None,
}
# Golden-derived from daily-2026-07-27: the recital sections 03-07 each cite 8-10 distinct
# feed claims of ONE instrument, while the level-map sections 10-12 the operator asked for
# cite at most 4. A cap of 5 blocks the first and leaves the second a slot of headroom.
RECITAL_CAP = 5


def to_float(v):
    try:
        return float(str(v).replace(",", "").rstrip("%"))
    except ValueError:
        return None


def decimals(v):
    s = str(v)
    return len(s.split(".")[1]) if "." in s else 0


def norm_ws(s):
    return WS_RE.sub(" ", s).strip()


def parse_sections(vo_text):
    """Split vo.txt into {'NN': narration_text} by '## NN slug' headers; # lines dropped."""
    sections, cur_id, buf = {}, None, []
    for line in vo_text.splitlines():
        if line.startswith("## "):
            if cur_id is not None:
                sections[cur_id] = "\n".join(buf).strip()
            m = re.match(r"##\s+(\S+)", line)
            cur_id = m.group(1)
            buf = []
        elif line.strip().startswith("#"):
            continue  # comment line, ignored per spec
        else:
            buf.append(line)
    if cur_id is not None:
        sections[cur_id] = "\n".join(buf).strip()
    return sections


def tokenize(text):
    return [(m.group(0).lower(), m.start(), m.end()) for m in TOKEN_RE.finditer(text)]


CLAUSE_BREAK_RE = re.compile(r"[.!?—]")  # sentence end or em-dash: never merge a region across these


def find_number_regions(text, gap=2):
    """Number-bearing spans: digits, longhand cardinals/ordinals/fractions, percent.
    Adjacent hits (<= `gap` non-hit tokens between, and no clause break between them) merge
    into one region. 'one' alone is noise unless within `gap` tokens of another number word
    or a unit.
    # ponytail: gap calibrated to 2 (spec said "~3") against the real video-02 script — 3 let
    # a name ("S and P five hundred") bleed into an unrelated number two clauses later; a hard
    # break on . ! ? and em-dash catches the rest (sentence/clause boundaries never merge)."""
    toks = tokenize(text)
    n = len(toks)
    flags = [False] * n
    for i, (t, s, e) in enumerate(toks):
        if t.isdigit() or (t in NUMBER_WORDS and t != "one") or t == "percent":
            flags[i] = True
        elif t == "one":
            lo, hi = max(0, i - gap), min(n, i + gap + 1)
            if any((toks[j][0] in NUMBER_WORDS and toks[j][0] != "one") or toks[j][0] in UNIT_WORDS
                   for j in range(lo, hi) if j != i):
                flags[i] = True
    regions = []
    i = 0
    while i < n:
        if not flags[i]:
            i += 1
            continue
        last, misses, j = i, 0, i + 1
        while j < n:
            if CLAUSE_BREAK_RE.search(text[toks[j - 1][2]:toks[j][1]]):
                break
            if flags[j]:
                last, misses = j, 0
            else:
                misses += 1
                if misses > gap:
                    break
            j += 1
        start, end = toks[i][1], toks[last][2]
        regions.append((start, end, text[start:end]))
        i = last + 1
    return regions


def context_words(text, start, end, n=8):
    words = list(re.finditer(r"\S+", text))
    idxs = [i for i, m in enumerate(words) if m.end() > start and m.start() < end]
    if not idxs:
        return text[start:end]
    lo, hi = max(0, idxs[0] - n), min(len(words), idxs[-1] + 1 + n)
    return " ".join(w.group(0) for w in words[lo:hi])


def parse_as_of(v):
    v = str(v)
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", v)
    if m:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"(\d{4})-(\d{2})$", v)
    if m:
        return datetime.date(int(m.group(1)), int(m.group(2)), 1)
    return None  # ponytail: unparseable as_of (e.g. "static-geography") -> skip staleness, can't judge


def run_checks(sections, claims, receipts, today=None, feed_receipts=None):
    """Core gate logic, file-format-agnostic. Returns (blocked, warns).

    `feed_receipts` maps a receipt FILENAME to its parsed JSON, so a claim source of
    `ohlcv-feed-receipts-<date>.json#SP:SPX` resolves exactly."""
    today = today or datetime.date.today()
    blocked, warns = [], []

    # 1. schema
    seen_ids = set()
    claim_by_id = {}
    for c in claims:
        missing = [f for f in REQUIRED_CLAIM_FIELDS if f not in c or c.get(f) in (None, "")]
        if missing:
            blocked.append({"type": "schema", "detail": f"claim missing fields {missing}: {c.get('id', '<no id>')}"})
            continue
        if c["status"] not in STATUSES:
            blocked.append({"type": "schema", "detail": f"claim {c['id']} bad status {c['status']!r}"})
        if c["id"] in seen_ids:
            blocked.append({"type": "schema", "detail": f"duplicate claim id {c['id']}"})
        seen_ids.add(c["id"])
        claim_by_id[c["id"]] = c

    for sec, rs in receipts.items():
        for r in rs:
            if "quote" not in r or "claim" not in r:
                blocked.append({"type": "schema", "section": sec, "detail": f"receipt missing quote/claim: {r}"})
                continue
            if r["claim"] not in claim_by_id:
                blocked.append({"type": "schema", "section": sec, "detail": f"receipt claim id not found: {r['claim']}"})

    # 2. quote integrity
    for sec, rs in receipts.items():
        sec_norm = norm_ws(sections.get(sec, ""))
        if sec not in sections:
            blocked.append({"type": "quote_integrity", "section": sec, "detail": "receipt section not in vo.txt"})
            continue
        for r in rs:
            if "quote" not in r:
                continue
            if norm_ws(r["quote"]) not in sec_norm:
                blocked.append({"type": "quote_integrity", "section": sec, "detail": f"quote not found verbatim in section: {r['quote']!r}"})

    # 3. status gate
    for sec, rs in receipts.items():
        for r in rs:
            c = claim_by_id.get(r.get("claim"))
            if c is None:
                continue  # already flagged by schema check
            status = c["status"]
            if status == "unverified":
                blocked.append({"type": "status_gate", "section": sec, "detail": f"claim {c['id']} is unverified, banned from script"})
            elif status == "single_source" and not r.get("attributed"):
                blocked.append({"type": "status_gate", "section": sec, "detail": f"claim {c['id']} is single_source but receipt not attributed"})

    # 4. number coverage -- spec: region must fall inside the span of AT LEAST ONE receipt quote
    # (not a union of several); run on normalized text so region spans line up with quote text.
    for sec, text in sections.items():
        norm_text = norm_ws(text)
        rs = receipts.get(sec, [])
        quotes_norm = [norm_ws(r["quote"]) for r in rs if "quote" in r]
        for start, end, region_text in find_number_regions(norm_text):
            if not any(region_text in q for q in quotes_norm):
                blocked.append({
                    "type": "number_coverage", "section": sec,
                    "detail": f"uncovered number '{region_text}' in context: ...{context_words(norm_text, start, end)}...",
                })

    # 5. staleness (warn only)
    for c in claims:
        if c.get("status") not in STATUSES or "as_of" not in c:
            continue
        if not STALE_PREDICATE_RE.search(str(c.get("predicate", ""))):
            continue
        d = parse_as_of(c["as_of"])
        if d is not None and (today - d).days > 30:
            warns.append({"type": "staleness", "claim": c["id"],
                          "detail": f"{c['id']} as_of={c['as_of']} predicate={c.get('predicate')}"})

    # 6. feed-claim schema. A feed claim must name a closed-vocabulary predicate and an
    # instrument that resolves under the receipt's `dashboard` object -- NOT the top level,
    # which carries zero instruments; specified there this check would fail closed on every
    # legitimate feed claim. The value is then cross-checked against the field the predicate
    # names, at the claim's own precision (the script rounds 0.0162 -> 0.02).
    feed_receipts = feed_receipts or {}
    instrument_of = {}
    for c in claims:
        src = str(c.get("source", ""))
        if not FEED_SOURCE_RE.search(src):
            continue
        cid = c.get("id", "<no id>")
        if "#" not in src:
            blocked.append({"type": "feed_schema", "detail": f"claim {cid} cites the feed with no #instrument fragment"})
            continue
        filename, frag = src.split("#", 1)
        if c.get("predicate") not in FEED_PREDICATES:
            blocked.append({"type": "feed_schema",
                            "detail": f"claim {cid} predicate {c.get('predicate')!r} is outside the feed vocabulary"})
        dashboard = (feed_receipts.get(filename) or {}).get("dashboard")
        if not isinstance(dashboard, dict):
            blocked.append({"type": "feed_schema", "detail": f"claim {cid} cites {filename}, which is missing or has no dashboard"})
            continue
        if frag not in dashboard:
            blocked.append({"type": "feed_schema", "detail": f"claim {cid} instrument {frag} is not in {filename} dashboard"})
            continue
        instrument_of[cid] = frag
        path = FEED_PREDICATES.get(c.get("predicate"))
        if not path:
            continue  # derived arithmetic: no single receipt field to compare against
        expected = dashboard[frag]
        for key in path:
            expected = expected.get(key) if isinstance(expected, dict) else None
        actual = to_float(c.get("value"))
        dotted = ".".join(path)
        if expected is None or actual is None:
            blocked.append({"type": "feed_schema", "detail": f"claim {cid} value {c.get('value')!r} cannot be cross-checked against {dotted}"})
        elif round(float(expected), decimals(c["value"])) != actual:
            blocked.append({"type": "feed_schema", "detail": f"claim {cid} value {c['value']} != receipt {dotted} {expected}"})

    # 7. recital cap per (section, instrument). Attribution is the `#` fragment, never
    # `subject` -- `subject` is optional (see REQUIRED_CLAIM_FIELDS), so a writer could split
    # one instrument across spellings and duck the cap.
    for sec, rs in receipts.items():
        per = {}
        for cid in {r.get("claim") for r in rs}:
            if cid in instrument_of:
                per.setdefault(instrument_of[cid], set()).add(cid)
        for inst, ids in sorted(per.items()):
            if len(ids) > RECITAL_CAP:
                blocked.append({"type": "recital", "section": sec,
                                "detail": f"{inst}: {len(ids)} distinct feed claims in one section, "
                                          f"cap is {RECITAL_CAP} ({', '.join(sorted(ids))})"})

    # 8. alternate-source laundering (WARN). Re-sourcing a feed number to a news URL ducks
    # checks 6 and 7 entirely; this cannot be blocked without breaking legitimate reporting
    # of the same figure, so it routes to the supervised review.
    feed_values, stack = set(), [(p or {}).get("dashboard") for p in feed_receipts.values()]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            stack.extend(node.values())
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            feed_values.add(round(float(node), 4))
    for c in claims:
        if FEED_SOURCE_RE.search(str(c.get("source", ""))):
            continue
        v = to_float(c.get("value"))
        if v is not None and round(v, 4) in feed_values:
            warns.append({"type": "laundering", "claim": c.get("id"),
                          "detail": f"{c.get('id')} value {c.get('value')} is in the session feed receipt "
                                    f"but is sourced to {c.get('source')}"})

    return blocked, warns


def gate(vid_dir):
    vo_path = os.path.join(vid_dir, "vo.txt")
    claims_path = os.path.join(vid_dir, "claims.yaml")
    receipts_path = os.path.join(vid_dir, "vo-receipts.yaml")

    with open(vo_path, encoding="utf-8") as f:
        sections = parse_sections(f.read())
    with open(claims_path, encoding="utf-8") as f:
        claims = yaml.safe_load(f) or []
    with open(receipts_path, encoding="utf-8") as f:
        receipts = yaml.safe_load(f) or {}
    feed_receipts = {}
    for path in sorted(glob.glob(os.path.join(vid_dir, "ohlcv-feed-receipts*.json"))):
        with open(path, encoding="utf-8") as f:
            feed_receipts[os.path.basename(path)] = json.load(f)

    blocked, warns = run_checks(sections, claims, receipts, feed_receipts=feed_receipts)

    report = {
        "verdict": "BLOCK" if blocked else "PASS",  # fail-closed: never PASS if blocked is non-empty
        "checked_sections": len(sections),
        "claims_total": len(claims),
        "receipts_total": sum(len(v) for v in receipts.values()),
        "blocked": blocked,
        "warns": warns,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }

    build_dir = os.path.join(vid_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    out_path = os.path.join(build_dir, "claims-gate.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"claims_gate: {report['verdict']} -- {report['checked_sections']} sections, "
          f"{report['claims_total']} claims, {report['receipts_total']} receipts")
    if warns:
        print(f"  {len(warns)} warn(s):")
        for w in warns:
            print(f"    - {w['type']}: {w['detail']}")
    if blocked:
        print(f"  {len(blocked)} block(s):")
        for b in blocked:
            loc = f"[{b['section']}] " if b.get("section") else ""
            print(f"    - {b['type']} {loc}{b['detail']}")
    print(f"  report: {out_path}")
    return report


def selftest():
    # case 1: uncovered number -> BLOCK
    sections = {"01": "Revenue grew twelve percent this quarter."}
    claims = [{"id": "c1", "value": "12%", "as_of": "2026-07-13", "source": "x", "retrieved_at": "2026-07-13", "status": "verified", "predicate": "growth"}]
    receipts = {"01": [{"quote": "Revenue grew", "claim": "c1"}]}  # quote omits the number
    blocked, warns = run_checks(sections, claims, receipts)
    assert any(b["type"] == "number_coverage" for b in blocked), "expected uncovered-number block"

    # case 2: unverified claim -> BLOCK regardless of attribution
    sections = {"01": "We saw five ships today."}
    claims = [{"id": "c1", "value": "5", "as_of": "2026-07-13", "source": "x", "retrieved_at": "2026-07-13", "status": "unverified", "predicate": "count"}]
    receipts = {"01": [{"quote": "We saw five ships today.", "claim": "c1", "attributed": True}]}
    blocked, warns = run_checks(sections, claims, receipts)
    assert any(b["type"] == "status_gate" for b in blocked), "expected unverified block"

    # case 3: happy path -> PASS (also exercises single_source+attributed and stale-but-irrelevant-predicate)
    sections = {"01": "Brent closed near seventy six dollars today in New York trading. "
                       "Separately, some desks are already pricing in up three percent for the reopen."}
    claims = [
        {"id": "c1", "value": 76, "as_of": "2026-07-10", "source": "x", "retrieved_at": "2026-07-13", "status": "verified", "predicate": "close"},
        {"id": "c2", "value": "3%", "as_of": "2026-01-01", "source": "y", "retrieved_at": "2026-07-13", "status": "single_source", "predicate": "move_pct"},
    ]
    receipts = {"01": [
        {"quote": "Brent closed near seventy six dollars", "claim": "c1"},
        {"quote": "up three percent", "claim": "c2", "attributed": True},
    ]}
    blocked, warns = run_checks(sections, claims, receipts)
    assert blocked == [], f"expected clean pass, got {blocked}"

    # cases 4-6 share one synthetic feed receipt and a section built from its own quotes,
    # so number_coverage never fires and only the check under test can block.
    feed = {"ohlcv-feed-receipts-test.json": {"dashboard": {"SP:SPX": {
        "prior": {"open": 1.0, "high": 2.0, "low": 3.0, "close": 4.0},
        "session": {"open": 5.0, "high": 6.0, "low": 7.0, "close": 8.0},
        "returnPercent": 0.0162,
    }}}}
    fields = [("prior_open", 1.0), ("prior_high", 2.0), ("prior_low", 3.0), ("prior_close", 4.0),
              ("session_open", 5.0), ("session_high", 6.0)]

    def feed_case(pairs, source="ohlcv-feed-receipts-test.json#SP:SPX"):
        cs = [{"id": f"c{i}", "value": v, "as_of": "2026-07-27", "source": source,
               "retrieved_at": "2026-07-27", "status": "verified", "predicate": p}
              for i, (p, v) in enumerate(pairs)]
        text = " ".join(f"Level {c['value']} held." for c in cs)
        rs = [{"quote": f"Level {c['value']} held.", "claim": c["id"]} for c in cs]
        return run_checks({"01": text}, cs, {"01": rs}, feed_receipts=feed)

    # 4. recital cap: RECITAL_CAP of one instrument passes, one more blocks
    blocked, _ = feed_case(fields[:RECITAL_CAP])
    assert blocked == [], f"expected {RECITAL_CAP} feed claims to pass, got {blocked}"
    blocked, _ = feed_case(fields[:RECITAL_CAP + 1])
    assert any(b["type"] == "recital" for b in blocked), f"expected recital block, got {blocked}"

    # 5. feed schema: instrument must resolve under `dashboard`, and the value must match it
    blocked, _ = feed_case(fields[:1], source="ohlcv-feed-receipts-test.json#SP:NOPE")
    assert any(b["type"] == "feed_schema" for b in blocked), "expected unknown-instrument block"
    blocked, _ = feed_case([("prior_open", 99.0)])
    assert any(b["type"] == "feed_schema" for b in blocked), "expected value-mismatch block"
    blocked, _ = feed_case([("made_up", 1.0)])
    assert any(b["type"] == "feed_schema" for b in blocked), "expected predicate-vocabulary block"
    # rounding: the script may quote a receipt's 0.0162 as 0.02
    blocked, _ = feed_case([("session_return", 0.02)])
    assert blocked == [], f"expected rounded return to pass, got {blocked}"

    # 6. laundering: a feed value re-sourced elsewhere warns, never blocks
    blocked, warns = feed_case([("prior_open", 1.0)], source="https://example.com/article")
    assert blocked == [], f"laundering must not block, got {blocked}"
    assert any(w["type"] == "laundering" for w in warns), "expected laundering warn"

    print("selftest: 6/6 PASS")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    if len(sys.argv) < 2:
        print("usage: python tools/claims_gate.py productions/<vid> [--selftest]", file=sys.stderr)
        sys.exit(1)
    rpt = gate(sys.argv[1])
    sys.exit(1 if rpt["verdict"] == "BLOCK" else 0)
