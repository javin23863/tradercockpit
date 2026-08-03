# Into the Laboratory E01-E03 rewrite candidates

Status: candidate scripts for operator review. These are not approved for narration, rendering, upload, or publication.

The scripts describe the recorded pipeline runs captured in [`../e01-e03-live-receipts-2026-08-03.json`](../e01-e03-live-receipts-2026-08-03.json). The matching deterministic visual map is [`../e01-e03-rewrite-visual-map.json`](../e01-e03-rewrite-visual-map.json), with its provenance receipt in `../visual-rebuild-previews/e01-e03-rewrite-visual-receipt.json`.

| Episode | Candidate title | VO SHA-256 | Script JSON SHA-256 | Current gate boundary |
| --- | --- | --- | --- | --- |
| 01 | The First Screen Rejected 5,206 Candidates. One Run Continued. | `995fa5b2f3efe312d873b36ead2af5ea08aa62ccca5a9ec5768ac19afbefa98c` | `a320986879eec868c8ed8e9321efbcc13e24169c3f2aa5a3b69a1c08c6bff239` | Dow 1,335→184; ES 2,004→0; EURUSD 2,051→0 |
| 02 | The SPY RSI2 Test Rejected Five Candidates Before the Holdout | `b0c5f6e6c12e00c9c02122a34c70c4e703380e8016860e63f2c6513f8852d753` | `1507ac3d0bf8351a268746e5c26518543aa4bb481e29f08328865e5d2c0aca6a` | SPY 5→0; holdout not reached; Dow 184→154 is a separate branch |
| 03 | The Dow Test Kept 53 Candidates. 101 Failed the Fill and Session Checks. | `c0909adb6742c74b71d4ea4909c3c68034f274b0a3bb6ec576c06c645d74ff6c` | `0b207d59b7329592cef5d8d1f57c7b15636ce6f0f17b20e0cc5468b12ad6a6ff` | Dow phase03 154→53; 101 failed at least one view; phase04 handoff preserved |

All three pass the teaching-claim, packaging, arc, style, AI-writing, and strict syllabus-term gates. The `ai_tell_gate` remains a candidate blocker because technical teaching copy exceeds its market-speech unseen-bigram threshold; that needs an owner decision or calibrated gate treatment. The Impeccable detector returned an empty findings list for the deterministic visual set.
