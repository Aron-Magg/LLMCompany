#!/usr/bin/env python3
"""Track quota readings, estimates and actual usage."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from uuid import uuid4


def root():
    if os.environ.get('AGENT_OFFICE_ROOT'): return Path(os.environ['AGENT_OFFICE_ROOT']).resolve()
    for path in (Path.cwd(), *Path.cwd().parents):
        if (path / 'management/registry/rooms.json').is_file(): return path
    raise ValueError('Office root not found')


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('status'); sub.add_parser('costs')
    a = sub.add_parser('estimate')
    for flag in ('badge', 'task', 'team', 'cost', 'done-when'): a.add_argument('--' + flag, required=True)
    a = sub.add_parser('actuals'); a.add_argument('--id', required=True); a.add_argument('--kind', default='task')
    a = sub.add_parser('check'); a.add_argument('--team', required=True)
    args = p.parse_args()
    try:
        reg = root() / 'management/registry'; reg.mkdir(parents=True, exist_ok=True)
        def read(name, default):
            path = reg / name
            return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
        def lines(name):
            path = reg / name
            return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()] if path.exists() else []
        def append(name, obj):
            with (reg / name).open('a', encoding='utf-8') as f: f.write(json.dumps(obj, ensure_ascii=False) + '\n')
        quotas = read('quotas.json', {}).get('teams', {})
        if args.command == 'status': print(json.dumps(quotas, indent=2)); return 0
        if args.command == 'check':
            windows = quotas.get(args.team, {}).get('windows', [])
            if not windows: print('Warning: quota unavailable'); return 0
            for w in windows:
                print(f"{w.get('name', 'window')}: {w.get('used_pct', 'unknown')}% (read {w.get('read_at', 'unknown')}, reset {w.get('resets_at', 'unknown')})")
                try:
                    read_at = datetime.fromisoformat(w['read_at'].replace('Z', '+00:00')); reset = datetime.fromisoformat(w['resets_at'].replace('Z', '+00:00'))
                    current = datetime.now(timezone.utc)
                    if read_at.tzinfo is None or reset.tzinfo is None or read_at > current or reset <= current: raise ValueError()
                    if float(w['used_pct']) == 100: return 75
                except (ValueError, TypeError, KeyError): print('Warning: quota is not confirmed')
            return 0
        estimates = lines('estimates.jsonl'); actuals = lines('actuals.jsonl')
        if args.command == 'estimate':
            obj = dict(id=uuid4().hex, badge=args.badge, task=args.task, team=args.team, cost=args.cost, done_when=args.done_when, at=datetime.now(timezone.utc).isoformat(), windows=quotas.get(args.team, {}).get('windows', []))
            append('estimates.jsonl', obj); print(obj['id']); return 0
        if args.command == 'actuals':
            estimate = next((e for e in estimates if e['id'] == args.id), None)
            if not estimate: raise ValueError('Estimate not found')
            if any(a['id'] == args.id for a in actuals): raise ValueError('Estimate already closed')
            closed = {a['id'] for a in actuals}; overlaps = [e['id'] for e in estimates if e['id'] != args.id and e['team'] == estimate['team'] and e['id'] not in closed]
            if overlaps: print('Warning: other estimates are open; usage may overlap')
            end = {w['name']: w for w in quotas.get(estimate['team'], {}).get('windows', [])}; results = []
            for start in estimate['windows']:
                w = end.get(start.get('name')); result = {'name': start.get('name'), 'points': None}
                if w:
                    try:
                        before = datetime.fromisoformat(start['read_at'].replace('Z', '+00:00')); after = datetime.fromisoformat(w['read_at'].replace('Z', '+00:00')); reset = datetime.fromisoformat(start['resets_at'].replace('Z', '+00:00'))
                        if after < before: result['reason'] = 'reading is older'
                        elif before < reset <= after or start['resets_at'] != w['resets_at'] or float(w['used_pct']) < float(start['used_pct']): result['reason'] = 'reset between readings'
                        else: result['points'] = float(w['used_pct']) - float(start['used_pct'])
                    except (KeyError, ValueError, TypeError): result['reason'] = 'incomplete reading'
                else: result['reason'] = 'reading unavailable'
                results.append(result)
            obj = dict(id=args.id, kind=args.kind, at=datetime.now(timezone.utc).isoformat(), windows=results, overlapping_estimates=overlaps); append('actuals.jsonl', obj); print(json.dumps(obj, indent=2)); return 0
        rows = ['# Cost table', '', '| Task | Team | Kind | Window | Points |', '| --- | --- | --- | --- | --- |']
        for a in actuals:
            e = next((x for x in estimates if x['id'] == a['id']), {})
            for w in a.get('windows', []): rows.append('| ' + ' | '.join(str(x).replace('|', '\\|').replace('\n', ' ') for x in (e.get('task', ''), e.get('team', ''), a.get('kind', ''), w.get('name', ''), w.get('points') if w.get('points') is not None else w.get('reason', 'unknown'))) + ' |')
        (reg / 'COST_TABLE.md').write_text('\n'.join(rows) + '\n', encoding='utf-8'); return 0
    except (OSError, ValueError, KeyError, TypeError) as exc: print(f'Error: {exc}', file=sys.stderr); return 1

if __name__ == '__main__': sys.exit(main())
