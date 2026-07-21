import sys
import unittest
from pathlib import Path
from unittest.mock import patch


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import janitor  # noqa: E402


class JanitorTests(unittest.TestCase):
    def test_cache_audit_skips_protected_directories(self):
        with patch.object(Path, "is_dir", side_effect=PermissionError("protected")):
            self.assertEqual([], janitor.scan_caches())


if __name__ == "__main__":
    unittest.main()
