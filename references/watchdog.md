# The watchdog

The watchdog is a small timer-driven script that lets the office work while the owner is away. It is not a model and consumes no tokens by itself. It needs `systemd --user` (Linux) and the `claude` command on the PATH.

## Why

When the owner leaves the computer, a message written for an agent sits unread in a mailbox until someone opens a chat. The watchdog wakes the right agent for explicit, pre-approved instructions and nothing else.

## Commands

- `watchdog.py guard [--until HH:MM | --hours N] [--no-systemd]`: installs and enables a systemd **user** timer from the templates in `tools/systemd/`. Default length: 8 hours. `--no-systemd` only records the state (useful for tests). Starting the guard writes the limits in `watchdog.json`: check the file afterwards and edit the values you want.
- `watchdog.py pause`: stops the timer.
- `watchdog.py status`: shows whether the guard is on and when it ends (the rounds are in the log, see below).
- `watchdog.py round`: one pass. The timer runs it every 5 minutes.

## What one round does

1. Check the quotas with `shifts.py check`. If a window is confirmed exhausted, do nothing.
2. Scan every mailbox for an **open** message flagged `instructions: yes`. The owner (or management on the owner's behalf) writes such a message with `post.py write --instructions ...`. The tool does not verify the sender: keeping the flag for the owner is a rule of the office, and agents must not use it.
3. Find the session of the addressee: the badge with an active shift in that room, mapped to a session id in `management/registry/sessions.json` (filled by the session-start hook). Wake it with `claude -p --resume <session>` for that message only. One wake at a time.
4. Log the round in `management/registry/watchdog.jsonl`.

If the addressee has no known session, nothing is woken.

## Limits (in `management/registry/watchdog.json`)

- Maximum wakes per guard period (for example 6).
- Maximum tries per message (for example 2).
- Maximum minutes per wake (for example 45).

The awakened agent executes only that message and follows every rule of the office. It does not start new work, spend the other team's quota, or ask the owner questions that block.

## Rules of use

- **Only the owner turns it on**, or management for the owner from the terminal. Agents never enable the guard on their own initiative.
- It switches itself off at the end time.
- It respects the shifts: no wake with quota exhausted.
- Nothing else runs permanently in the office. The watchdog is the single exception to the rule "no permanent processes"; its activity is in `watchdog.jsonl`. The package ships no dashboard.
- Always check `watchdog.py status` before leaving, and `pause` when you return.
