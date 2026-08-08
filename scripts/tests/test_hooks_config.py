import json
import os
import sys
import unittest

# Ensure the scripts module directory is in sys.path
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


class TestHooksConfig(unittest.TestCase):
    def test_hooks_json_relative_paths(self):
        """Verify that hooks.json contains only relative paths for python scripts and no absolute drive letters or /Users/ paths."""
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
                cmd.startswith(("python scripts/", "python scripts\\")),
                f"Command '{cmd}' should start with relative path 'python scripts/'"
            )

    def test_setup_utf8_streams(self):
        """Verify setup_utf8_streams() runs without exception on standard sys.stdin, sys.stdout, sys.stderr."""
        from hooks.utils import setup_utf8_streams
        setup_utf8_streams()


if __name__ == "__main__":
    unittest.main()
