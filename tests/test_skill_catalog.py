import json
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import skill_catalog  # noqa: E402


class SkillCatalogTests(unittest.TestCase):
    def test_project_skill_description_overrides_stale_user_level_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared = root / "shared"
            project = root / "project"
            usage = root / "usage"
            (shared / "tiktok-upload").mkdir(parents=True)
            (project / "tiktok-upload").mkdir(parents=True)
            usage.mkdir()
            (shared / "tiktok-upload" / "SKILL.md").write_text(
                "---\nname: tiktok-upload\ndescription: Retired cookie uploader.\n---\n",
                encoding="utf-8",
            )
            (project / "tiktok-upload" / "SKILL.md").write_text(
                "---\nname: tiktok-upload\ndescription: Official refreshable API.\n---\n",
                encoding="utf-8",
            )

            result = skill_catalog.build_catalog(
                roots=(("shared", shared), ("project", project)),
                usage_root=usage,
                usage_cache=root / "usage-cache.json",
            )

            item = next(item for item in result["skills"] if item["name"] == "tiktok-upload")
            self.assertEqual("Official refreshable API.", item["description"])

    def test_catalog_deduplicates_packages_and_records_claude_usage_metadata_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex = root / "codex"
            claude = root / "claude"
            usage = root / "usage"
            (codex / "market-analysis").mkdir(parents=True)
            (claude / "market-analysis").mkdir(parents=True)
            usage.mkdir()
            skill_text = "---\nname: market-analysis\ndescription: Analyze current markets.\n---\n# Workflow\n"
            (codex / "market-analysis" / "SKILL.md").write_text(skill_text, encoding="utf-8")
            (claude / "market-analysis" / "SKILL.md").write_text(skill_text, encoding="utf-8")
            event = {
                "timestamp": "2026-07-18T09:30:49Z",
                "cwd": "C:/work",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Skill", "input": {"skill": "market-analysis", "args": "private task body"}},
                        {"type": "tool_use", "name": "Skill", "input": {"skill": "bundle:market-analysis", "args": "private alias body"}},
                        {"type": "tool_use", "name": "Skill", "input": {"skill": "loop", "args": "private monitor body"}},
                    ]
                },
            }
            (usage / "session.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")

            result = skill_catalog.build_catalog(
                roots=(("codex", codex), ("claude", claude)),
                usage_root=usage,
                usage_cache=root / "usage-cache.json",
            )

            by_name = {item["name"]: item for item in result["skills"]}
            self.assertEqual(by_name["market-analysis"]["source_kinds"], ["claude", "codex"])
            self.assertEqual(by_name["market-analysis"]["claude_used_count"], 2)
            self.assertEqual(by_name["market-analysis"]["claude_aliases"], ["bundle:market-analysis"])
            self.assertTrue(by_name["market-analysis"]["available"])
            self.assertFalse(by_name["loop"]["available"])
            self.assertNotIn("private task body", json.dumps(result))
            self.assertNotIn("private monitor body", json.dumps(result))
            self.assertNotIn("bundle:market-analysis", by_name)
            cache = (root / "usage-cache.json").read_text(encoding="utf-8")
            self.assertNotIn("private task body", cache)


if __name__ == "__main__":
    unittest.main()
