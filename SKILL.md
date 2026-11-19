---
name: agent-office
description: Use when the user wants to build an "office of AI agents": a project folder where several Claude Code agents work as colleagues with rooms, layered rules, mailboxes, a knowledge library, estimates, approvals and guards. Use it to scaffold the folder structure, write the rules, wire the hooks and set up the helper tools. Not for single-agent tasks or one-off scripts.
---

# Agent office

Author: Aron Maggisano · License: proprietary, all rights reserved (see `LICENSE`) · Version 1.1

A way to run many AI agents in one repository like a small company. Agents have rooms, a badge, written rules and shared tools. Everything that matters is written in files, so a new chat can resume from them.

## What this skill gives

- A folder skeleton (`template/`) with the rooms of the office.
- A root rule file with 30 generic rules, extended level by level.
- Small Python tools (`tools/`): badge and clock-in, mailboxes, quota and estimates, guards, CPU cap, library catalog, optional away-mode watchdog.
- Hook wiring for Claude Code so that rules are enforced by scripts, not by memory.
- Role cards, lessons and handover habits that keep knowledge across chats.

## Quick start

1. Choose an empty target folder (a new project, or a new subfolder). Do not copy `template/` by hand: `init.py` does it.
2. Run, with the absolute path of the installed skill:
   `python3 ~/.claude/skills/agent-office/scripts/init.py --target <folder> --owner "Name" --language en --brand "Brand" [--departments design,sales] [--teams claude,codex]`.
   Pass `--brand` for the exact spelling of your brand (rule R01); if omitted it defaults to the owner name. The script copies the template, creates the rooms and mailboxes, copies the tools into `<target>/management/tools/`, writes the registry files in `management/registry/`, creates the root `README.md` and `exchange/RECEIPTS.md`, a `CLAUDE.md` link to `AGENTS.md`, and fills `{{OWNER}}`, `{{LANGUAGE}}` and `{{BRAND}}`. A non-empty target is refused unless you add `--force`, which merges into it and keeps existing registry files.
3. Check that the new folder has `management/registry/rooms.json`.
4. The hooks are already installed in `<target>/.claude/settings.json`: open it and check it. Merge it by hand only if the project already had its own settings file (merging twice duplicates hooks). It calls `wardens.py` before and after tool use, on each prompt and at stop, and `office.py` at session start and after tool use.
5. Open Claude Code in the folder. The session-start hook gives the first agent a badge; it reads the root `AGENTS.md`, declares its task (`office.py task`) and checks its mailbox.

To keep the owner's preference rule (R30), edit it in the root `AGENTS.md`; `management/DIARY.md` and `management/LESSONS.md` are starter files with a heading and the entry format.

## The 10 core principles

1. **Rules live in one place.** Each rule is written once in the root `AGENTS.md`. Departments, role cards and lessons point to it by code ("see R09"), never copy it.
2. **Measure, don't guess.** Sizes, times, quotas and defects are measured on real files. If it can't be measured, say so.
3. **Estimate before every task.** Write a short estimate (task, team, quota read with time, cost, margin) and tell the owner before work starts.
4. **Approval means a commit.** When the owner approves something with an explicit yes, commit it at once with the message `Approved: <what>` (the agent does it; `office.py approve` only records a SHA-256 and optional commit id). Heavy binaries are copied with a hash instead of committed.
5. **The other team reviews blind.** Before delivery, a colleague who did not do the work and has no context checks it.
6. **Log every correction of the owner.** Write it at once, in the owner's words, with the mistake, the rule and where it applies. A rule broken twice becomes an automatic guard.
7. **Mechanical work by script, judgment by agents.** Counting, renaming, checking and copying are scripts. Agents decide, write and review.
8. **Never touch services, originals or secrets.** Do not stop the owner's running services. Never edit protected originals. Secrets live only in `secrets/` folders outside git.
9. **A broken guard warns, never blocks.** If a guard crashes, has stale data or cannot read quota, it gives a warning only. Blocking is for explicit, tested rules.
10. **Files and folders in English.** New names are English and the content uses the owner's language. One naming rule for the whole office.

## Map of `references/`


- `architecture.md`: rooms, layered rules, mailboxes, exchange, library, archive, inspectorate, projects, glossary.
- `processes.md`: entering, badge and clock-in, shifts and quotas, estimates, approvals, lessons log, handovers, blind reviews, workshop, "fired" procedure.
- `rules.md`: the 30 generic rules, each with exceptions, check and a typical mistake.
- `wardens.md`: hooks, the implemented checks, exceptions with expiry, anti-deadlock, cheap AI warden (off by default), census of judgment rules.
- `organization.md`: roles, role cards, managers, teams with a lead, two model teams.
- `watchdog.md`: the optional away-mode timer that wakes an agent for flagged messages.
- `lessons.md`: generic failure patterns and their remedies.

## Map of `template/`

`AGENTS.md` (root rules with the placeholders `{{OWNER}}`, `{{LANGUAGE}}`, `{{BRAND}}`, filled by `init.py`), plus one `AGENTS.md` for `management/`, `departments/`, `canteen/`, `library/`, `exchange/`, `inspectorate/`, `staff/`, `staff/roles/_example/ROLE_CARD.md`, the starter files `management/LESSONS.md` and `management/DIARY.md`, `management/registry/wardens_rules.json` (default warden rules) and `.claude/settings.json` (hooks).

## Map of `tools/` and `scripts/`

All tools are plain Python 3 with no external services or dependencies. Each has a test in `tools/tests/`. In an office they are copied to `management/tools/` and find the office root through `AGENT_OFFICE_ROOT` or by walking up from the current folder to `management/registry/rooms.json`.

- `tools/office.py`: badge, clock-in and out, task, rest, approvals with SHA-256.
- `tools/post.py`: mailboxes: write, read new or open, close.
- `tools/shifts.py`: quota reading, estimate, actuals, cost table.
- `tools/wardens.py`: rules engine for hooks (pre, post, prompt, stop) and the commands `exception`, `exceptions`, `log`, `rules`, `thresholds`.
- `tools/cpu_cap.py`: CPU cap for long jobs.
- `tools/library.py`: catalog add, search, check.
- `tools/adapters/quota_from_ccusage.py`: example quota adapter.
- `tools/watchdog.py`: optional guard timer (see `references/watchdog.md`).
- `scripts/init.py`: creates the skeleton: `--target DIR --owner NAME --language CODE [--brand NAME] [--departments a,b] [--teams claude,codex] [--force]`.

## Glossary

Badge, clock-in, shift, quota, estimate, warden and blind review are defined in `references/architecture.md`. The "owner" is the human who directs the office; a "warden" is an automatic check wired to a hook.
