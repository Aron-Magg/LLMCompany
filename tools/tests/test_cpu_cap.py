import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'cpu_cap.py'
class CpuTest(unittest.TestCase):
    def test_child_and_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'cpu.log'
            result = subprocess.run([sys.executable, str(TOOL), '--log', str(log), '--', sys.executable, '-c', 'import time; t=time.monotonic()+1;\nwhile time.monotonic()<t: pass'], env=dict(os.environ, CAP_CPU_TOTAL='1', CAP_CPU_RESUME='1'), timeout=8)
            self.assertEqual(result.returncode, 0); self.assertIn('total=', log.read_text())

    def test_calm_wait_and_mine_pause_resume(self):
        import importlib.util
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location('cpu_cap', TOOL)
        cap = importlib.util.module_from_spec(spec); spec.loader.exec_module(cap)
        messages = []
        with patch.object(cap, 'cpu', side_effect=[(100, 0), (200, 10), (300, 100)]), patch.object(cap.time, 'sleep'):
            cap.wait_calm(.5, messages.append)
        self.assertIn('Waiting', messages[0])
        class Child:
            pid = 123
            returncode = 0
            def __init__(self): self.calls = 0
            def poll(self):
                self.calls += 1
                return None if self.calls <= 2 else 0
        child = Child()
        with patch.object(sys, 'argv', ['cpu_cap.py', '--', 'fake']), patch.dict(os.environ, {'CAP_CPU_TOTAL': '1', 'CAP_CPU_RESUME': '.8', 'CAP_CPU_CALM': '1', 'CAP_CPU_MINE': '.2'}), patch.object(cap, 'wait_calm', return_value=(100, 0)), patch.object(cap, 'cpu', side_effect=[(200, 50), (300, 140)]), patch.object(cap, 'group_ticks', side_effect=[0, 50, 50]), patch.object(cap.subprocess, 'Popen', return_value=child), patch.object(cap.time, 'sleep'), patch.object(cap.os, 'killpg') as kill:
            self.assertEqual(cap.main(), 0)
            self.assertEqual([call.args[1] for call in kill.call_args_list], [cap.signal.SIGSTOP, cap.signal.SIGCONT])
