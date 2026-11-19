#!/usr/bin/env python3
"""Run a command while limiting CPU pressure on Linux."""
import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def cpu():
    values = [int(x) for x in Path('/proc/stat').read_text().splitlines()[0].split()[1:]]
    return sum(values[:8]), values[3] + values[4]


def group_ticks(pgid):
    ticks = 0
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            stat = (path / 'stat').read_text().rsplit(')', 1)[1].split()
            if int(stat[2]) == pgid:
                ticks += int(stat[11]) + int(stat[12])
        except (OSError, ValueError, IndexError):
            continue
    return ticks


def usage(previous, current):
    delta = current[0] - previous[0]
    return 1 - (current[1] - previous[1]) / delta if delta > 0 else 0


def wait_calm(calm, log, timeout=30, interval=0.25):
    previous = cpu()
    deadline = time.monotonic() + timeout
    while True:
        time.sleep(interval)
        current = cpu()
        load = usage(previous, current)
        if load < calm:
            return current
        log(f'Waiting for calm CPU: total={load:.4f}')
        if time.monotonic() >= deadline:
            raise TimeoutError('Timed out waiting for calm CPU')
        previous = current


def main():
    p = argparse.ArgumentParser(description=__doc__, epilog='Environment: CAP_CPU_TOTAL (pause total, default 0.70), CAP_CPU_MINE (pause group, 0.64), CAP_CPU_CALM (start threshold, 0.60), CAP_CPU_RESUME (resume total, 0.60). Values are fractions of machine CPU.')
    p.add_argument('--log'); p.add_argument('command', nargs=argparse.REMAINDER); args = p.parse_args()
    cmd = args.command
    if cmd and cmd[0] == '--': cmd = cmd[1:]
    if not cmd: p.error('a command is required after --')
    def log(message):
        if args.log:
            with open(args.log, 'a', encoding='utf-8') as f: f.write(f'{time.time():.3f} {message}\n')
        else:
            print(message, file=sys.stderr)
    try:
        total = float(os.getenv('CAP_CPU_TOTAL', '0.70')); resume = float(os.getenv('CAP_CPU_RESUME', '0.60')); calm = float(os.getenv('CAP_CPU_CALM', '0.60')); mine = float(os.getenv('CAP_CPU_MINE', '0.64'))
        if not all(0 < x <= 1 for x in (total, resume, calm, mine)) or resume > total: raise ValueError('Invalid CPU thresholds')
        previous = wait_calm(calm, log)
        child = subprocess.Popen(cmd, start_new_session=True); stopped = False
        previous_ticks = group_ticks(child.pid)
        try:
            while child.poll() is None:
                time.sleep(0.25); current = cpu(); ticks = group_ticks(child.pid)
                delta = current[0] - previous[0]
                load = usage(previous, current)
                own = max(0, ticks - previous_ticks) / delta if delta > 0 else 0
                previous, previous_ticks = current, ticks
                if not stopped and (load > total or own > mine):
                    try: os.killpg(child.pid, signal.SIGSTOP); stopped = True
                    except ProcessLookupError: pass
                elif stopped and load < resume:
                    try: os.killpg(child.pid, signal.SIGCONT); stopped = False
                    except ProcessLookupError: pass
                if args.log: log(f'total={load:.4f} mine={own:.4f} stopped={stopped}')
        finally:
            if stopped:
                try: os.killpg(child.pid, signal.SIGCONT)
                except ProcessLookupError: pass
            if child.poll() is None:
                try: os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError: pass
                child.wait()
        return child.returncode if child.returncode >= 0 else 128 - child.returncode
    except (OSError, ValueError, TimeoutError) as exc: print(f'Error: {exc}', file=sys.stderr); return 1

if __name__ == '__main__': sys.exit(main())
