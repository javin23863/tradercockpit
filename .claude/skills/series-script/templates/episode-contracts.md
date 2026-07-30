# Teaching-series episode contracts

Use this page with `../SKILL.md`. Replace every placeholder from receipts; `unknown` is allowed
only where the source does not establish a value. These are candidates until the operator issues
the two approval receipts.

## Working files and runtime exports

| Working file | Runtime export | Rule |
|---|---|---|
| `script.md` SPOKEN cells | `artifacts/vo.txt` | Preserve order; put `# receipt: <id>` immediately before every spoken paragraph. |
| `capture-transcript.txt` | `artifacts/operator-capture.txt` | Copy the approved capture exactly. |
| `scene-plan.json` | `artifacts/scenes.json` | Convert each beat into the renderer's scene object; preserve the beat ID and visual purpose. Do not copy the working schema unchanged. |
| `thumbnail-brief.md` | `artifacts/thumbnail-epNN.html` and `.png` | Build the approved composition only after title, promise, and brief agree. |
| `fact-pack.md` | `artifacts/claims.json` and `strategy-passport.json` | Re-check every locator and hash after the final spoken edit. |

`scene-plan.json` uses `tradercockpit-scene-plan/v1`: `episode`, `status`, `voice_mode`, and a
`beats` array. Each beat needs `id`, `section`, `narration`, `spokenSubjects`, and a `visual`
object containing `path`, `kind`, `visibleSubjects`, `fit`, and `purpose`.

Runtime `scenes.json` is a scene-ID object. This is the minimum useful scene shape; add only
fields the episode composition uses:

```json
{
  "scene-hook": {
    "title": "VISIBLE TITLE",
    "sub": "VISIBLE CONTEXT",
    "cards": [{
      "label": "METRIC",
      "value": "VALUE",
      "note": "WHAT THE VALUE MEANS"
    }],
    "kicker": "VISIBLE IMPLICATION",
    "beats": [0.03, 0.12, 0.42, 0.84],
    "plate": "OPTIONAL-ASSET-NAME.png"
  }
}
```

Use the same scene ID in the working beat, the matching `# receipt:` paragraph, the runtime
object, the HyperFrames composition filename, and the timeline slot. The JSON is a hash-bound
execution manifest; the HTML composition remains the renderer source of truth.

Package-first means the promise, title, and `thumbnail-brief.md` are settled before drafting.
The source gate checks the title and public writing but does not certify thumbnail geometry.
After the HTML and PNG exist, run `tools/thumb_gate.py` through the full episode gate; the exact
PNG is hash-bound only by final certification. Do not claim a pre-TTS visual pass from a brief.

## Packaging

`artifacts/packaging.json` must contain at least:

```json
{
  "episode": 5,
  "syllabus_episode": "05",
  "title": "REPLACE WITH APPROVED TITLE",
  "release": {
    "privacy": "private",
    "category": "22",
    "containsSyntheticMedia": true,
    "captionLanguage": "en",
    "captionName": "English"
  }
}
```

`episode` is the public slate number. `syllabus_episode` is the matching heading number in
`OpenMontage/docs/syllabus.md`; never infer one from the other.

`artifacts/_yt_tags.json` is a JSON array of non-empty strings:

```json
["backtesting", "walk-forward analysis", "trading strategy"]
```

## Strategy passport

`artifacts/strategy-passport.json`:

```json
{
  "schema": "strategy-passport/v1",
  "strategy": {
    "asset_class": "RECEIPT VALUE",
    "instrument": "RECEIPT VALUE",
    "venue": "RECEIPT VALUE",
    "timeframe": "RECEIPT VALUE",
    "session_timezone": "RECEIPT VALUE",
    "entry": "RECEIPT VALUE",
    "exits": ["RECEIPT VALUE"],
    "sizing": "RECEIPT VALUE",
    "costs": "RECEIPT VALUE",
    "parameters": {"name": "value or range"}
  },
  "validation": {
    "phase": "RECEIPT VALUE",
    "test_window": "RECEIPT VALUE",
    "settings": {"name": "value"},
    "thresholds": {"name": "value"},
    "result": {"name": "value"}
  },
  "sources": [{
    "citation": "SOURCE NAME",
    "locator": "EXACT PATH, QUERY, OR JSON LOCATOR",
    "supports": "EXACT VALUES THIS SOURCE SUPPORTS",
    "limitations": "WHAT THIS SOURCE DOES NOT ESTABLISH"
  }],
  "limitations": ["EPISODE-SPECIFIC LIMIT"]
}
```

## Claims

Every `# receipt: <id>` in `vo.txt` has exactly one key in `artifacts/claims.json`. Every factual
source is an artifacts-relative evidence file with an exact hash. Academic and run-receipt
claims need at least one source; the narrow `delivery` kind is only for a pure transition line
accepted by `teaching_claim_gate.py`.

```json
{
  "schema": "teaching-claims/v1",
  "script_sha256": "SHA256 OF vo.txt",
  "sources": {
    "S1": {
      "citation": "SOURCE NAME",
      "locator": "EXACT PAGE, PATH, QUERY, OR JSON LOCATOR",
      "supports": "EXACT SPOKEN FACTS THIS SOURCE SUPPORTS",
      "limitations": "WHAT THIS SOURCE DOES NOT ESTABLISH",
      "path": "evidence/source-file.json",
      "sha256": "SHA256 OF artifacts/evidence/source-file.json"
    }
  },
  "claims": {
    "C1": {
      "kind": "run_receipt",
      "source_ids": ["S1"]
    },
    "C2": {
      "kind": "delivery",
      "source_ids": [],
      "why_non_claim": "Transition only."
    }
  }
}
```

## Human review and operator approvals

Compute hashes only after their inputs stop changing.

`artifacts/human-facing-review.json`:

```json
{
  "schema": "human-facing-review/v1",
  "script_sha256": "SHA256 OF vo.txt",
  "operator_capture_sha256": "SHA256 OF operator-capture.txt",
  "strategy_passport_sha256": "SHA256 OF strategy-passport.json",
  "protected_items_status": "PASS",
  "disclosure_status": "PASS",
  "independent_critic": {
    "reviewer": "NAMED CRITIC",
    "status": "PASS",
    "unresolved_findings": []
  },
  "operator_read_aloud": {
    "operator": "OPERATOR NAME",
    "status": "APPROVED",
    "date": "YYYY-MM-DD"
  }
}
```

The operator, not a writer or worker, issues `artifacts/operator-script-approval.json`:

```json
{
  "schema": "tradercockpit-series-script-approval/v1",
  "status": "approved",
  "script": "vo.txt",
  "scriptSha256": "SHA256 OF vo.txt",
  "reviewedBy": "OPERATOR NAME",
  "reviewedAt": "YYYY-MM-DDTHH:MM:SS+07:00",
  "approvalKind": "operator",
  "operatorReviewed": true,
  "attestations": {
    "readAloud": true,
    "phrasingATraderWouldSay": true,
    "factSeparatedFromJudgment": true
  }
}
```

After watching the exact master, the operator issues `artifacts/operator-master-approval.json`:

```json
{
  "schema": "tradercockpit-series-master-approval/v1",
  "status": "approved",
  "master": "PROJECT-RELATIVE MASTER PATH",
  "sha256": "SHA256 OF MASTER",
  "reviewedBy": "OPERATOR NAME",
  "reviewedAt": "YYYY-MM-DDTHH:MM:SS+07:00",
  "approvalKind": "operator",
  "operatorReviewed": true,
  "publicationAuthorized": false
}
```

## Create the runtime project

`OpenMontage` is a separate checkout at `<tradercockpit>/OpenMontage`; its `projects/` directory
is deliberately gitignored. A parent-repository worktree does not contain those projects.
Confirm the separate checkout and the prior series projects exist before continuing. If the
checkout lives elsewhere, set `OPENMONTAGE_ROOT` to its absolute path before running
`episode_gate.py`. If the prior project bundle is absent, stop and restore it; do not substitute
an empty directory or claim a repair ran on another computer.

In every command below, `<episode-dir>` means the absolute path
`<OPENMONTAGE_ROOT>/projects/series-05-<slug>`. Do not pass a repository-relative
`OpenMontage/projects/...` path when the checkout is external.

From the OpenMontage root, initialize the standard workspace:

```text
python -B -c "from lib.checkpoint import init_project; init_project('series-05-<slug>', title='<approved title>', pipeline_type='hybrid')"
```

From `projects/series-05-<slug>/`, initialize HyperFrames:

```text
npx hyperframes init hyperframes
```

This creates plumbing, not creative work. After approved audio exists at
`hyperframes/assets/audio/v1/<scene-id>.wav`, run the existing card builder from the
TraderCockpit repository root:

```text
python -B tools/build_scenes.py <episode-dir>
```

It consumes `artifacts/scenes.json` and writes the scene compositions plus
`hyperframes/index.html`; any `plate` named in a scene must already exist under
`hyperframes/assets/images/`. Do not call OpenMontage's generic `video_compose` or
`hyperframes_compose` render operation afterward: it scaffolds again and can overwrite that
index. Run from `hyperframes/`:

```text
npx hyperframes lint .
npx hyperframes validate .
npx hyperframes snapshot . --at <comma-separated seconds>
npx hyperframes render . --output renders/episode-05.mp4
```

The full gate also expects an episode-local gate toolkit. For this series baseline, copy only
these shared tools from the exact compatibility source
`<OPENMONTAGE_ROOT>/projects/series-04-mc-param/tools/`: `broll_conflicts.py`, `check_bed.py`,
`cut_census.py`, `intro_pace.py`, `motion_census.py`, `presentation_gate.py`, `slop_gate.py`,
`thumb_gate.py`, and `voice_consistency.py`. Do not choose another episode when that path is
missing; restore the bundle first. Write `check_figures.py` and `lexicon_gate.py` from Episode
5's own receipts and words; never inherit their assertions. A missing tool blocks by design.

## Gate order and complete runtime inventory

Before TTS, capture, or rendering:

```text
python -B tools/episode_gate.py source <episode-dir>
```

The source gate needs `vo.txt`, `packaging.json`, `claims.json`, `operator-capture.txt`,
`strategy-passport.json`, `human-facing-review.json`, `operator-script-approval.json`,
`_yt_desc.txt`, and `_yt_tags.json`, plus every evidence file referenced by `claims.json`.

Before upload:

```text
python -B tools/episode_gate.py run <episode-dir> --master <master.mp4>
```

The full gate also needs `scenes.json`, `thumbnail-epNN.html`, `thumbnail-epNN.png`,
`assets/subtitles.srt`, `hyperframes/index.html`, the exact master, and
`operator-master-approval.json`. `waivers.json`, when present, is also hash-bound. A GREEN source
receipt cannot certify a render, and a master approval cannot authorize publication.
