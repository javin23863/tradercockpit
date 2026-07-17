import copy
import inspect
import subprocess
import unittest

from tools.editorial_gate import DEFAULT_GAP_S, compile_timeline, load_timeline, validate_scene_plan


SECTIONS = [{
    "num": "01",
    "text": "Brent is holding the war premium. Spy is not confirming panic.",
    "duration": 12.0,
}]

GOOD_PLAN = {
    "schema": "tradercockpit-scene-plan/v1",
    "beats": [
        {
            "id": "01a",
            "section": "01",
            "narration": "Brent is holding the war premium.",
            "spokenSubjects": ["brent"],
            "visual": {
                "path": "visuals/01a-brent.mp4",
                "kind": "tradingview",
                "visibleSubjects": ["brent"],
                "fit": "contain",
                "purpose": "Show Brent while the narration discusses Brent.",
            },
        },
        {
            "id": "01b",
            "section": "01",
            "narration": "Spy is not confirming panic.",
            "spokenSubjects": ["spy"],
            "visual": {
                "path": "visuals/01b-spy.mp4",
                "kind": "tradingview",
                "visibleSubjects": ["spy"],
                "fit": "contain",
                "purpose": "Show SPY while the narration discusses SPY.",
            },
        },
    ],
}


class EditorialGateTests(unittest.TestCase):
    def test_standalone_gate_uses_the_production_section_gap(self):
        default = inspect.signature(load_timeline).parameters["gap_s"].default
        self.assertEqual(DEFAULT_GAP_S, default)
        self.assertEqual(0.45, default)

    def test_compiles_explicit_narration_beats_instead_of_equal_filename_splits(self):
        errors = validate_scene_plan(GOOD_PLAN, SECTIONS, require_files=False)
        self.assertEqual([], errors)
        timeline = compile_timeline(GOOD_PLAN, SECTIONS)
        self.assertEqual(["01a", "01b"], [beat["id"] for beat in timeline])
        self.assertAlmostEqual(12.0, sum(beat["duration"] for beat in timeline), places=3)
        self.assertNotEqual(timeline[0]["duration"], timeline[1]["duration"])

    def test_rejects_chart_topic_mismatch(self):
        plan = copy.deepcopy(GOOD_PLAN)
        plan["beats"][0]["visual"]["visibleSubjects"] = ["spy"]
        errors = validate_scene_plan(plan, SECTIONS, require_files=False)
        self.assertTrue(any("subject overlap" in error for error in errors), errors)

    def test_rejects_cropped_news_cards(self):
        plan = copy.deepcopy(GOOD_PLAN)
        plan["beats"][0]["visual"].update({"kind": "news", "fit": "cover"})
        errors = validate_scene_plan(plan, SECTIONS, require_files=False)
        self.assertTrue(any("news visual" in error and "contain" in error for error in errors), errors)

    def test_rejects_generic_godseye_filler(self):
        plan = copy.deepcopy(GOOD_PLAN)
        plan["beats"][0]["visual"].update({
            "kind": "godseye",
            "purpose": "generic b-roll",
            "evidenceUse": "location-b-roll",
        })
        errors = validate_scene_plan(plan, SECTIONS, require_files=False)
        self.assertTrue(any("Godseye" in error and "purpose" in error for error in errors), errors)

    def test_news_renderer_has_a_contain_only_selftest(self):
        result = subprocess.run(
            ["node", "tools/visuals/fetch_news_shots.mjs", "--selftest"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("NEWS FIT SELFTEST PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
