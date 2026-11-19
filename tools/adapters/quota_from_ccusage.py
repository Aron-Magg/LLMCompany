#!/usr/bin/env python3
"""Import a normalized JSON quota snapshot.

Input: {"teams": {"team": {"windows": [{"name": "session", "used_pct": 40,
"read_at": "ISO timestamp", "resets_at": "ISO timestamp"}]}}}. A missing
source leaves the existing registry untouched. Transform ccusage output into
this format before using this example adapter.
"""
import argparse
import json
import os
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('source'); args = p.parse_args()
    source = Path(args.source)
    if not source.is_file(): print('Warning: source not found; quotas unchanged'); return 0
    try:
        data = json.loads(source.read_text(encoding='utf-8'))
        for team in data['teams'].values():
            for w in team['windows']:
                if not all(k in w for k in ('name', 'used_pct', 'read_at', 'resets_at')) or not 0 <= float(w['used_pct']) <= 100: raise ValueError('Invalid window')
        root = Path(os.environ['AGENT_OFFICE_ROOT']).resolve() if os.environ.get('AGENT_OFFICE_ROOT') else next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / 'management/registry/rooms.json').is_file())
        target = root / 'management/registry/quotas.json'; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8'); return 0
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc: print(f'Error: {exc}', file=sys.stderr); return 1

if __name__ == '__main__': sys.exit(main())
