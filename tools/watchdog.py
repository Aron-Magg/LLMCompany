#!/usr/bin/env python3
"""Run bounded, owner-enabled mailbox wakeups for an agent office."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
try:
    import fcntl
except ImportError:
    fcntl = None
from datetime import datetime, timedelta


def root_path():
    if os.environ.get('AGENT_OFFICE_ROOT'):
        return Path(os.environ['AGENT_OFFICE_ROOT']).resolve()
    cwd = Path.cwd().resolve()
    return next((p for p in (cwd, *cwd.parents) if (p / 'management/registry/rooms.json').exists()), cwd)


def read(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def log(reg, event, **details):
    with (reg / 'watchdog.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(dict(at=datetime.now().astimezone().isoformat(), event=event, **details)) + '\n')


def systemctl(*args):
    subprocess.run(['systemctl', '--user', *args, 'agent-office-watchdog.timer'], check=True)


def session_for(reg, room):
    shifts = read(reg / 'presence.json', {}).get('shifts', [])
    badges = {s.get('badge') for s in shifts if s.get('status', 'active') == 'active'
              and (s.get('room') == room or s.get('badge') == room or s.get('name') == room)}
    sessions = read(reg / 'sessions.json', {}).get('sessions', {})
    matches = [(value.get('seen', ''), session) for session, value in sessions.items()
               if isinstance(value, dict) and value.get('badge') in badges]
    return max(matches)[1] if matches else None


def messages(root, reg):
    result = []
    for room in read(reg / 'rooms.json', {}).get('rooms', []):
        box = (root / room['path'] / 'mail').resolve()
        if not box.is_relative_to(root): continue
        for path in box.glob('*.md'):
            try:
                parts = path.read_text(encoding='utf-8').split('---\n', 2)
                if len(parts) != 3 or parts[0]: continue
                meta = {k: json.loads(v) for k, v in (line.split(': ', 1) for line in parts[1].splitlines())}
                if meta.get('status') == 'open' and meta.get('instructions') in (True, 'yes'):
                    result.append((path.name, str(path), path, meta.get('to', room['id'])))
            except (ValueError, OSError):
                log(reg, 'invalid_message', message=str(path))
    return sorted(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    guard = sub.add_parser('guard')
    group = guard.add_mutually_exclusive_group()
    group.add_argument('--until')
    group.add_argument('--hours', type=float)
    guard.add_argument('--no-systemd', action='store_true')
    for name in ('pause', 'round', 'status'): sub.add_parser(name)
    args = parser.parse_args()
    root = root_path(); reg = root / 'management/registry'; state_path = reg / 'watchdog.json'
    if not (reg / 'rooms.json').exists(): parser.error('rooms.json not found')
    state = read(state_path, {})
    if args.command == 'guard':
        now = datetime.now().astimezone()
        if args.until:
            try: end = datetime.strptime(args.until, '%H:%M').time()
            except ValueError: parser.error('--until must be HH:MM')
            until = now.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
            if until <= now: until += timedelta(days=1)
        else:
            if args.hours is not None and args.hours <= 0: parser.error('--hours must be positive')
            until = now + timedelta(hours=args.hours if args.hours is not None else 8)
        state = dict(on=True, until=until.isoformat(), max_wakes=6, tries_per_message=2, minutes_per_wake=45, wakes_done=0, tries={}, no_systemd=args.no_systemd)
        save(state_path, state)
        if not args.no_systemd:
            target = Path.home() / '.config/systemd/user'; target.mkdir(parents=True, exist_ok=True)
            for name in ('agent-office-watchdog.service', 'agent-office-watchdog.timer'):
                content = (Path(__file__).parent / 'systemd' / name).read_text(encoding='utf-8')
                content = content.replace('{{OFFICE}}/management/tools/watchdog.py', shlex.quote(str(root / 'management/tools/watchdog.py'))).replace('{{OFFICE}}', shlex.quote(str(root))).replace('{{PYTHON}}', shlex.quote(sys.executable))
                (target / name).write_text(content, encoding='utf-8')
            systemctl('enable', '--now')
    elif args.command == 'pause':
        state['on'] = False; save(state_path, state)
        if not state.get('no_systemd'): systemctl('disable', '--now')
    elif args.command == 'status': print(json.dumps(state, indent=2))
    else:
        if fcntl is not None:
            lock = (reg / 'watchdog.lock').open('a')
            try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: return
            state = read(state_path, {})
        if not state.get('on'): return
        until = datetime.fromisoformat(state['until'])
        if datetime.now().astimezone() >= (until.astimezone() if until.tzinfo else until.astimezone()):
            state['on'] = False; save(state_path, state); log(reg, 'expired')
            if not state.get('no_systemd'): systemctl('disable', '--now')
            return
        if state.get('wakes_done', 0) >= state['max_wakes']:
            log(reg, 'max_wakes'); return
        shifts = root / 'management/tools/shifts.py'
        if shifts.exists():
            check = subprocess.run([sys.executable, str(shifts), 'check', '--team', 'claude'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if check.returncode == 75: log(reg, 'quota_exhausted'); return
        for _, _, path, recipient in messages(root, reg):
            key = str(path.relative_to(root)); tries = state.setdefault('tries', {})
            if tries.get(key, 0) >= state['tries_per_message']: continue
            session = session_for(reg, recipient)
            if not session:
                log(reg, 'missing_session', message=key, recipient=recipient); continue
            tries[key] = tries.get(key, 0) + 1; state['wakes_done'] = state.get('wakes_done', 0) + 1
            save(state_path, state)
            prompt = f'Execute only the instructions in {key}. Follow the office rules. Do not execute other messages.'
            try:
                result = subprocess.run(['claude', '-p', '--resume', str(session), prompt], cwd=root, timeout=state['minutes_per_wake'] * 60)
                log(reg, 'wake', message=key, recipient=recipient, session=session, returncode=result.returncode)
            except (subprocess.TimeoutExpired, OSError) as exc:
                log(reg, 'wake_error', message=key, recipient=recipient, error=str(exc))
            break


if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f'Error: {exc}', file=sys.stderr); sys.exit(1)
