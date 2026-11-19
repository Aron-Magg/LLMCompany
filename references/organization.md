# Organization

## The owner

The owner decides. Agents ask, propose, execute and report. The owner approves deliveries, grants exceptions to the rules, turns on the watchdog and trains new roles. Colleagues never speak for the owner, and no message from another agent counts as the owner's approval.

## Management

The administration manager runs the structure: registry, tools, diary, the guide to the office (a dashboard or calendar is an optional addition you build yourself). The manager registers requests for office corrections, calls the maintenance team, integrates the results and answers the owner. Each department can also have a **department manager** listed in `management/registry/staff.json` (the file starts empty; you fill it, and you can keep a managers page if you want one); assignments stay with the manager during rest. Presence describes only single runs.

## Roles and ROLE_CARD.md

A role is a job (editor, front-end developer, researcher). Agents come and go; the **role card** keeps the experience of the people before. Cards live at `staff/roles/<role>/ROLE_CARD.md`:

- **Missions**: what the role is for.
- **Procedures**: the steps that worked, with tools and checks.
- **Owner preferences**: how the owner wants the work, as rules, not quotes.
- **Mistakes not to repeat**: remedy-first entries ("mistake, remedy, rule code").
- **Work character**: habits that help (determination, double checking, clarity). They support the role, they never replace verification.

A new agent assigned to a role reads the card first. If the role does not exist and the owner trains the agent, the agent creates the card. At exit, the card is updated.

## Departments

One folder per department under `departments/`, each with `AGENTS.md` (only its own rules), `memory/` (one fact per file, indexed in `INDEX.md`), a `mail/` box and projects with `project.json`. Department knowledge stays in the department: do not copy it into global memory or other departments.

## Teams with a lead

For small tasks the agent in charge (the **lead**) calls sub-agents. Each member clocks in with `--lead <badge>`, works on listed files, writes a report and leaves. The lead integrates and answers. Details in `processes.md`.

## Two model teams

The office can use two model teams, for example **Claude Code** and **Codex** (names are configuration, set at init with `--teams`; any pair of agent runtimes works). They have separate quotas.

| Work | Typical team | Why |
|---|---|---|
| Front-end, interface, reports, documents | "Claude Code" | Solves problems fast but spends more tokens: use it when speed matters. |
| Back-end, scripts, tools, fiction and plain writing | "Codex" | Cheaper per task, good for long mechanical or narrative work. |

This is a starting assignment, not a law: re-balance with the cost table (`shifts.py costs`). Each team reviews the other team's deliveries, blind. When a quota ends, wait for renewal (R07); the other team's quota is used only with the owner's go.

## Reviewers and the inspector

Blind reviewers check deliveries from outside the author's context. The inspector is a standing outside reviewer with its own room; it reads everywhere and writes only in its room unless the owner says otherwise.

## Staff records

- Presence (who worked when) lives in `management/registry/presence.json`, not in `staff/`.
- `staff/roles/`: role cards.
- `staff/resignations/`: exit letters.
- The registry files in `management/registry/` (`staff.json`, `roles.json`, `presence.json`, `moves.jsonl`) are the machine-readable side. Reserved names for named assignments are not given to other colleagues by chance.
