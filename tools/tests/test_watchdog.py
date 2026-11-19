import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

TOOL = Path(__file__).resolve().parents[1] / 'watchdog.py'
POST = TOOL.with_name('post.py')


class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.reg = self.root / 'management/registry'; self.reg.mkdir(parents=True)
        self.tools = self.root / 'management/tools'; self.tools.mkdir()
        self.write('rooms.json', {'rooms': [{'id': 'lab', 'path': 'departments/lab'}]})
        self.write('presence.json', {'shifts': [{'room': 'lab', 'badge': 'a', 'status': 'active'}]})
        self.write('sessions.json', {'sessions': {'right-session': {'badge': 'a', 'seen': '2026-01-01T00:00:00+00:00'}}})
        bin_dir = self.root / 'bin'; bin_dir.mkdir()
        fake = bin_dir / 'claude'; fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@" >> "$AGENT_OFFICE_ROOT/calls"\n'); fake.chmod(0o755)
        self.env = dict(os.environ, AGENT_OFFICE_ROOT=str(self.root), PATH=str(bin_dir) + os.pathsep + os.environ['PATH'])
        self.run_tool('guard', '--no-systemd')

    def write(self, name, data): (self.reg / name).write_text(json.dumps(data))
    def state(self): return json.loads((self.reg / 'watchdog.json').read_text())
    def run_tool(self, *args): return subprocess.run([sys.executable, str(TOOL), *args], env=self.env, check=True, capture_output=True, text=True)
    def message(self):
        subprocess.run([sys.executable, str(POST), 'write', '--to', 'lab', '--from', 'owner', '--type', 'request', '--subject', 'work', '--body', 'do work', '--instructions'], env=self.env, check=True, capture_output=True)
    def calls(self): return (self.root / 'calls').read_text().splitlines() if (self.root / 'calls').exists() else []
    def test_hook_start_then_wake(self):
        self.write('presence.json', {'shifts': []})
        self.write('sessions.json', {'sessions': {}})
        office = TOOL.with_name('office.py')
        subprocess.run([sys.executable, str(office), 'hook', 'start'], input=json.dumps({'session_id': 'new-session', 'cwd': str(self.root / 'departments/lab')}), env=self.env, text=True, capture_output=True, check=True)
        self.message(); self.run_tool('round')
        self.assertEqual(self.calls()[:3], ['-p', '--resume', 'new-session'])

    def test_guard_pause(self):
        self.assertTrue(self.state()['on']); self.run_tool('pause'); self.assertFalse(self.state()['on'])
    def test_no_messages(self):
        self.run_tool('round'); self.assertEqual(self.calls(), [])
    def test_wake_and_tries_limit(self):
        self.message(); self.run_tool('round'); self.assertEqual(self.calls()[:3], ['-p', '--resume', 'right-session'])
        self.run_tool('round'); self.run_tool('round'); self.assertEqual(self.state()['wakes_done'], 2); self.assertEqual(self.calls().count('--resume'), 2)
    def test_max_wakes(self):
        self.message(); state = self.state(); state['wakes_done'] = 6; self.write('watchdog.json', state)
        self.run_tool('round'); self.assertEqual(self.calls(), [])
    def test_quota_exhausted(self):
        self.message(); (self.tools / 'shifts.py').write_text('import sys\nsys.exit(75)\n')
        self.run_tool('round'); self.assertEqual(self.calls(), [])
    def test_expiry(self):
        self.message(); state = self.state(); state['until'] = (datetime.now().astimezone() - timedelta(minutes=1)).isoformat(); self.write('watchdog.json', state)
        self.run_tool('round'); self.assertFalse(self.state()['on']); self.assertEqual(self.calls(), [])


if __name__ == '__main__': unittest.main()
