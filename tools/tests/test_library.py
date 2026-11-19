import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'library.py'
class LibraryTest(unittest.TestCase):
    def test_add_search_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'book').write_text('text'); env = dict(os.environ, AGENT_OFFICE_ROOT=tmp)
            def run(*args): return subprocess.run([sys.executable, str(TOOL), *args], env=env, capture_output=True, text=True)
            self.assertEqual(run('add', '--id', 'one', '--title', 'Manual', '--path', 'book', '--dept', 'work', '--tags', 'guide').returncode, 0)
            self.assertIn('Manual', run('search', 'guide').stdout); self.assertEqual(run('check').returncode, 0)
            (root / 'book').unlink(); self.assertEqual(run('check').returncode, 1)
            self.assertTrue((root / 'library/CATALOG.md').is_file())
