"""Section locator for the derivative lane.

Both cases below are real 2026-07-28 aborts on daily-2026-07-27, not hypotheticals:
the cut refused twice on a master whose audio and plan were in fact aligned.
"""
import json
import tempfile
import unittest
from pathlib import Path

from tools.cut_derivatives import CAPTION_DRIFT_MAX_S, caption_start, section_start

ROOT = Path(__file__).resolve().parents[1]

# faster-whisper breaks cues at sentence boundaries, so a 5-word prefix straddles two cues.
CUES = [
    (19.0, "Start with the index."),
    (21.5, "The S&P 500 sold off all afternoon."),
    (45.0, "Nvidia is the reason the tape turned."),
]


def _prod(timeline=None):
    tmp = tempfile.TemporaryDirectory(dir=ROOT)
    prod = Path(tmp.name)
    if timeline is not None:
        (prod / "build").mkdir()
        (prod / "build" / "timeline.json").write_text(json.dumps(timeline), encoding="utf-8")
    return tmp, prod


class CaptionStartTests(unittest.TestCase):
    def test_prefix_spanning_two_cues_is_found(self):
        # The old locator compared the prefix against ONE cue's first five words and aborted
        # here, because "Start with the index." is four words.
        self.assertEqual(caption_start(CUES, "Start with the index. The S&P 500 sold off"), 19.0)

    def test_asr_normalisation_is_not_a_match(self):
        # Spoken "Nvidia's the reason", transcribed "Nvidia is the reason". No match is correct;
        # the old code turned this into a hard exit instead of deferring to the timeline.
        self.assertIsNone(caption_start(CUES, "Nvidia's the reason the tape turned"))


class SectionStartTests(unittest.TestCase):
    def test_timeline_wins_when_captions_cannot_match(self):
        tmp, prod = _prod([{"id": "06-a", "start": 45.2}])
        with tmp:
            self.assertEqual(section_start(prod, CUES, "Nvidia's the reason the tape turned", "06"),
                             45.2)

    def test_captions_carry_the_cut_without_a_timeline(self):
        tmp, prod = _prod()
        with tmp:
            self.assertEqual(section_start(prod, CUES, "Start with the index. The S&P", "03"), 19.0)

    def test_real_drift_still_hard_fails(self):
        tmp, prod = _prod([{"id": "03-a", "start": 19.0 + CAPTION_DRIFT_MAX_S + 0.5}])
        with tmp, self.assertRaises(SystemExit):
            section_start(prod, CUES, "Start with the index. The S&P", "03")

    def test_no_timeline_and_no_caption_match_hard_fails(self):
        tmp, prod = _prod()
        with tmp, self.assertRaises(SystemExit):
            section_start(prod, CUES, "A sentence the transcript never contains", "09")


if __name__ == "__main__":
    unittest.main()
