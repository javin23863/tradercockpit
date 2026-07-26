import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import paths  # noqa: E402


class PathsTests(unittest.TestCase):
    def test_env_override_wins(self):
        with patch.dict(os.environ, {"TRADERCOCKPIT_VAULT_DIR": "/srv/vault"}):
            self.assertEqual(paths.vault_dir(), Path("/srv/vault"))

    def test_default_is_the_operator_box_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                str(paths.vault_dir()), paths.DEFAULTS["TRADERCOCKPIT_VAULT_DIR"]
            )

    def test_empty_env_falls_back_rather_than_resolving_to_cwd(self):
        # a blank var in a systemd unit must not silently mean Path(".")
        with patch.dict(os.environ, {"TRADERCOCKPIT_MANAGER_DIR": ""}):
            self.assertEqual(
                str(paths.manager_dir()), paths.DEFAULTS["TRADERCOCKPIT_MANAGER_DIR"]
            )

    def test_missing_reports_dirs_absent_on_this_box(self):
        with patch.dict(os.environ, {"TRADERCOCKPIT_VAULT_DIR": "/nonexistent-vault"}):
            self.assertIn("TRADERCOCKPIT_VAULT_DIR", paths.missing())


if __name__ == "__main__":
    unittest.main()
