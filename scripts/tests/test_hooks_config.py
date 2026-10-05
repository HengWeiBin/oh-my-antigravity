import json
import os
import re
import sys
import unittest

# Ensure the scripts module directory is in sys.path
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


class TestHooksConfig(unittest.TestCase):
    def test_hooks_json_relative_paths(self):
        """Verify that hooks.json commands do not hardcode absolute drive letters or specific user home paths, but correctly use the cross-workspace safe pattern and target existing scripts."""
        root_dir = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
        hooks_json_path = os.path.join(root_dir, "hooks.json")
        self.assertTrue(os.path.isfile(hooks_json_path), f"hooks.json not found at {hooks_json_path}")

        with open(hooks_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        commands = []

        def extract_commands(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "command" and isinstance(v, str):
                        commands.append(v)
                    else:
                        extract_commands(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract_commands(item)

        extract_commands(data)
        self.assertGreater(len(commands), 0, "No commands found in hooks.json")

        for cmd in commands:
            self.assertNotRegex(cmd, r'^[a-zA-Z]:', f"Command '{cmd}' contains an absolute drive letter")
            self.assertNotIn("/Users/", cmd, f"Command '{cmd}' contains an absolute /Users/ path")
            self.assertNotIn("\\Users\\", cmd, f"Command '{cmd}' contains an absolute \\Users\\ path")
            self.assertTrue(
                cmd.startswith(("python %USERPROFILE%", "python -c ", "python scripts/", "python scripts\\")),
                f"Command '{cmd}' should use cross-workspace safe pattern or relative path"
            )
            if cmd.startswith("python -c "):
                self.assertIn("runpy.run_path", cmd, f"Command '{cmd}' should use runpy.run_path")
                self.assertIn("os.path.expanduser", cmd, f"Command '{cmd}' should use os.path.expanduser")

            match = re.search(r"scripts[/\\]([a-zA-Z0-9_]+\.py)", cmd)
            self.assertIsNotNone(match, f"Could not extract target script from command '{cmd}'")
            script_file = os.path.join(root_dir, "scripts", match.group(1))
            self.assertTrue(os.path.isfile(script_file), f"Target script does not exist: {script_file}")

    def test_setup_utf8_streams(self):
        """Verify setup_utf8_streams() runs without exception on standard sys.stdin, sys.stdout, sys.stderr."""
        from hooks.utils import setup_utf8_streams
        setup_utf8_streams()

    def test_stop_hook_configured(self):
        """Verify hooks.json contains Stop lifecycle hook invoking stop.py."""
        root_dir = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
        hooks_json_path = os.path.join(root_dir, "hooks.json")
        with open(hooks_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        hooks = data.get("hooks", {})
        self.assertIn("Stop", hooks)
        stop_entries = hooks["Stop"]
        self.assertIsInstance(stop_entries, list)
        self.assertEqual(len(stop_entries), 1)
        self.assertEqual(stop_entries[0].get("type"), "command")
        stop_cmd = stop_entries[0].get("command", "")
        self.assertIn("stop.py", stop_cmd)
        self.assertEqual(stop_entries[0].get("timeout"), 5)


if __name__ == "__main__":
    unittest.main()
