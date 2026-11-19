import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "post.py"


class PostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        registry = self.root / "management/registry"
        registry.mkdir(parents=True)
        (registry / "rooms.json").write_text(json.dumps({"rooms": [{"id": "lab", "path": "departments/lab"}]}))

    def run_cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stderr)
        return result

    def write(self, kind, subject, *extra):
        return self.run_cli("write", "--to", "lab", "--from", "agent", "--type", kind, "--subject", subject, "--body", "hello", *extra).stdout.strip()

    def test_new_open_close_and_reply(self):
        request = self.write("request", "Request")
        note = self.write("note", "Note")
        new = self.run_cli("read", "--mailbox", "lab", "--new", "--reader", "reader").stdout
        self.assertIn("Request", new)
        self.assertIn("[closed] note", new)
        self.assertNotIn("Request", self.run_cli("read", "--mailbox", "lab", "--new", "--reader", "reader").stdout)
        opened = self.run_cli("read", "--mailbox", "lab", "--open").stdout
        self.assertIn("Request", opened)
        self.assertNotIn("Note", opened)
        reply = self.write("reply", "Reply", "--reply-to", request)
        self.assertIn(json.dumps(request), (self.root / reply).read_text())
        self.run_cli("close", request, "--by", "reader", "--note", "done")
        self.assertNotIn("Request", self.run_cli("read", "--mailbox", "lab", "--open").stdout)
        self.assertIn('closed_by: "reader"', (self.root / request).read_text())
        self.assertTrue((self.root / note).exists())
        self.assertIn("Reply", self.run_cli("read", "--mailbox", "lab", "--new", "--reader", "reader").stdout)

    def test_unknown_room(self):
        result = self.run_cli("read", "--mailbox", "missing", ok=False)
        self.assertIn("Unknown room", result.stderr)

    def test_filtered_new_does_not_consume_notes(self):
        self.write("note", "Note")
        self.run_cli("read", "--mailbox", "lab", "--new", "--reader", "reader", "--open")
        self.assertIn("Note", self.run_cli("read", "--mailbox", "lab", "--new", "--reader", "reader").stdout)


if __name__ == "__main__":
    unittest.main()
