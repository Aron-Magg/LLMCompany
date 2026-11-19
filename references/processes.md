# Processes of the agent office

Every process leaves a written trace. A new chat must be able to resume from files alone.

## 1. Entering the office

1. Read the root `README.md` and every `AGENTS.md` from the root down to the folder you will work in.
2. A hook at session start clocks you in and gives you a **badge**. The hook picks a first name from a short list (Alex, Sam, …), records the room from the working folder and leaves the task empty. Introduce yourself with the name the hook gives you, unless the owner assigns another. Agents without hooks clock in by hand: `office.py in --name N --room R --task T`.
3. Declare the real task straight away: `office.py task --badge B --task "<what>"`. Room changes are logged by the hook only for tool events it understands; otherwise move by hand with `office.py move --badge B --room R`.
4. If the owner gives you a role that has a `ROLE_CARD.md`, read it (see `organization.md`). If the role does not exist and the owner trains you, create the card.
5. Ask the library first: `library.py search "<question>"`. If you find it, go straight to the source. If not, search elsewhere and then add an entry.
6. Read your mailbox: `post.py read --mailbox <room> --new --reader <badge>` (notes included), then `--open` for requests still to do.
7. Check the quotas before any big job (section 4).

One person has one open shift. Whoever finishes clocks out (`office.py out --badge B --report FILE` for team members, `--resignation FILE` for the others) or rests (`office.py rest --badge B`). Abandoned shifts are closed by management with one collective note.

## 2. Rest and exit

- `office.py rest --badge B`: you stop but keep your assignment. The record describes only single runs, not the assignment.
- `office.py out --badge B --report FILE`: team members (clocked in with `--lead`) leave with a short report, no resignation letter. Team members must use `--report`; the tool refuses a resignation from them.
- `office.py out --badge B --resignation FILE`: a full exit for everyone else, see section 12. The tool records the letter path in `presence.json`; you write the letter in `staff/resignations/` yourself.
- Presence (shifts) is stored in `management/registry/presence.json`, moves in `moves.jsonl`, and the session-to-badge map in `sessions.json`.

## 3. Teams with a lead

An agent may call a **team** of sub-agents for smaller tasks.

- Each member clocks in with `--lead <badge of the lead>`.
- Each member works only on the given files, writes a short report (what was done, how it was checked, what is missing) and clocks out with `office.py out --badge B --report FILE`.
- The lead merges the reports and answers the owner. Members never answer the owner directly.
- Give members explicit assignments and file lists. Check the quotas before starting or resuming them.
- When the project is done the lead leaves too.

## 4. Shifts and quotas

Each model team (for example "Claude Code" and "Codex", configurable) has a usage budget with windows, for example a 5-hour session and a weekly window. A small adapter writes them into `management/registry/quotas.json`:

```json
{"teams": {"claude": {"windows": [{"name": "session", "used_pct": 40, "resets_at": "ISO", "read_at": "ISO"}]}}}
```

The key is `resets_at` (not `reset_at`: a misspelled key makes the reset show as unknown). `tools/adapters/quota_from_ccusage.py` is an example adapter.

- `shifts.py status` prints every window with its reset time and the time of the reading.
- `shifts.py check --team TEAM` exits with 75 only when a window is confirmed at 100%. It launches or blocks nothing: whoever starts an agent (a person, a script, the watchdog) must honor the exit code.
- Thresholds on the session window, in trial: warn at **65%**, no new assignment above **80%** without the owner's go, above **90%** only closing and delivery. After ten successful trial runs they become 70/85/95.
- The brake applies only to **new assignments** (agents started or resumed). Enforcement is partial: the `agent_quota` warden blocks launching an agent when any team's fresh reading is above 80%; the other levels are guidance. The owner lifts the block with a recorded exception (`wardens.py exception`).
- **Anti-deadlock**: a stale, missing or broken reading gives warnings only. A confirmed exhausted quota stops new assignments (`shifts.py check` exits 75 and callers must stop); reading, writing and the terminal stay allowed so the work can always be saved.
- Every sentence about credit states the reading and its time ("16:02, session 36%"). If you did not read it, write "not checked". Tokens consumed and quota left are different things. Never invent a ceiling.
- When a quota ends: wait for the renewal with the same team and leave a resume reminder. Use the other team only with the owner's go. Never open a new chat or process to dodge a limit.
- After each step of a long job, write the resume state (diary or room), so a limit loses nothing.

## 5. Estimate before, actuals after

Before every assignment or resume:

`shifts.py estimate --badge B --task T --team TEAM --cost "<estimate>" --done-when "<closing point>"`

The tool reads the quotas itself and records in `estimates.jsonl`: task, team, quota with time of reading, estimated cost, closing point. `shifts.py costs` may print nothing until some actuals have points. Tell the owner the estimate before work starts.

After the work: `shifts.py actuals --id ID [--kind KIND]` records what it really used. `shifts.py costs` prints a cost table by kind of task, so the next estimate starts from measured data instead of a guess.

For long jobs (render, encode, archive, heavy build): measure a probe, compute the duration, tell the owner ("starts now, about 25 min, ends around 15:40"), run it under the CPU cap (`cpu_cap.py -- <command>`), make it resumable (one file per step, no overwrite, clean stop after the current step, explicit resume that reuses what exists), and leave nothing running when you suspend.

## 6. Approvals

- When the owner approves something with an explicit yes, commit at once in the repo that holds the work: `Approved: <what>`.
- Heavy binaries (models, renders, videos) are not committed. Copy the file with an `_approved` suffix (never overwrite) and record it: `office.py approve --badge B --what "..." --file PATH [--commit SHA]`. This writes the SHA-256 into `approvals.jsonl`. Then commit the registry.
- Commit by path: `git add <files> && git commit -m "..." -- <files>`. Several agents share the index, so never `git add -A` on a folder. Push only when the owner asks.

## 7. Lessons log and the "violated twice" rule

- Every correction or instruction from the owner is written at once in the `LESSONS.md` next to the work: the owner's words, the mistake, the rule, where it applies. End the entry with the rule code ("see R09").
- Add it also to "Mistakes not to repeat" in the role cards touched.
- Whoever enters a project reads its `LESSONS.md` and cites it in assignments.
- A rule broken **twice** becomes an automatic warden (see `wardens.md`), or you tell the owner why it cannot be automated.
- In this package, lessons are shared as "mistake, remedy" pairs (see `lessons.md`).

## 8. Handovers and diaries

- Each room or role keeps a `DIARY.md` of working notes: what was done, what is next, what is blocked. Management's diary is `management/DIARY.md`.
- A handover between agents is a written note with: goal, state, files, decisions with their source, open questions. Put it in the recipient's mailbox.
- A resume point is a file, not a memory. If it is not written it does not exist.

## 9. Blind reviews by the other team

Every delivery to the owner is checked first by a colleague who did not make it and who receives no context from the author. For documents, look at each page as an image. For code, run the full suite and read the diff. For data, recompute a sample.

The reviewer writes findings with evidence. The author fixes at the source (not in the copy). After two failed reviews on the same work, go back to the owner.

## 10. Workshop: request, build, test, delivery

When a department needs a new tool or a repair, it asks the IT/workshop department:

1. **Request** in the workshop mailbox: need, who uses it, example input and output.
2. **Build** in the workshop folder, reusing what exists. Small steps, tests first when possible.
3. **Test** by a different colleague, with real data, not toy data.
4. **Delivery** to the requesting department, with a short usage note. The tool is added to the library catalog.

Nothing is installed from outside before the owner chooses: external repositories are downloaded outside the office, read only, and conclusions are proposals.

## 11. Maintenance team and fixes to the office itself

When the owner asks to correct the office (a rule, a tool, a registry), the manager logs the request and calls the maintenance team:

- **Coordinator**: scopes the request, splits the work, decides the order.
- **Implementer**: changes tools or files, small commits by path.
- **Tester**: reproduces the defect first, then checks the fix with the full test suite.

The manager merges the result and answers the owner. A defect not reproduced is not a defect fixed.

## 12. The "fired" procedure

The owner can end an agent's engagement with a command (for example `/fired`). The agent then:

1. Writes the resignation letter in `staff/resignations/`: what was done, what is open, what the next person must know.
2. Updates the role card (new "mistakes not to repeat"), the department memory, the project status file and the library catalog.
3. Checks that nothing conflicts with existing notes.
4. Clocks out (`office.py out --badge B --resignation FILE`; a team member uses `--report FILE` instead) and commits by path.

The owner then deletes the chat. Only what is written counts.

## 13. Exchange: in and out, with expiry

- `exchange/in/`: the owner drops material. The office looks at it, moves it to the right room, adds knowledge to the library, logs it in `exchange/RECEIPTS.md` (created by `init.py`; what, from where, where it went). The folder ends empty.
- `exchange/out/`: copies only. The original stays in its room. Copies expire after a fixed period (7 days by default, a rule for agents; the package ships no expiry timer, see `architecture.md`). A written exception with a reason keeps an item longer.

## 14. Closing a project

Set `status: closed` and `closed_on` in `project.json`, fill the milestones with real dates, and let management update the statistics.
