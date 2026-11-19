# Exchange (level 1)

Adds to the root rules.

- `in/`: material from the owner. Process it: look, move to the right room, catalog if it is knowledge, log in `RECEIPTS.md`. Leave `in/` empty.
- `out/`: deliveries for the owner. Copies only; the original stays in its room. Items expire after 7 days by default (change the number in the root `AGENTS.md` if you want another period). No expiry timer is shipped: delete by hand, or add your own job that logs each deletion with its SHA-256 and never touches `in/`. An exception needs a written reason.
- No rules file points into `out/`.
