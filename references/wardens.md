# Wardens: rules enforced by scripts

A rule that lives only in a text file gets forgotten. A **warden** is a small check wired to a Claude Code hook. It reads the event, applies a rule and either warns or blocks. Memory is for knowledge; wardens are for discipline. Only what is listed below is implemented; every other rule in `rules.md` is checked by judgment.

## Hook entry points

`.claude/settings.json` (installed by `init.py`) wires these events. Claude Code sends the event as JSON on stdin.

| Hook | Command | What it does |
|---|---|---|
| PreToolUse | `wardens.py pre` | Inspects the command or file path before the tool runs: wide kill, push, commit without paths, protected ports and folders, secrets, long job without CPU cap, new file with a non-English name, agent launched without a fresh estimate or above 80% quota. |
| PostToolUse | `wardens.py post` | Reserved. No shipped rule uses it; it is wired so you can add post-run checks. (`office.py hook tool` in the same event records room moves.) |
| UserPromptSubmit | `wardens.py prompt` | Adds the current time and the quota readings to the context; shows the result of the last AI warden run, if any. |
| Stop | `wardens.py stop` | Reads the last reply: a clock time without a `date` call, a credit claim without a `shifts.py` call, a deferral without a scheduling tool call. Optionally starts the AI warden. It does not check open shifts or proof of completion. |

A blocking `pre` finding is returned as `hookSpecificOutput.permissionDecision: "deny"` with a reason; warnings are returned as additional context (or a system message at Stop). Every hook command ends with `|| true`, so a crash of a warden never stops the session. The settings file is installed by `init.py`: inspect it, and merge it by hand only if your project already has its own `.claude/settings.json` (merging it twice duplicates hooks).

Matching is textual: a command that only mentions `git push` inside a string can trigger the warden. That is the price of a cheap check; use an exception if it gets in the way.

## Warden ids and rule codes

| Warden id | Rule | Default mode | Checks |
|---|---|---|---|
| `ports` | R18 | block | a protected port number appears in a command (`protected_ports`, empty by default) |
| `wide_kill` | R19 | block | `pkill` or `killall` |
| `git_push` | R05 | block | `git push` |
| `commit_paths` | R05 | warn | `git commit` without `-- <paths>` |
| `protected_folder` | R21 | block | a write touching a folder in `protected_folders` (empty by default) |
| `secrets` | R22 | block | a path or command touching a `secrets/` folder |
| `long_job` | R09 | warn | `blender`, `ffmpeg` or `zip` without `cpu_cap.py` |
| `file_name` | R03 | warn | a new file whose name contains a word from `non_english_words` (configurable, with `filename_allowlist`) |
| `time` | R02 | warn | a clock time in the reply with no `date` call in the turn |
| `credit` | R06 | warn | a credit claim in the reply with no `shifts.py` call |
| `agent_estimate` | R06 | warn | an agent is launched with no estimate in the last 30 minutes |
| `agent_quota` | R06 | block | an agent is launched while any team's fresh reading (under 10 minutes old) is above 80% used |
| `postponement` | R07 | warn | a deferral word in the reply and no scheduling tool call in the turn |

Language (R02), the 65% and 90% thresholds and the 70/85/95 promotion are not enforced by a script. `wardens.py thresholds` prints which set applies (trial or promoted) for agents to follow; `agent_quota` always uses 80%, and it looks at any team's window, not only the team of the agent being launched. Rule codes in `wardens_rules.json` follow `rules.md`.

## Rules file

`management/registry/wardens_rules.json` lists the rules. Each has a warden id, the office `rule` code, a `mode` and a `text`:

- `off`: ignored.
- `warn`: the agent sees a message and continues.
- `block`: the action is refused with the reason.

Use **block** only for rules that are explicit, tested and cheap to satisfy (push, wide kill, protected originals, secrets, protected ports). Everything else warns. Only the owner changes the rules.

Inspect: `wardens.py rules`, `wardens.py thresholds`, `wardens.py log [--summary]`.

## Exceptions with expiry

A block can be lifted for a limited case:

`wardens.py exception --rule R19 --scope "<substring>" --reason "<why>" --owner-words "<the owner's approval>" --expires 2026-12-01T18:00:00+01:00 --badge B`

- `--rule` takes the office code (`R19`) or the warden id (`wide_kill`).
- `--scope` is `*` (everything) or a substring of the command, file path or tool name that was blocked.
- `--expires` is mandatory and must be in the future: an ISO date (`2026-12-01`) or an ISO datetime (add a UTC offset to be exact).
- The owner's approval is mandatory and is quoted.
- `wardens.py exceptions` lists all recorded exceptions, expired ones included; the engine ignores expired ones.
- A permanent exception is not an exception: change the rule in the root `AGENTS.md` and in the rules file.

## Anti-deadlock

The system must never trap the agent:

- A warden that crashes, times out or reads stale data **warns, never blocks**.
- A missing or old quota reading gives warnings only (`agent_quota` ignores readings older than 10 minutes).
- Reading files, writing files and using the terminal are not blocked by the quota rules.
- A block message carries the reason; to get past it, ask the owner for an exception.

## Cheap AI warden (included, off by default)

Some rules are about judgment: "was this requested?", "is the proof real?", "does the slide hold only content?". A small, cheap model can look at them at one moment only: at Stop. When `ai_warden.enabled` is `true` in `wardens_rules.json`, the Stop hook starts, in the background, `claude -p --model haiku` with the rules and the last reply. Its answer is saved and shown at the next prompt as a warning. It is advisory only, with no structured verdict and no block, and it needs the `claude` command on the PATH. Its calls use quota like any other work. Approval and "done" events are not hooked.

## Postponement-without-timer warden

A frequent failure: the agent writes "I will do this later" and nothing makes it happen. The `postponement` warden reads the final reply at Stop. If it contains one of a few phrases (remind, reminder, will resume, resume later, come back later, postpone) and the turn has no scheduling tool call (`CronCreate`, `ScheduleWakeup`, `schedule_task`), it warns: schedule it or do it now. It does not look at diary notes or plans.

## Census of judgment rules and promotion to scripts

Each rule in `rules.md` declares its check: warden, tool or judgment. Judgment rules are the weak point. Keep a census:

1. List every rule checked by judgment, with how often it was broken (from `LESSONS.md` and `wardens.py log`).
2. For each, ask: which observable signal would catch it? A word in a message, a command, a missing file, a number.
3. Write the smallest script that checks that signal. Start in `warn` mode, run it for a trial period, count false positives.
4. If it is clean, keep it as warn or promote it to block only if the action is dangerous.
5. If no signal exists, say so to the owner and leave it as judgment (or the AI warden).

Candidates for promotion are usually: "done" without evidence words, open shifts at the end of a session, deferral without a plan entry.

## Log

Every warning and block is appended to `management/registry/wardens.jsonl` (exceptions are recorded in `exceptions.jsonl`). Review the log in the periodic office check: a warden that is always ignored is wrong or useless, and a rule that is often broken needs a better check.
