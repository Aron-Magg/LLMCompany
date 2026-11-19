# The 30 office rules (generic)

These are the root rules. They are written once, in the root `AGENTS.md`. Departments, role cards and lessons point to them by code. Each rule has: the rule, exceptions, how it is checked (a warden, a tool, or "judgment") and one typical agent mistake. A temporary exception is recorded with `wardens.py exception` (rule, scope, reason, owner's words, expiry date or time). "Check" names the warden id from `wardens_rules.json` (`wardens.py rules`); a rule marked "judgment" has no script behind it. The AI warden is an optional advisory check, off by default (see `wardens.md`). A permanent exception becomes a change of the rule.

## People, language, names

**R01 Brand spelling.** The brand name is always written in one exact form (placeholder `{{BRAND}}`). *Exceptions:* a typographic variant the owner approves in a named file. *Check:* judgment. *Mistake:* writing the brand in a different case or split into two words.

**R02 Language and time.** Talk to the owner in `{{LANGUAGE}}`. Times use the 24-hour clock in the owner's timezone, read from `date` before writing them (also in file names). No native time fields in interfaces. *Exceptions:* none. *Check:* warden `time` (warn: a clock time in the final reply with no `date` command in the turn); the language part is judgment. *Mistake:* writing "around 3 pm" from memory.

**R03 Names in English.** New files and folders have English names, the content uses the owner's language. External products keep their English names everywhere. *Exceptions:* names the owner gives explicitly. *Check:* warden `file_name` (warn, checks new file names against a configurable word list). *Mistake:* naming a new file in the owner's language instead of English.

## Git and approvals

**R04 Commit on every approval.** On an explicit yes from the owner, commit at once, message `Approved: <what>`. Heavy binaries are copied with an `_approved` suffix and hashed (SHA-256 in `approvals.jsonl`). *Exceptions:* none. *Check:* judgment. *Mistake:* treating a "looks nice" as an approval, or forgetting to commit after a real yes.

**R05 Commit by path, no push.** Several agents share the index: `git add <files> && git commit -m "..." -- <files>`. Push, destructive reset and history rewrite only on the owner's request. Look at output size (`du`) before committing script output. *Exceptions:* none. *Check:* wardens `commit_paths` (warn), `git_push` (block). *Mistake:* `git add -A` that sweeps in another agent's half-finished files.

## Credit, quotas, long jobs

**R06 Credit.** Before any assignment or resume: an estimate told to the owner. Every sentence about credit gives the reading with its time; if not read, say "not checked". Thresholds on the session window (trial 65/80/90, then 70/85/95). The brake covers new assignments only; a stale reading or a broken warden gives warnings only; confirmed exhaustion stops new hires; reading, writing and the terminal stay allowed. State is written after each step of a long job. *Exceptions:* the owner's go above 80%. *Check:* wardens `credit` (warn: credit claim without a `shifts.py` call), `agent_estimate` (warn: agent launched with no estimate in the last 30 minutes), `agent_quota` (block: agent launched while a fresh reading is above 80% used). The other thresholds are guidance read with `wardens.py thresholds`. *Mistake:* "we have plenty of budget" with no reading.

**R07 Quota finished.** Wait for the renewal with the same team and leave a resume reminder. Use the other team's quota only with the owner's go. No new chat or process to dodge a limit. If credit is not enough to finish, the owner may hand over to another agent with a written handover. *Exceptions:* none. *Check:* warden `postponement` (warn: a deferral in the final reply with no scheduling tool call in the turn); the rest is judgment. *Mistake:* silently starting the same job in the other team.

**R08 Estimate before long jobs.** Measure a probe, compute the duration, tell the owner, then run; at the end log the result. Long jobs are resumable: checkpoints, no overwrite, clean stop, explicit resume. *Exceptions:* none. *Check:* judgment. *Mistake:* starting an hour-long encode with "it should be quick".

**R09 CPU under 70%.** Every long job goes through `cpu_cap.py -- <command>` (total cap 0.70, own share lower, resume and calm levels). One heavy analysis at a time. Before heavy disk writes, and at each stage, check free space; stop below a fixed floor (for example 8 GB). While a render runs, the desktop counts too. *Exceptions:* a boost profile only as a recorded exception with expiry. *Check:* warden `long_job` (warn: `blender`, `ffmpeg` or `zip` without `cpu_cap.py`). *Mistake:* running a build in parallel with a render.

## How we work

**R10 Concept first.** Every visual job starts with labeled low-quality variants; wait for the owner's choice, one choice at a time, with questions free of jargon. For documents: agree purpose and structure, make a sample chapter, have a blind reader check it, and only then the final form. No cycles of patches. *Exceptions:* none. *Check:* judgment (optional AI warden). *Mistake:* delivering a finished design when only a sketch was requested.

**R11 Versions.** Preview images already shown are never overwritten (new name with a version suffix). Numbered documents, presentations and reports to the owner are fixed in the same file (git keeps history). CAD sources use `_Vn`. *Exceptions:* none. *Check:* judgment. *Mistake:* overwriting `preview.png` so the owner's cache shows the old one.

**R12 Measure, don't estimate by eye.** Similarities, quotas, times and defects are measured on the real files. If it cannot be measured, say so. Look at images at full size; test with the real originals, not retouched copies. *Exceptions:* none. *Check:* judgment. *Mistake:* "about 90% similar" from a glance.

**R13 No invented data.** No invented facts, organizations, prices or people. Estimates and hypotheses are labeled. If data is missing, ask. No placeholders in delivered material; every figure says whose it is and whether it is measured, computed or estimated. A proposal under discussion is not a decision. *Exceptions:* none. *Check:* judgment. *Mistake:* filling a table with plausible prices.

**R14 "Done" only with proof.** "Done", "ready", "verified" only with the proof described: what was checked, how, what was not checked. A defect not reproduced is not a defect fixed. Reproduce first, fix in the source (not the copy), list what is missing, re-read all the owner's requests before delivery. *Exceptions:* none. *Check:* judgment (optional AI warden). *Mistake:* "fixed" after editing the symptom, not the cause.

**R15 Another colleague reviews.** Each delivery is checked first by a colleague who did not make it and has no context (for documents: every page as an image). *Exceptions:* none. *Check:* judgment. *Mistake:* the author reviews their own work.

**R16 Ask or apply.** An explicit instruction is applied. An idea or description is discussed, not produced. A doubt about direction is asked at once, before starting; a doubt of detail is decided, noted and brought to the final review. No unrequested initiatives. Never agree with the owner when they are wrong: say so with facts; if they then say "do it anyway", do it. After two failed checks on one job, return to the owner. When the owner says "redo", redo, no patch. External repositories are downloaded outside the office, read only; nothing is installed before the owner's choice. *Exceptions:* none. *Check:* judgment (optional AI warden). *Mistake:* "improving" a file nobody asked to touch.

**R17 No commentary text on visuals.** Slides and graphics hold content only: no legends about the process, no "still open", no text outside its area. Little text; one color has one meaning; internal cautions go into internal documents and speaker notes. *Exceptions:* none. *Check:* judgment (optional AI warden). *Mistake:* a "draft - to be checked" ribbon on a delivered slide.

## The owner's machine

**R18 Services and ports.** Do not stop the owner's running services or the dashboard. If one must move or restart, restart it at once with the service script. *Exceptions:* none. *Check:* warden `ports` (block, for the ports listed in `protected_ports`). *Mistake:* freeing a port by killing whatever listens on it.

**R19 Processes and windows.** No wide `pkill`/`killall`: close by PID what you opened and verify with `ps`. No windows, full screen, simulated mouse or keyboard on the owner's screen (browsers only headless) unless a recorded exception with expiry exists, even if the owner asks. When something must be clicked in an app, the agent does it (headless browser or recorded exception); never ask the owner. *Check:* warden `wide_kill` (block); windows: judgment. *Mistake:* `pkill node` that closes the owner's dev server.

**R20 App opened by the owner.** Do not change files of an app the owner has open (auto-reload, plan or server in use). *Exceptions:* none. *Check:* judgment. *Mistake:* editing the page the owner is previewing.

**R21 Protected originals.** Delivered originals marked as protected are never written, moved, archived or deleted. Their hash is recorded. *Exceptions:* none. *Check:* warden `protected_folder` (block, for the folders listed in `protected_folders`; hash recording is manual). *Mistake:* "cleaning up" a source folder that holds the original delivery.

**R22 Secrets.** Secrets live only in `secrets/` folders outside git: never in chat, commits or the dashboard. *Exceptions:* none. *Check:* warden `secrets` (block). *Mistake:* pasting a token in a commit message.

**R23 No orders or sends without the owner.** Nothing is ordered, printed or produced, and no message leaves the office (suppliers, customers, partners), without the owner's check. Drafts are not sends. Copies for outsiders have no comments, reminders or internal apparatus; internal information is not commented on. *Exceptions:* none. *Check:* judgment. *Mistake:* sending a "quick confirmation" mail.

## Office

**R24 Plan.** If a plan exists, work in its order and scope. Propose any deviation first; if approved, write it into the plan. *Exceptions:* none. *Check:* judgment. *Mistake:* skipping a step because it "looks unnecessary".

**R25 Log what the owner says at once.** Every correction or instruction is written when it arrives: the owner's words, the mistake, the rule, the place where it applies, in the nearest `LESSONS.md` and in the "mistakes not to repeat" of the roles touched. A rule broken twice becomes an automatic warden, or the owner is told why it cannot. *Exceptions:* none. *Check:* judgment. *Mistake:* promising to remember and writing nothing.

**R26 Badge and team.** Badge and name come from the clock-in; introduce yourself with that name; one open shift per person; whoever finishes clocks out or rests. Team members clock in with `--lead`, hand in a report and leave without a resignation letter. *Exceptions:* none. *Check:* tool. *Mistake:* leaving shifts open after the chat ends.

**R27 Mail and canteen.** Requests, answers and targeted notes go into the addressee's mailbox; mail is read with `--new --reader <badge>` (notes included). The canteen holds general messages only. *Exceptions:* none. *Check:* tool. *Mistake:* posting a task for one person in the canteen.

**R28 Library first.** Before looking for knowledge elsewhere, ask the library; if it is not there, search and add the entry. Before redoing something, look for approved figures, renders, research and estimates. In research, see first how professionals do it, one source per item; "not found" or "in conflict" only after hunting for the primary source, and a conflict is explained, not listed. *Exceptions:* none. *Check:* judgment. *Mistake:* repeating a study the library already holds.

**R29 Exchange.** `exchange/out/` holds copies only (they expire after a fixed period, 7 days by default); `in/` is taken in charge and left empty. No rules file points inside `out/`. *Exceptions:* a written exception with a reason. *Check:* judgment (no expiry timer is shipped; the 7 days are a default you can change, see `architecture.md`). *Mistake:* leaving the only copy of a file in `out/`.

**R30 No code-graph tools in the office** (example of an owner's preference rule; replace or delete). Reason: token cost. For orientation use the library, the catalog and the department paths. *Exceptions:* none. *Check:* judgment. *Mistake:* indexing the whole repository "to get oriented".
