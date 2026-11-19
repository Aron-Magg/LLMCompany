import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'shifts.py'
class ShiftsTest(unittest.TestCase):
    def test_readings_and_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = Path(tmp) / 'management/registry'; reg.mkdir(parents=True)
            env = dict(os.environ, AGENT_OFFICE_ROOT=tmp)
            def run(*args): return subprocess.run([sys.executable, str(TOOL), *args], env=env, text=True, capture_output=True)
            def quota(used, read, reset): (reg / 'quotas.json').write_text(json.dumps({'teams': {'team': {'windows': [{'name': 'session', 'used_pct': used, 'read_at': read, 'resets_at': reset}]}}}))
            quota(40, '2020-01-01T00:00:00+00:00', '2020-01-02T00:00:00+00:00')
            result = run('estimate', '--badge', 'b', '--task', 't', '--team', 'team', '--cost', 'small', '--done-when', 'done'); self.assertEqual(result.returncode, 0)
            quota(10, '2020-01-03T00:00:00+00:00', '2020-01-04T00:00:00+00:00')
            actual = run('actuals', '--id', result.stdout.strip()); self.assertIn('reset between readings', actual.stdout)
            self.assertEqual(run('costs').returncode, 0); self.assertTrue((reg / 'COST_TABLE.md').exists())
            self.assertEqual(run('check', '--team', 'missing').returncode, 0)
