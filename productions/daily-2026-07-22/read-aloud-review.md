# Read-Aloud and Numeric-Idiom Review — daily-2026-07-22

status: PASS

Reviewed at conversational delivery cadence against the hook, the GEV chart section, the scenario map, and the close.

## Read-aloud checks

- Hook leads with the SMCI/GEV divergence and reaches the portfolio question without setup narration.
- Company-release sections keep official figures with Apollo; chart judgment and conditional levels remain with the Operator.
- Longhand prices are speakable without changing precision or causal direction.
- Instrument names remain literal. Instrument-role metaphors and personification found in the first draft were removed.
- Corrective-contrast templates found in the first draft were rewritten positively. The required closing financial-advice sentence remains.
- No narration refers to screens, charts being shown, gates, receipts, verification machinery, editing, or production tools.
- No product pitch appears in narration.

## Numeric-idiom checks

- “nearly twenty percent” reduces to the receipted SMCI return of 19.84%.
- “almost nine percent” reduces to the receipted GEV loss of 8.69%.
- “about half a percent” reduces to the receipted NDX loss of 0.54%.
- GEV “closed at the low” is exact: close 985.03 equals low 985.03.
- VIX “closed at the session low” is exact: close 16.64 equals low 16.64.
- The S&P 500 finishing close to its open is supported by 7,497.47 open and 7,498.96 close; the script does not call that a full giveback.
- Scenario levels are conditional closes using captured July 22 levels; none is phrased as a prediction.

## Final verification

- `claims_gate.py`: PASS — 12 sections, 45 claims, 111 receipts.
- `script_style_gate.py`: PASS — 12 sections, 2,214 gate-counted words.
- Independent GPT-5.6 Sol xhigh critic: SHIP after one FIX/triage cycle.

## Boundary

This editorial review and the independent critic do not substitute for exact-hash operator approval. `script-approval.json` remains absent.
