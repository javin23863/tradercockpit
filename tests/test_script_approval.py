import hashlib
import inspect
import json
import tempfile
import unittest
from pathlib import Path

from tools import produce
from tools.script_approval import (
    ROOT,
    load_production_approval,
    require_production_approval,
    require_script_approval,
)
from tools.tts_chatterbox import main as chatterbox_main


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_approved_production(folder, framing="Bloomberg market framing"):
    production = Path(folder)
    brief = production / "analysis-brief.md"
    sources = production / "source-receipt.md"
    script = production / "vo.txt"
    script_receipt = production / "script-approval.json"
    production_receipt = production / "production-approval.json"
    brief.write_text(f"National Bureau of Statistics evidence. {framing}", encoding="utf-8")
    sources.write_text(f"Official NBS release. {framing}", encoding="utf-8")
    script.write_text("operator approved", encoding="utf-8")
    script_receipt.write_text(json.dumps({
        "schema": "tradercockpit-script-approval/v1",
        "status": "approved",
        "script": script.relative_to(ROOT).as_posix(),
        "scriptSha256": sha(script),
        "reviewedBy": "operator",
        "reviewedAt": "2026-07-16T17:00:00Z",
    }), encoding="utf-8")
    receipt = {
        "schema": "tradercockpit-production-approval/v1",
        "status": "approved",
        "analysisBrief": brief.relative_to(ROOT).as_posix(),
        "analysisBriefSha256": sha(brief),
        "sourceReceipt": sources.relative_to(ROOT).as_posix(),
        "sourceReceiptSha256": sha(sources),
        "scriptApproval": script_receipt.relative_to(ROOT).as_posix(),
        "scriptApprovalSha256": sha(script_receipt),
        "framingSources": ["Bloomberg"],
        "reviewedBy": "operator",
        "reviewedAt": "2026-07-16T17:05:00Z",
    }
    production_receipt.write_text(json.dumps(receipt), encoding="utf-8")
    return production, receipt


class ScriptApprovalTests(unittest.TestCase):
    def test_tts_and_assembly_check_production_approval_before_work(self):
        chatterbox_source = inspect.getsource(chatterbox_main)
        self.assertLess(chatterbox_source.index("require_production_approval"), chatterbox_source.index("import torch"))
        produce_source = inspect.getsource(produce.main)
        self.assertLess(produce_source.index("require_production_approval"), produce_source.index("STAGES[name]"))

    def test_exact_topic_source_and_script_approvals_pass(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            production, receipt = make_approved_production(folder)
            self.assertEqual(require_production_approval(production), receipt)

    def test_missing_or_changed_topic_and_script_inputs_block(self):
        mutations = {
            "analysis brief": ("analysis-brief.md", "changed topic"),
            "source receipt": ("source-receipt.md", "changed sources"),
            "script": ("vo.txt", "changed script"),
        }
        for label, (filename, content) in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(dir=ROOT) as folder:
                production, _ = make_approved_production(folder)
                (production / filename).write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "changed after operator approval"):
                    require_production_approval(production)
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            with self.assertRaisesRegex(ValueError, "missing or unreadable production approval"):
                require_production_approval(Path(folder))

    def test_nbs_only_framing_fails_but_bloomberg_framing_passes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            production, _ = make_approved_production(folder, framing="official evidence only")
            with self.assertRaisesRegex(ValueError, "declared framing source is absent"):
                load_production_approval(production / "production-approval.json")
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            production, _ = make_approved_production(folder)
            load_production_approval(production / "production-approval.json")

    def test_rejected_script_blocks(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            production = Path(folder)
            (production / "script-approval.json").write_text(
                '{"schema":"tradercockpit-script-approval/v1","status":"rejected"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "status is rejected"):
                require_script_approval(production)


if __name__ == "__main__":
    unittest.main()
