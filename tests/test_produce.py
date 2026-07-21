import inspect
import json
import tempfile
import unittest
from pathlib import Path

from tools.produce import (allocate_frame_counts, build_sound_filter, parse_sections,
                           section_starts, stage_assemble, stage_shorts)


ROOT = Path(__file__).resolve().parents[1]


class ProduceSectionParserTests(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            production = Path(tmp)
            (production / "vo.txt").write_text(text, encoding="utf-8")
            return parse_sections(production)

    def test_tagged_sections_and_sub_blocks_round_trip(self):
        sections = self.parse(
            "## 01 data [APOLLO]\nOfficial data is unchanged.\n\n"
            "## 02 handoff\n### APOLLO\nThe release is due at ten.\n"
            "### OPERATOR\nI am watching the completed-bar level.\n"
        )

        self.assertEqual("APOLLO", sections[0]["speaker"])
        self.assertEqual([{"speaker": "APOLLO", "text": "Official data is unchanged."}],
                         sections[0]["blocks"])
        self.assertIsNone(sections[1]["speaker"])
        self.assertEqual(["APOLLO", "OPERATOR"],
                         [block["speaker"] for block in sections[1]["blocks"]])
        self.assertEqual(sections, json.loads(json.dumps(sections)))

    def test_untagged_sections_default_to_operator(self):
        sections = self.parse("## 01 legacy\nFirst paragraph.\n\nSecond paragraph.\n")

        self.assertEqual("OPERATOR", sections[0]["speaker"])
        self.assertEqual("First paragraph.  Second paragraph.", sections[0]["text"])
        self.assertEqual([{"speaker": "OPERATOR",
                           "text": "First paragraph.  Second paragraph."}],
                         sections[0]["blocks"])

    def test_video_04_iran_regime_v2_matches_existing_sections_golden(self):
        production = ROOT / "productions" / "video-04-iran-regime-v2"
        golden = json.loads((production / "build" / "sections.json").read_text(encoding="utf-8"))
        parsed = parse_sections(production)

        fields = ("num", "slug", "text")
        self.assertEqual([{key: section[key] for key in fields} for section in golden],
                         [{key: section[key] for key in fields} for section in parsed])
        self.assertTrue(all(section["speaker"] == "OPERATOR" for section in parsed))


class ProduceFrameAllocationTests(unittest.TestCase):
    def test_long_form_master_has_no_burned_captions(self):
        self.assertNotIn("subtitles=captions.srt", inspect.getsource(stage_assemble))
        self.assertNotIn("master-clean.mp4", inspect.getsource(stage_shorts))

    def test_cumulative_boundaries_stay_locked_to_timeline(self):
        durations = [5.46, 11.188, 18.362, 1.253, 4.196, 18.419]
        timeline = []
        start = 0.0
        for duration in durations:
            timeline.append({"start": start, "duration": duration})
            start += duration

        counts = allocate_frame_counts(timeline, fps=30)

        elapsed_frames = 0
        for beat, count in zip(timeline, counts):
            self.assertEqual(round(beat["start"] * 30), elapsed_frames)
            elapsed_frames += count
        self.assertEqual(round(start * 30), elapsed_frames)


class SoundLayerTests(unittest.TestCase):
    TIMELINE = [{"id": "01a", "start": 0.0}, {"id": "01b", "start": 10.0},
                {"id": "02a", "start": 20.0}, {"id": "03a", "start": 30.0},
                {"id": "03b", "start": 40.0}, {"id": "04a", "start": 50.0}]

    def test_section_starts_skip_first_section_and_sub_beats(self):
        self.assertEqual([20.0, 30.0, 50.0], section_starts(self.TIMELINE))

    def test_full_layer_mixes_vo_music_whooshes_and_final_impact(self):
        f = build_sound_filter(6, 60.0, [20.0, 30.0, 50.0], music_idx=7,
                               music_gain_db=-28.6, whoosh_idx=8, impact_idx=9)
        self.assertIn("atrim=0:60.000,volume=-28.6dB", f)
        self.assertIn("asplit=2", f)                        # impact replaces the last whoosh
        self.assertIn("adelay=19800|19800", f)              # whoosh leads the cut by 0.2s
        self.assertIn("adelay=50000|50000[imp]", f)
        self.assertIn("amix=inputs=5:normalize=0", f)       # vo + music + 2 whoosh + impact

    def test_no_music_and_no_boundaries_falls_back_to_plain_vo(self):
        self.assertIsNone(build_sound_filter(6, 60.0, []))

    def test_music_only_still_mixes(self):
        f = build_sound_filter(6, 60.0, [], music_idx=7, music_gain_db=-20.0)
        self.assertIn("amix=inputs=2:normalize=0", f)


if __name__ == "__main__":
    unittest.main()
