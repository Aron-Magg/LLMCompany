import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

BASE = Path(__file__).resolve().parents[2]
SCRIPT = BASE / 'tools/wardens.py'
CONFIG = BASE / 'template/management/registry/wardens_rules.json'

class WardensTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.reg = self.root / 'management/registry'; self.reg.mkdir(parents=True)
        shutil.copy(CONFIG, self.reg / 'wardens_rules.json')
        self.env = dict(os.environ, AGENT_OFFICE_ROOT=str(self.root))
    def invoke(self, action, payload=None, *args):
        p = subprocess.run(['python3', str(SCRIPT), action, *args], input=json.dumps(payload or {}), text=True, capture_output=True, env=self.env, check=True)
        return json.loads(p.stdout) if p.stdout.startswith('{') else p.stdout
    def config(self, **values):
        p = self.reg / 'wardens_rules.json'; data = json.loads(p.read_text()); data.update(values); p.write_text(json.dumps(data))
    def pre(self, command='', name='Bash', path=''):
        return self.invoke('pre', {'tool_name': name, 'tool_input': {'command': command, 'file_path': path}})
    def test_pre_rules(self):
        self.config(protected_ports=[9999], protected_folders=['private'])
        for command in ('pkill x', 'killall x', 'git push', 'kill 9999', 'cat secrets/key'):
            with self.subTest(command=command): self.assertEqual(self.pre(command)['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.pre(name='Write', path='private/file')['hookSpecificOutput']['permissionDecision'], 'deny')
        for command in ('git commit -m hello', 'ffmpeg -i in out'):
            self.assertIn('additionalContext', self.pre(command)['hookSpecificOutput'])
        self.assertIn('filename', self.pre(name='Write', path=str(self.root / 'documento.txt'))['hookSpecificOutput']['additionalContext'])
        self.assertEqual(self.pre(name='Read', path='private/file'), '')
    def test_agent_quota_and_exception(self):
        at = dt.datetime.now(dt.timezone.utc)
        (self.reg / 'quotas.json').write_text(json.dumps({'teams': {'test': {'windows': [{'read_at': at.isoformat(), 'used_pct': 81}]}}}))
        self.assertEqual(self.pre(name='mcp__x__delegate_task')['hookSpecificOutput']['permissionDecision'], 'deny')
        e = {'rule':'agent_quota','scope':'*','expires':(at + dt.timedelta(minutes=1)).isoformat()}
        (self.reg / 'exceptions.jsonl').write_text(json.dumps(e)+'\n')
        self.assertIn('estimate', self.pre(name='Agent')['hookSpecificOutput']['additionalContext'])
        e['expires'] = (at - dt.timedelta(minutes=1)).isoformat(); (self.reg / 'exceptions.jsonl').write_text(json.dumps(e)+'\n')
        self.assertEqual(self.pre(name='Agent')['hookSpecificOutput']['permissionDecision'], 'deny')
        (self.reg / 'estimates.jsonl').write_text(json.dumps({'at':at.isoformat()})+'\n')
        self.assertNotIn('estimate', self.pre(name='Agent')['hookSpecificOutput']['permissionDecisionReason'])
    def test_scoped_date_exception(self):
        expiry = (dt.datetime.now().astimezone().date() + dt.timedelta(days=1)).isoformat()
        self.invoke('exception', {}, '--rule', 'R05', '--scope', 'git push origin', '--reason', 'test', '--owner-words', 'yes', '--expires', expiry, '--badge', 'b')
        self.assertEqual(self.pre('git push origin main'), '')
        self.assertEqual(self.pre('git push upstream main')['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_push_command_boundaries(self):
        for command in ('echo "git push"', "echo 'git push'", 'echo git push', 'cat <<EOF\ngit push\nEOF\n'):
            with self.subTest(command=command): self.assertEqual(self.pre(command), '')
        for command in ('cd x && git push', 'true; git push', 'true | git push', '(git push)', 'true\ngit push'):
            with self.subTest(command=command): self.assertEqual(self.pre(command)['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_exception_validation(self):
        expiry = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat()
        valid = {'rule': 'R05', 'scope': '*', 'reason': 'test', 'owner-words': 'yes', 'expires': expiry, 'badge': 'b'}
        cases = {'rule': 'unknown', 'scope': '  ', 'reason': '', 'owner-words': ' ', 'expires': 'bad'}
        for field, value in list(cases.items()) + [('expires', '2000-01-01')]:
            args = dict(valid); args[field] = value
            command = ['python3', str(SCRIPT), 'exception']
            for key, item in args.items(): command.extend(['--' + key, item])
            result = subprocess.run(command, text=True, capture_output=True, env=self.env)
            with self.subTest(field=field, value=value):
                self.assertEqual(result.returncode, 2)
                self.assertIn('error:', result.stderr)
                self.assertFalse((self.reg / 'exceptions.jsonl').exists())

    def test_stop_and_prompt(self):
        transcript = self.root / 'transcript'; transcript.write_text(json.dumps({'type':'user','message':{'content':'hello'}})+'\n')
        output = self.invoke('stop', {'transcript_path':str(transcript), 'last_assistant_message':'At 12:34 quota used 50%. I will resume later.'})
        for word in ('Time', 'Credit', 'Postponement'): self.assertIn(word, output['systemMessage'])
        self.assertIn('quota', self.invoke('prompt')['hookSpecificOutput']['additionalContext'])
    def test_broken_config_and_speed(self):
        (self.reg / 'wardens_rules.json').write_text('{')
        self.assertIn('Warden warning', self.pre('git push')['systemMessage'])
        shutil.copy(CONFIG, self.reg / 'wardens_rules.json')
        start = time.monotonic(); self.pre('true'); self.assertLess(time.monotonic()-start, .1)
    def test_commands(self):
        self.assertEqual(self.invoke('thresholds')['thresholds'], [65,80,90])
        self.config(trial_successes=10); self.assertEqual(self.invoke('thresholds')['thresholds'], [70,85,95])
        expiry=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)).isoformat()
        self.invoke('exception', {}, '--rule','R05','--scope','*','--reason','test','--owner-words','yes','--expires',expiry,'--badge','b')
        self.assertEqual(self.invoke('exceptions')['rule'], 'R05'); self.invoke('log', {}, '--summary'); self.invoke('rules')

if __name__ == '__main__': unittest.main()
