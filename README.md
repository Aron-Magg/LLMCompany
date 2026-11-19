# agent-office

A Claude Code skill and folder template for running several AI agents in one repository like a small office. Agents get rooms, a badge, layered rule files, mailboxes, a knowledge library, estimates before work, approvals recorded with a hash, and optional wardens that enforce the rules through hooks.

The package holds the skill (`SKILL.md`), reference documents, a folder template, small Python tools with no dependencies, and an init script. By Aron Maggisano. Proprietary license, all rights reserved.

## Prerequisites

- Python 3.9 or newer (standard library only).
- Claude Code, for the hooks and for the skill itself.
- Git, if you want the commit-by-path habits and the commit warden.
- Optional: Linux with `systemd --user` and the `claude` command on the PATH, only for the away-mode watchdog and the AI warden.

## Install

Unzip into `~/.claude/skills/agent-office/`, then ask Claude Code to "set up an agent office in this folder". It will run `scripts/init.py` into an empty folder:

```
python3 ~/.claude/skills/agent-office/scripts/init.py --target <empty folder> --owner "Name" --language en --brand "Brand" --departments design,sales --teams claude,codex
```

Required: `--target`, `--owner`, `--language`. `--brand` is the exact spelling rule R01 enforces by judgment; if omitted it defaults to the owner name. `--departments` and `--teams` are optional. A non-empty target is refused unless you add `--force`: then only missing files are created, and existing registry files, `AGENTS.md`, `LESSONS.md` and `DIARY.md` are kept.

## Author and license

Created by Aron Maggisano. Proprietary software, all rights reserved (see `LICENSE`). Use requires a license from the author.
Contact: https://github.com/Aron-Magg
