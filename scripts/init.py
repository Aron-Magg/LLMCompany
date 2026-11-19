#!/usr/bin/env python3
"""Initialize an agent office in a target directory."""
import argparse
import json
import shutil
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', required=True, help='Office directory')
    p.add_argument('--owner', required=True, help='Office owner')
    p.add_argument('--language', required=True, help='Office language')
    p.add_argument('--brand', default=None, help='Office brand')
    p.add_argument('--departments', default='', help='Comma-separated department IDs')
    p.add_argument('--teams', default='claude,codex', help='Comma-separated team IDs')
    p.add_argument('--force', action='store_true', help='Allow a non-empty target')
    a = p.parse_args()
    if a.brand is None: a.brand = a.owner
    target = Path(a.target).resolve()
    kept = set()
    if target.exists() and any(target.iterdir()) and not a.force:
        p.error('target is not empty; use --force to merge')
    target.mkdir(parents=True, exist_ok=True)
    template = PACKAGE / 'template'
    if a.force:
        kept.update(p for p in target.rglob('*') if p.is_file() and (p.is_relative_to(target / 'management/registry') or p.name in ('AGENTS.md', 'LESSONS.md', 'DIARY.md')))
        for path in sorted(kept): print('Kept ' + str(path.relative_to(target)))
    if template.exists():
        def preserve(directory, names):
            relative = Path(directory).relative_to(template)
            ignored = []
            for name in names:
                destination = target / relative / name
                if destination.is_file() and (relative.parts[:2] == ('management', 'registry') or name in ('AGENTS.md', 'LESSONS.md', 'DIARY.md')):
                    kept.add(destination)
                    ignored.append(name)
            return ignored
        shutil.copytree(template, target, dirs_exist_ok=True, ignore=preserve)
    shutil.copytree(PACKAGE / 'tools', target / 'management/tools', dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', 'tests'))
    depts = [v.strip() for v in a.departments.split(',') if v.strip()]
    if any(not d.replace('-', '').replace('_', '').isalnum() for d in depts):
        p.error('department IDs must contain only letters, numbers, underscores or hyphens')
    rooms = {'management': 'management', 'canteen': 'canteen', 'library': 'library', 'exchange': 'exchange', 'archive': 'archive', 'inspectorate': 'inspectorate', 'staff': 'staff'}
    rooms.update({d: 'departments/' + d for d in depts})
    for room in rooms.values():
        (target / room / 'mail').mkdir(parents=True, exist_ok=True)
    for folder in ['exchange/in', 'exchange/out', 'staff/roles', 'staff/resignations']:
        (target / folder).mkdir(parents=True, exist_ok=True)
    for d in depts:
        path = target / 'departments' / d
        (path / 'memory').mkdir(exist_ok=True)
        (path / 'memory/INDEX.md').touch(exist_ok=True)
        (path / 'AGENTS.md').touch(exist_ok=True)
    reg = target / 'management/registry'
    reg.mkdir(parents=True, exist_ok=True)
    defaults = {'rooms.json': {'rooms': [{'id': k, 'path': v} for k, v in rooms.items()]}, 'staff.json': {}, 'roles.json': {}, 'presence.json': {}, 'quotas.json': {'teams': {v.strip(): {'windows': []} for v in a.teams.split(',') if v.strip()}}, 'catalog.json': {}, 'watchdog.json': {}}
    for name, value in defaults.items():
        path = reg / name
        if not path.exists(): path.write_text(json.dumps(value, indent=2) + '\n')
    for name in ['moves', 'approvals', 'estimates', 'actuals', 'exceptions', 'wardens']:
        (reg / (name + '.jsonl')).touch(exist_ok=True)
    for name in ['AGENTS.md', 'management/AGENTS.md', 'management/DIARY.md', 'management/LESSONS.md']:
        (target / name).touch(exist_ok=True)
    for name, content in {'README.md': f'# {a.brand or "Agent office"}\n\nOffice of {a.owner}. See AGENTS.md for the rules.\n', 'exchange/RECEIPTS.md': '# Receipts\n'}.items():
        path = target / name
        if not path.exists(): path.write_text(content, encoding='utf-8')
    link = target / 'CLAUDE.md'
    if not link.exists() and not link.is_symlink(): link.symlink_to('AGENTS.md')
    for path in target.rglob('*'):
        if path.is_file() and not path.is_symlink() and path not in kept:
            try:
                text = path.read_text(encoding='utf-8')
                for key, value in {'OWNER': a.owner, 'LANGUAGE': a.language, 'BRAND': a.brand}.items(): text = text.replace('{{' + key + '}}', value)
                path.write_text(text, encoding='utf-8')
            except UnicodeError: pass
    print('Office initialized. Review the rules and configure quotas before starting agents.')

if __name__ == '__main__': main()
