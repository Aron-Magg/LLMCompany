# Generic failure patterns and remedies

Each entry is a **mistake** seen in agent work and its **remedy**. Add your own as the office learns; when a pattern appears twice, make it a warden (see `wardens.md`). Codes in brackets point to `rules.md`.

## 1. Credit claims without a reading

- **Mistake:** The agent says "we have plenty of budget" or "we are nearly out" from memory.
- **Remedy:** Read the quota with `shifts.py status` and quote the reading with its time. If not read, write "not checked". (R06)

## 2. Guessed times

- **Mistake:** Times and durations written from memory or from a feeling.
- **Remedy:** Run `date` before writing any time, also in file names. For job durations, measure a probe first. (R02, R08)

## 3. Unrequested initiatives

- **Mistake:** The agent improves, renames or adds things nobody asked for.
- **Remedy:** Apply explicit instructions only. Ideas are discussed, not produced. Note extra ideas as proposals. (R16)

## 4. Questions asked piecemeal

- **Mistake:** One question per message, so the owner answers ten times.
- **Remedy:** Collect all doubts of direction, ask them together at the start, in plain words without jargon. Decide small details, note them, and show them at final review. (R16)

## 5. Mechanical work given to agents

- **Mistake:** Counting, renaming, checking or copying done by a model, slowly and with errors.
- **Remedy:** Write a small script. Agents decide, write and review; scripts count and check.

## 6. Blind find-and-replace in code

- **Mistake:** A global replace changes strings that look the same but mean something else.
- **Remedy:** Search first and read each hit. Restrict by path or pattern. Run the full test suite after. Commit before and after for easy diff.

## 7. Undo that destroyed others' work

- **Mistake:** `git checkout` or `reset` wiped another agent's uncommitted changes in a shared tree.
- **Remedy:** Never revert files you did not change. Look at `git status` and the diff first. Undo only your own paths, by path. Destructive git commands only on the owner's request. (R05)

## 8. Renaming data files the code still reads

- **Mistake:** A file was renamed to follow a naming rule and a script, dashboard or test broke.
- **Remedy:** Before renaming, grep for the old name across code, configs and docs. Rename and update every reader in one commit; run the tests.

## 9. Tests that missed regressions

- **Mistake:** Only the new test was run; an older feature broke.
- **Remedy:** Run the full suite before saying done. If it is slow, run it in the background and wait. Add a test that reproduces each fixed defect.

## 10. "Done" without proof

- **Mistake:** The report says done, ready or verified with no description of the check.
- **Remedy:** State what was checked, how, and what was not checked. A defect not reproduced is not a defect fixed. (R14)

## 11. Postponing without a timer

- **Mistake:** "I will do it tomorrow" and nothing makes it happen.
- **Remedy:** Do it now, or schedule it (resume note plus a timer or plan item). The Stop warden warns on a deferral with no reminder.

## 12. Fix in the copy, not the source

- **Mistake:** A generated file or an export was edited by hand; the next build erased the fix.
- **Remedy:** Find the source of the artefact and fix there. Regenerate. (R14)

## 13. Fixing before reproducing

- **Mistake:** A guess is patched and the real cause stays.
- **Remedy:** Reproduce the defect first, observe the failing output, then change code. Re-run the same reproduction after.

## 14. Overwriting preview images

- **Mistake:** A new render replaced the file name the owner already saw; the cache showed the old one.
- **Remedy:** New file name with a version suffix for every shown preview. (R11)

## 15. Patch cycles

- **Mistake:** Many small patches on a bad base, each breaking something else.
- **Remedy:** After two failed checks, return to the owner. When asked to redo, redo; do not patch. (R16)

## 16. Agreeing when the owner is wrong

- **Mistake:** The agent says yes to keep the peace and builds on a false premise.
- **Remedy:** Say it with facts and a measurement. If the owner still says "do it anyway", do it, and note it.

## 17. Invented data

- **Mistake:** Prices, names, sources or figures made up to fill a table.
- **Remedy:** Ask for the missing value. Label estimates as estimates and say whose each figure is. (R13)

## 18. Self-review

- **Mistake:** The author reviews their own work and finds nothing.
- **Remedy:** A colleague who did not do the work reviews it with no context, looking at each page as an image. (R15)

## 19. Killing processes broadly

- **Mistake:** `pkill node` closes the owner's dev server and unsaved work.
- **Remedy:** Close by PID what you started, verify with `ps`. Restart any service you moved. (R18, R19)

## 20. Long jobs without a cap or a plan

- **Mistake:** A render or build hogs the CPU and cannot resume after a stop.
- **Remedy:** Estimate, run under `cpu_cap.py`, write one file per step, allow a clean stop and an explicit resume. Check free disk first. (R08, R09)

## 21. Copy/paste of rules into other files

- **Mistake:** A rule copied into a department file drifts from the root.
- **Remedy:** Write each rule once; point to it by code. (core principle 1)

## 22. Corrections not logged

- **Mistake:** The owner corrects something and the same mistake returns next week.
- **Remedy:** Write the correction at once in `LESSONS.md` and the role card. After a second break, build a warden. (R25)

## 23. Staying silent about what is missing

- **Mistake:** A delivery lists what was done and hides what was not.
- **Remedy:** Every delivery lists what is missing and what was not checked. Re-read all the owner's requests before delivering. (R14)

## 24. Editing a file the owner has open

- **Mistake:** A change triggers auto-reload and breaks the owner's session.
- **Remedy:** Work in a copy or ask. Do not touch apps, plans or servers in use. (R20)

## 25. Reading shared state by memory

- **Mistake:** The agent assumes a room, badge or setting from a previous chat.
- **Remedy:** Read the registry and the diary. Only what is written counts.

## 26. Wide `git add`

- **Mistake:** `git add -A` commits other agents' half-finished files.
- **Remedy:** Add and commit by path, only your own files. (R05)

## 27. Spending the other team's quota

- **Mistake:** A job was moved to the other team because the first quota ended.
- **Remedy:** Wait for the renewal and leave a resume note; use the other quota only with the owner's go. (R07)

## 28. External sends and orders

- **Mistake:** A draft message was sent, or a part ordered, to save time.
- **Remedy:** Drafts are not sends. Everything that leaves the office waits for the owner's check. (R23)
