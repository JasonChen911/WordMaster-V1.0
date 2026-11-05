"""Data paths must remain writable after installation into /opt."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from platform_paths import user_data_dir


class UserDataDirTests(unittest.TestCase):
    def test_explicit_override_wins_on_both_platforms(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, {"WORDMASTER_DATA_DIR": root}):
                self.assertEqual(user_data_dir("nt"), Path(root).resolve())
                self.assertEqual(user_data_dir("posix"), Path(root).resolve())

    def test_linux_uses_xdg_data_home(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, {"XDG_DATA_HOME": root}, clear=True):
                self.assertEqual(user_data_dir("posix"), Path(root) / "WordMaster")

    def test_windows_uses_roaming_appdata(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, {"APPDATA": root}, clear=True):
                self.assertEqual(user_data_dir("nt"), Path(root) / "WordMaster")


if __name__ == "__main__":
    unittest.main()
