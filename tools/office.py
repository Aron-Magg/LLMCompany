#!/usr/bin/env python3
"""Record office shifts, movements and approvals."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
from uuid import uuid4


def root():
    if os.environ.get('AGENT_OFFICE_ROOT'):
        return Path(os.environ['AGENT_OFFICE_ROOT']).resolve()
    for path in (Path.cwd(), *Path.cwd().parents):
        if (path / 'management/registry/rooms.json').is_file():
            return path
    raise ValueError('Office root not found')


def now():
    return datetime.now(timezone.utc).isoformat()


def hook(event, data):
    session = data.get('session_id')
    if not session:
        return
    base = root() if os.environ.get('AGENT_OFFICE_ROOT') else Path(data.get('cwd', Path.cwd())).resolve()
    if not os.environ.get('AGENT_OFFICE_ROOT'):
        base = next(p for p in (base, *base.parents) if (p / 'management/registry/rooms.json').is_file())
    reg = base / 'management/registry'
    def read(name, default):
        path = reg / name
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
    def write(name, value):
        (reg / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    def move(shift, room):
        shift['room'] = room
        with (reg / 'moves.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps({'badge': shift['badge'], 'room': room, 'at': now()}) + '\n')
    rooms = read('rooms.json', {}).get('rooms', [])
    presence = read('presence.json', {})
    shifts = presence.setdefault('shifts', [])
    sessions = read('sessions.json', {}).setdefault('sessions', {})
    badge = sessions.get(session, {}).get('badge')
    shift = next ( (s for s in shifts if s['badge'] == badge and s['status'] == 'active'), None)
    def room_for(path):
        path = Path(path).expanduser()
        if not path.is_absolute():
            path = Path(data.get('cwd', base)) / path
        path = path.resolve()
        matches = [(len(str((base / r['path']).resolve())), r['id']) for r in rooms
                   if r.get('path') and path.is_relative_to((base / r['path']).resolve())]
        return max(matches)[1] if matches else None
    if event == 'start':
        if not shift:
            used = {s['name'].casefold() for s in shifts if s['status'] == 'active'}
            name = next((n for n in ('Alex', 'Sam', 'Jamie', 'Taylor', 'Jordan') if n.casefold() not in used), 'Agent ' + uuid4().hex[:6])
            badge = uuid4().hex[:12]
            room = room_for(data.get('cwd', str(base))) or (rooms[0]['id'] if rooms else None)
            if room is None:
                return
            shift = dict(badge=badge, name=name, room=room, task='', lead=None, role=None, status='active', started_at=now())
            shifts.append(shift)
            move(shift, room)
            write('presence.json', presence)
        sessions[session] = {'badge': badge, 'seen': now()}
        write('sessions.json', {'sessions': sessions})
        context = f'You are {shift["name"]}, badge {shift["badge"]}. Clock your task with: office.py task --badge {shift["badge"]} --task "..."'
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': context}}))
    elif shift and data.get('tool_name'):
        def paths(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if isinstance(item, str) and (key in ('path', 'file_path', 'filePath', 'directory', 'cwd') or key.endswith('_path')):
                        yield item
                    elif isinstance(item, (dict, list)):
                        yield from paths(item)
            elif isinstance(value, list):
                for item in value:
                    yield from paths(item)
        for path in paths(data.get('tool_input', {})):
            room = room_for(path)
            if room and room != shift['room']:
                move(shift, room)
                write('presence.json', presence)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('in')
    for flag in ('name', 'room', 'task'): a.add_argument('--' + flag, required=True)
    a.add_argument('--lead'); a.add_argument('--role')
    for command in ('move', 'task', 'rest', 'out', 'approve'):
        a = sub.add_parser(command); a.add_argument('--badge', required=True)
        if command == 'move': a.add_argument('--room', required=True)
        if command == 'task': a.add_argument('--task', required=True)
        if command == 'out':
            group = a.add_mutually_exclusive_group(required=True)
            group.add_argument('--report'); group.add_argument('--resignation')
        if command == 'approve':
            a.add_argument('--what', required=True); a.add_argument('--file', required=True); a.add_argument('--commit')
    sub.add_parser('who')
    a = sub.add_parser('hook'); a.add_argument('event', choices=('start', 'tool'))
    args = p.parse_args()
    if args.command == 'hook':
        try:
            hook(args.event, json.load(sys.stdin))
        except Exception:
            pass  # Hooks must never interrupt the host.
        return 0
    try:
        base = root(); reg = base / 'management/registry'; reg.mkdir(parents=True, exist_ok=True)
        def read(name, default):
            path = reg / name
            return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
        def write(name, data):
            (reg / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        def append(name, data):
            with (reg / name).open('a', encoding='utf-8') as f: f.write(json.dumps(data, ensure_ascii=False) + '\n')
        presence = read('presence.json', {'shifts': []}); shifts = presence.setdefault('shifts', [])
        if args.command == 'who':
            print(json.dumps([s for s in shifts if s['status'] == 'active'], indent=2)); return 0
        if args.command == 'in':
            if any(s['name'].casefold() == args.name.casefold() and s['status'] == 'active' for s in shifts): raise ValueError('Person already has an open shift')
            rooms = read('rooms.json', {'rooms': []})['rooms']
            if not any(r['id'] == args.room for r in rooms): raise ValueError('Unknown room')
            if args.lead and not any(s['badge'] == args.lead and s['status'] == 'active' for s in shifts): raise ValueError('Lead is not active')
            badge = uuid4().hex[:12]; shift = dict(badge=badge, name=args.name, room=args.room, task=args.task, lead=args.lead, role=args.role, status='active', started_at=now())
            shifts.append(shift); staff = read('staff.json', {'staff': []})
            if not any(s.get('name', '').casefold() == args.name.casefold() for s in staff.setdefault('staff', [])): staff['staff'].append({'name': args.name})
            write('staff.json', staff); write('presence.json', presence); append('moves.jsonl', {'badge': badge, 'room': args.room, 'at': now()}); print(badge); return 0
        shift = next((s for s in shifts if s['badge'] == args.badge and s['status'] == 'active'), None)
        if not shift: raise ValueError('Active badge not found')
        if args.command == 'move':
            if not any(r['id'] == args.room for r in read('rooms.json', {'rooms': []})['rooms']): raise ValueError('Unknown room')
            shift['room'] = args.room; append('moves.jsonl', {'badge': args.badge, 'room': args.room, 'at': now()})
        elif args.command == 'task': shift['task'] = args.task
        elif args.command == 'rest': shift.update(status='rest', ended_at=now())
        elif args.command == 'out':
            if bool(shift.get('lead')) != bool(args.report): raise ValueError('Team members require a report; others require a resignation')
            path = (base / (args.report or args.resignation)).resolve()
            if not path.is_file(): raise ValueError('Report or resignation file not found')
            shift.update(status='out', ended_at=now(), report=args.report, resignation=args.resignation)
        elif args.command == 'approve':
            path = (base / args.file).resolve()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            append('approvals.jsonl', dict(badge=args.badge, what=args.what, file=args.file, commit=args.commit, sha256=digest, at=now()))
        write('presence.json', presence); return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Error: {exc}', file=sys.stderr); return 1


if __name__ == '__main__': sys.exit(main())
