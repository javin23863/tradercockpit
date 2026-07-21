import sys
import unittest
from pathlib import Path
from unittest.mock import patch


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import credential_custody  # noqa: E402


class CredentialCustodyTests(unittest.TestCase):
    def test_meta_loader_treats_protected_operator_path_as_unavailable(self):
        with patch.object(Path, "is_file", side_effect=PermissionError("protected")):
            self.assertFalse(credential_custody.load_meta_env())


if __name__ == "__main__":
    unittest.main()
