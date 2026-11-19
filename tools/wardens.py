#!/usr/bin/env python3
"""Configurable Claude Code hooks. Internal errors always fail open."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys


def root():
    here = Path(os.environ.get('AGENT_OFFICE_ROOT', os.getcwd())).resolve()
    return next((p for p in (here, *here.parents) if (p / 'management/registry/rooms.json').exists()), here)


def now(): return dt.datetime.now(dt.timezone.utc)
def stamp(s):
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        return dt.datetime.combine(dt.date.fromisoformat(s), dt.time.max).astimezone().astimezone(dt.timezone.utc)
    value = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
    if value.tzinfo is None: raise ValueError('Timestamp must include a timezone')
    return value.astimezone(dt.timezone.utc)
def read(path, default): return json.loads(path.read_text()) if path.exists() else default
def rows(path): return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
def append(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as f: f.write(json.dumps(value) + '\n')
def fresh(s, minutes):
    age = (now() - stamp(s)).total_seconds()
    return 0 <= age < minutes * 60


def turn(payload):
    """Return messages after the latest user message from Claude's JSONL transcript."""
    entries = rows(Path(payload['transcript_path'])) if payload.get('transcript_path') else []
    start = 0
    for i, item in enumerate(entries):
        if item.get('type') == 'user' and isinstance(item.get('message', {}).get('content'), str): start = i + 1
    return entries[start:]


def git_push_command(command):
    # Remove here-document bodies before tokenizing shell syntax.
    lines = command.splitlines(keepends=True)
    cleaned, pending = [], []
    for line in lines:
        if pending:
            delimiter, strip_tabs = pending[0]
            if (line.rstrip('\r\n').lstrip('\t') if strip_tabs else line.rstrip('\r\n')) == delimiter:
                pending.pop(0)
            continue
        cleaned.append(line)
        for match in re.finditer(r"<<(-?)(?!<)\s*(['\"]?)([A-Za-z_][A-Za-z_0-9]*)\2", line):
            pending.append((match.group(3), bool(match.group(1))))
    lexer = shlex.shlex(''.join(cleaned), posix=True, punctuation_chars=';&|()\n')
    lexer.whitespace = ' \t\r'
    lexer.whitespace_split = True
    lexer.commenters = '#'
    try:
        tokens = list(lexer)
    except ValueError:
        return False
    start = True
    for i, token in enumerate(tokens):
        if token in (';', '&&', '||', '|', '(', '\n'):
            start = True
        elif start:
            if token == 'git' and i + 1 < len(tokens) and tokens[i + 1] == 'push':
                return True
            start = False
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ('pre', 'post', 'prompt', 'stop', 'exceptions', 'rules', 'thresholds'): sub.add_parser(name)
    log = sub.add_parser('log'); log.add_argument('--summary', action='store_true')
    exc = sub.add_parser('exception')
    for flag in ('rule', 'scope', 'reason', 'owner-words', 'expires', 'badge'): exc.add_argument('--' + flag, required=True)
    a = parser.parse_args(); registry = root() / 'management/registry'
    try:
        config = read(registry / 'wardens_rules.json', {})
        rules = config.get('rules', {})
        for rule in rules.values():
            if rule.get('mode') not in ('off', 'warn', 'block') or not rule.get('rule') or not rule.get('text'): raise ValueError('Invalid rule configuration')
        if a.action == 'exception':
            if a.rule not in rules and a.rule not in {r['rule'] for r in rules.values()}: parser.error('Unknown rule: ' + a.rule)
            for field in ('scope', 'reason', 'owner_words'):
                if not getattr(a, field).strip(): parser.error('--' + field.replace('_', '-') + ' must not be empty')
            try:
                expiry = stamp(a.expires)
            except (ValueError, OverflowError):
                parser.error('Expiry must be a valid date or timezone-aware timestamp')
            if expiry <= now(): parser.error('Expiry must be in the future')
            append(registry / 'exceptions.jsonl', vars(a)); print('Exception recorded'); return
        if a.action in ('exceptions', 'log'):
            data = rows(registry / ('exceptions.jsonl' if a.action == 'exceptions' else 'wardens.jsonl'))
            if a.action == 'log' and a.summary:
                counts = {}
                for entry in data: counts[entry.get('rule', 'unknown')] = counts.get(entry.get('rule', 'unknown'), 0) + 1
                print(json.dumps(counts)); return
            print('\n'.join(json.dumps(x) for x in data) or 'No entries.'); return
        if a.action == 'rules': print(json.dumps(config, indent=2)); return
        if a.action == 'thresholds':
            count = config.get('trial_successes', 0)
            print(json.dumps({'trial_successes': count, 'thresholds': [70, 85, 95] if count >= 10 else [65, 80, 90]})); return
        payload = json.load(sys.stdin); tool = payload.get('tool_input') or {}; command = str(tool.get('command', '')); path = str(tool.get('file_path', tool.get('path', ''))); name = payload.get('tool_name', ''); findings = []
        exceptions = rows(registry / 'exceptions.jsonl')
        def flag(key, message):
            rule = rules.get(key)
            if not rule or rule['mode'] == 'off': return
            for e in exceptions:
                if e.get('rule') in (key, rule['rule']) and (e.get('scope') == '*' or bool(e.get('scope')) and any(e['scope'] in value for value in (command, path, name))) and stamp(e['expires']) > now(): return
            findings.append((rule['mode'], key, f"{rule['rule']}: {message}"))
        if a.action == 'pre':
            if re.search(r'\b(?:pkill|killall)\b', command): flag('wide_kill', 'Wide process termination')
            if git_push_command(command): flag('git_push', 'Git push requires approval')
            if re.search(r'\bgit\s+commit\b', command) and not re.search(r'\s--\s+\S', command): flag('commit_paths', 'Commit without explicit paths')
            if any(re.search(r'(?<!\d)' + re.escape(str(p)) + r'(?!\d)', command) for p in config.get('protected_ports', [])): flag('ports', 'Protected port')
            writing = name.lower() in ('write', 'edit', 'multiedit', 'notebookedit') or bool(re.search(r'(?:\s>\s*|\b(?:rm|mv|cp|touch|mkdir|tee)\s)', command))
            if writing and any(x in path or x in command for x in config.get('protected_folders', [])): flag('protected_folder', 'Protected folder write')
            if re.search(r'(^|[\s/"\'])secrets(?:/|\b)', path + ' ' + command): flag('secrets', 'Secret directory access')
            if re.search(r'\b(blender|ffmpeg|zip)\b', command) and 'cpu_cap.py' not in command: flag('long_job', 'Long job without CPU cap')
            if path and writing and not Path(path).exists():
                words = re.findall(r'[a-zà-ÿ]+', Path(path).stem.lower())
                foreign = set(config.get('non_english_words', ['documento', 'cartella', 'progetto', 'appunti', 'lavoro', 'rapporto']))
                if (set(words) & foreign) - set(config.get('filename_allowlist', [])): flag('file_name', 'Check the new filename language')
            if name in ('Agent', 'Task', 'SendMessage') or name.lower().endswith('delegate_task'):
                estimates = rows(registry / 'estimates.jsonl')
                if not any(fresh(e.get('at', e.get('created_at', '')), 30) for e in estimates): flag('agent_estimate', 'No estimate in the last 30 minutes')
                quotas = read(registry / 'quotas.json', {})
                windows = [w for team in quotas.get('teams', {}).values() for w in team.get('windows', [])]
                if any(fresh(w['read_at'], 10) and float(w['used_pct']) > 80 for w in windows): flag('agent_quota', 'Fresh quota exceeds 80% used')
        if a.action == 'prompt':
            quotas = read(registry / 'quotas.json', {})
            findings.append(('warn', 'quota', 'Time: ' + now().astimezone().isoformat(timespec='seconds') + '; quota: ' + json.dumps(quotas.get('teams', {}))))
            result = registry / 'ai_warden_result.txt'
            if result.exists(): findings.append(('warn', 'ai_warden', 'AI warden: ' + result.read_text())); result.unlink()
        if a.action == 'stop':
            entries = turn(payload); serialized = json.dumps(entries, ensure_ascii=False)
            reply = payload.get('last_assistant_message', '')
            if re.search(r'\b\d{1,2}:\d{2}\b', reply) and not re.search(r'\bdate\b', serialized): flag('time', 'Time written without a date command in this turn')
            if re.search(r'\b(?:quota|credit|tokens?)\b.{0,40}(?:\d+\s*%|remaining|used|left)', reply, re.I) and 'shifts.py' not in serialized: flag('credit', 'Credit claim without shifts.py reading')
            if re.search(r'\b(?:remind|reminder|will resume|resume later|come back later|postpone)\b', reply, re.I) and not re.search(r'CronCreate|ScheduleWakeup|schedule_task', serialized, re.I): flag('postponement', 'Postponement without a timer tool call')
            if config.get('ai_warden', {}).get('enabled') and not payload.get('stop_hook_active'):
                prompt = 'Review this reply against these rules and report concerns briefly: ' + json.dumps(rules) + '\nReply: ' + reply
                result = registry / 'ai_warden_result.txt'; result.parent.mkdir(parents=True, exist_ok=True)
                with result.open('w') as out:
                    subprocess.Popen(['claude', '-p', '--model', 'haiku', prompt], stdout=out, stderr=subprocess.DEVNULL, start_new_session=True)
        for mode, key, message in findings: append(registry / 'wardens.jsonl', {'at': now().isoformat(), 'event': a.action, 'mode': mode, 'rule': key, 'message': message})
        if findings:
            message = '; '.join(x[2] for x in findings)
            if a.action == 'pre' and any(m == 'block' for m, _, _ in findings): print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny', 'permissionDecisionReason': message}}))
            elif a.action in ('pre', 'post', 'prompt'): print(json.dumps({'hookSpecificOutput': {'hookEventName': {'pre':'PreToolUse', 'post':'PostToolUse', 'prompt':'UserPromptSubmit'}[a.action], 'additionalContext': message}}))
            else: print(json.dumps({'systemMessage': message}))
    except Exception as error:
        print(json.dumps({'systemMessage': 'Warden warning: ' + str(error)}))

if __name__ == '__main__': main()
