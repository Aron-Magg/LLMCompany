#!/usr/bin/env python3
"""Manage the office library catalog."""
import argparse
import json
import os
from pathlib import Path
import sys


def root():
    if os.environ.get('AGENT_OFFICE_ROOT'): return Path(os.environ['AGENT_OFFICE_ROOT']).resolve()
    for path in (Path.cwd(), *Path.cwd().parents):
        if (path / 'management/registry/rooms.json').is_file(): return path
    raise ValueError('Office root not found')


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('add')
    for flag in ('id', 'title', 'path', 'dept'): a.add_argument('--' + flag, required=True)
    a.add_argument('--tags', nargs='*', default=[])
    a = sub.add_parser('search'); a.add_argument('words', nargs='+')
    sub.add_parser('check'); args = p.parse_args()
    try:
        base = root(); file = base / 'management/registry/catalog.json'
        data = json.loads(file.read_text(encoding='utf-8')) if file.exists() else {'entries': []}; entries = data.setdefault('entries', [])
        if args.command == 'add':
            path = (base / args.path).resolve()
            if not path.is_relative_to(base) or not path.exists(): raise ValueError('Path must exist inside the office')
            if any(e['id'] == args.id for e in entries): raise ValueError('Duplicate ID')
            entries.append(dict(id=args.id, title=args.title, path=str(path.relative_to(base)), dept=args.dept, tags=args.tags))
            file.parent.mkdir(parents=True, exist_ok=True); file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            out = base / 'library/CATALOG.md'; out.parent.mkdir(parents=True, exist_ok=True)
            rows = ['# Library catalog', ''] + [f"- **{e['title']}** (`{e['id']}`) — {e['path']} ({e['dept']}; {', '.join(e['tags'])})" for e in entries]
            out.write_text('\n'.join(rows) + '\n', encoding='utf-8'); print(args.id)
        elif args.command == 'search':
            for e in entries:
                text = json.dumps(e, ensure_ascii=False).casefold()
                if all(word.casefold() in text for word in args.words): print(json.dumps(e, ensure_ascii=False))
        else:
            missing = [e['path'] for e in entries if not (base / e['path']).exists()]
            for path in missing: print(f'Missing: {path}')
            if missing: return 1
            print(f'{len(entries)} entries checked')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc: print(f'Error: {exc}', file=sys.stderr); return 1

if __name__ == '__main__': sys.exit(main())
