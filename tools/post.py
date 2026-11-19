#!/usr/bin/env python3
"""Manage per-room mailboxes in an agent office."""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:40] or "message"


def metadata(path):
    text = path.read_text(encoding="utf-8")
    parts = text.split("---\n", 2)
    if len(parts) != 3 or parts[0] != "":
        raise ValueError(f"Invalid message: {path}")
    return {k: json.loads(v) for k, v in (line.split(": ", 1) for line in parts[1].splitlines())}, parts[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="Office root (default: AGENT_OFFICE_ROOT or current directory)")
    commands = parser.add_subparsers(dest="command", required=True)
    write = commands.add_parser("write", help="Write a message to a room mailbox")
    write.add_argument("--to", required=True, help="Recipient room ID")
    write.add_argument("--from", dest="sender", required=True, help="Sender name or badge")
    write.add_argument("--type", choices=("request", "reply", "note"), required=True, help="Message type")
    write.add_argument("--subject", required=True, help="Message subject")
    write.add_argument("--body", required=True, help="Message body")
    write.add_argument("--reply-to", help="Path to an existing message, relative to the office root")
    write.add_argument("--instructions", action="store_true", help="Mark this message as instructions")
    read = commands.add_parser("read", help="List messages in a room mailbox")
    read.add_argument("--mailbox", required=True, help="Room ID whose messages to list")
    read.add_argument("--new", action="store_true", help="Show unread messages, including closed notes")
    read.add_argument("--reader", help="Reader badge, required with --new")
    read.add_argument("--open", action="store_true", help="Show only open requests")
    close = commands.add_parser("close", help="Close a message in a registered mailbox")
    close.add_argument("file", help="Message path, relative to the office root")
    close.add_argument("--by", required=True, help="Badge closing the message")
    close.add_argument("--note", help="Optional closing note")
    commands.add_parser("hook", help="Report unread mail for the current badge")
    args = parser.parse_args()
    if args.command == "read" and args.new and not args.reader:
        parser.error("read --new requires --reader")
    payload = json.load(sys.stdin) if args.command == "hook" else {}
    root = Path(args.root or os.environ.get("AGENT_OFFICE_ROOT") or payload.get("cwd") or ".").resolve()
    if not args.root and not os.environ.get("AGENT_OFFICE_ROOT"):
        root = next((p for p in (root, *root.parents) if (p / "management/registry/rooms.json").exists()), root)
    registry = root / "management/registry"
    try:
        if not (registry / "rooms.json").exists():
            raise ValueError("rooms.json not found; use --root or AGENT_OFFICE_ROOT to select the office")
        rooms = json.loads((registry / "rooms.json").read_text(encoding="utf-8"))["rooms"]
        mailboxes = {}
        for room in rooms:
            path = (root / room["path"] / "mail").resolve()
            if not path.is_relative_to(root):
                raise ValueError("Room path must stay inside the office root")
            mailboxes[room["id"]] = path

        def message_path(value):
            path = (root / value).resolve()
            if path.suffix != ".md" or path.parent not in mailboxes.values() or not path.is_file():
                raise ValueError(f"Message not found in a registered mailbox: {value}")
            return path

        if args.command == "write":
            if args.to not in mailboxes:
                raise ValueError(f"Unknown room: {args.to}")
            reply_to = str(message_path(args.reply_to).relative_to(root)) if args.reply_to else ""
            now = datetime.now()
            box = mailboxes[args.to]
            box.mkdir(parents=True, exist_ok=True)
            name = f"{now:%Y-%m-%d_%H%M}_{slug(args.sender)}_{slug(args.subject)}"
            data = {"type": args.type, "from": args.sender, "to": args.to, "subject": args.subject,
                    "status": "open" if args.type == "request" else "closed", "date": now.date().isoformat(),
                    "reply_to": reply_to, "instructions": args.instructions}
            content = "---\n" + "".join(f"{k}: {json.dumps(v, ensure_ascii=False)}\n" for k, v in data.items()) + "---\n" + args.body + "\n"
            index = 1
            while True:
                path = box / (name + (f"_{index}" if index > 1 else "") + ".md")
                try:
                    with path.open("x", encoding="utf-8") as stream:
                        stream.write(content)
                    break
                except FileExistsError:
                    index += 1
            print(path.relative_to(root))
        elif args.command == "read":
            if args.mailbox not in mailboxes:
                raise ValueError(f"Unknown room: {args.mailbox}")
            state_file = registry / "mail_read.json"
            state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
            key = json.dumps([args.reader, args.mailbox])
            seen = set(state.get(key, [])) if args.new else set()
            displayed = []
            for path in sorted(mailboxes[args.mailbox].glob("*.md")):
                meta, body = metadata(path)
                if path.name in seen or (args.open and not (meta.get("type") == "request" and meta.get("status") == "open")):
                    continue
                print(f"[{meta['status']}] {meta['type']} from {meta['from']}: {meta['subject']}\n{path.relative_to(root)}\n{body}")
                displayed.append(path.name)
            if not displayed:
                print("No messages found.")
            if args.new:
                state[key] = sorted(seen.union(displayed))
                registry.mkdir(parents=True, exist_ok=True)
                state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        elif args.command == "hook":
            badge = payload.get("badge") or payload.get("session_id", "")
            state_file = registry / "mail_read.json"
            state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
            count = sum(1 for room, box in mailboxes.items() for path in box.glob("*.md") if path.name not in state.get(json.dumps([badge, room]), [])) if badge else 0
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": f"Unread mail: {count}"}}))
        else:
            path = message_path(args.file)
            meta, body = metadata(path)
            meta.update(status="closed", closed_by=args.by)
            if args.note:
                meta["close_note"] = args.note
            path.write_text("---\n" + "".join(f"{k}: {json.dumps(v, ensure_ascii=False)}\n" for k, v in meta.items()) + "---\n" + body, encoding="utf-8")
            print(f"Closed: {path.relative_to(root)}")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 0 if args.command == "hook" else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
