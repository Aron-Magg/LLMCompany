import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]

class InitTest(unittest.TestCase):
    def test_initialize_and_mail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'office'
            subprocess.run([sys.executable, str(PACKAGE / 'scripts/init.py'), '--target', str(root), '--owner', 'Owner', '--language', 'en', '--departments', 'dev'], check=True, capture_output=True)
            post = root / 'management/tools/post.py'
            subprocess.run([sys.executable, str(post), '--root', str(root), 'write', '--to', 'dev', '--from', 'a', '--type', 'note', '--subject', 'hello', '--body', 'text'], check=True, capture_output=True)
            result = subprocess.run([sys.executable, str(post), '--root', str(root), 'read', '--mailbox', 'dev'], check=True, capture_output=True, text=True)
            self.assertIn('hello', result.stdout)
            settings = json.loads((root / '.claude/settings.json').read_text())
            self.assertTrue(all(h['command'].endswith('|| true') for entries in settings['hooks'].values() for entry in entries for h in entry['hooks']))
            office = root / 'management/tools/office.py'
            if office.exists(): subprocess.run([sys.executable, str(office), '--help'], check=True, capture_output=True)

    def test_default_brand_and_force_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'office'
            command = [sys.executable, str(PACKAGE / 'scripts/init.py'), '--target', str(root), '--owner', 'Alice', '--language', 'en']
            subprocess.run(command, check=True, capture_output=True)
            self.assertIn('Alice', (root / 'AGENTS.md').read_text())
            rules = root / 'management/registry/wardens_rules.json'
            rules.write_text('{"custom": "{{OWNER}}"}')
            agents = root / 'AGENTS.md'; agents.write_text('Custom {{OWNER}}')
            result = subprocess.run(command + ['--force'], check=True, capture_output=True, text=True)
            self.assertEqual(rules.read_text(), '{"custom": "{{OWNER}}"}')
            self.assertEqual(agents.read_text(), 'Custom {{OWNER}}')
            self.assertIn('Kept management/registry/wardens_rules.json', result.stdout)

if __name__ == '__main__': unittest.main()
