import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'office.py'

class OfficeTest(unittest.TestCase):
    def test_shift_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); reg = root / 'management/registry'; reg.mkdir(parents=True)
            (reg / 'rooms.json').write_text(json.dumps({'rooms': [{'id': 'work'}]}))
            env = dict(os.environ, AGENT_OFFICE_ROOT=tmp)
            def run(*args): return subprocess.run([sys.executable, str(TOOL), *args], env=env, text=True, capture_output=True)
            badge = run('in', '--name', 'Worker', '--room', 'work', '--task', 'Build').stdout.strip()
            self.assertTrue(badge)
            self.assertNotEqual(run('in', '--name', 'Worker', '--room', 'work', '--task', 'Build').returncode, 0)
            (root / 'letter').write_text('Done')
            self.assertEqual(run('out', '--badge', badge, '--resignation', 'letter').returncode, 0)
            self.assertEqual(run('who').stdout.strip(), '[]')
    def test_hook_invalid_input(self):
        result = subprocess.run([sys.executable, str(TOOL), 'hook', 'start'], input='bad', text=True)
        self.assertEqual(result.returncode, 0)

    def test_hooks_create_shift_and_record_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); reg = base / 'management/registry'; reg.mkdir(parents=True)
            (reg / 'rooms.json').write_text(json.dumps({'rooms': [{'id': 'one', 'path': 'one'}, {'id': 'two', 'path': 'two'}]}))
            env = dict(os.environ, AGENT_OFFICE_ROOT=tmp)
            def hook(event, data):
                return subprocess.run([sys.executable, str(TOOL), 'hook', event], input=json.dumps(data), env=env, text=True, capture_output=True, check=True)
            data = {'session_id': 'abc', 'cwd': str(base / 'one')}
            output = json.loads(hook('start', data).stdout)
            badge = json.loads((reg / 'sessions.json').read_text())['sessions']['abc']['badge']
            self.assertIn(badge, output['hookSpecificOutput']['additionalContext'])
            hook('start', data)
            self.assertEqual(len(json.loads((reg / 'presence.json').read_text())['shifts']), 1)
            hook('tool', dict(data, tool_name='Read', tool_input={'file_path': str(base / 'two/file')}))
            self.assertEqual(json.loads((reg / 'presence.json').read_text())['shifts'][0]['room'], 'two')
            self.assertEqual(json.loads((reg / 'moves.jsonl').read_text().splitlines()[-1])['room'], 'two')
