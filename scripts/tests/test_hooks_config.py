import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure the scripts module directory is in sys.path
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from setup_hooks import detect_python, render_hooks


def extract_commands(obj):
    commands = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "command" and isinstance(v, str):
                commands.append(v)
            else:
                commands.extend(extract_commands(v))
    elif isinstance(obj, list):
        for item in obj:
            commands.extend(extract_commands(item))
    return commands


class TestHooksConfig(unittest.TestCase):
    def test_hooks_template_json_exists_and_valid(self):
        """Verify hooks.template.json exists, is valid JSON, and contains placeholders and valid script targets."""
        template_path = os.path.join(ROOT_DIR, "hooks.template.json")
        self.assertTrue(os.path.isfile(template_path), f"hooks.template.json not found at {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("hooks", data, "hooks.template.json must have 'hooks' key")
        hooks = data["hooks"]

        for phase in ["SessionStart", "PreInvocation", "PreToolUse", "PostToolUse", "Stop"]:
            self.assertIn(phase, hooks, f"Missing lifecycle phase {phase} in hooks.template.json")

        commands = extract_commands(data)
        self.assertGreater(len(commands), 0, "No commands found in hooks.template.json")

        for cmd in commands:
            self.assertIn("{{PYTHON}}", cmd, f"Command '{cmd}' must contain '{{{{PYTHON}}}}' placeholder")
            self.assertIn("{{PLUGIN_DIR}}", cmd, f"Command '{cmd}' must contain '{{{{PLUGIN_DIR}}}}' placeholder")

            match = re.search(r"scripts[/\\]([a-zA-Z0-9_]+\.py)", cmd)
            self.assertIsNotNone(match, f"Could not extract target script from command '{cmd}'")
            script_file = os.path.join(ROOT_DIR, "scripts", match.group(1))
            self.assertTrue(os.path.isfile(script_file), f"Target script does not exist: {script_file}")

    def test_setup_hooks_renders_valid_config(self):
        """Verify setup_hooks.render_hooks generates valid hooks.json with substituted variables."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            template_path = os.path.join(ROOT_DIR, "hooks.template.json")
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            (tmp_path / "hooks.template.json").write_text(template_content, encoding="utf-8")

            custom_python = "python3"

            generated_path = render_hooks(
                plugin_dir=tmp_path,
                python_cmd=custom_python,
            )
            self.assertTrue(generated_path.is_file(), "Generated hooks.json must exist")

            with open(generated_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            commands = extract_commands(data)
            self.assertGreater(len(commands), 0)

            for cmd in commands:
                self.assertNotIn("{{PYTHON}}", cmd, f"Command '{cmd}' contains unrendered {{{{PYTHON}}}}")
                self.assertNotIn("{{PLUGIN_DIR}}", cmd, f"Command '{cmd}' contains unrendered {{{{PLUGIN_DIR}}}}")
                self.assertTrue(cmd.startswith(custom_python), f"Command '{cmd}' should start with custom python")

            # Test explicit plugin-dir argument
            custom_output = render_hooks(
                plugin_dir=tmp_path,
                python_cmd="python",
            )
            self.assertTrue(custom_output.is_file())

    def test_detect_python_runtime(self):
        """Verify detect_python detects a non-empty string for Python binary."""
        detected = detect_python()
        self.assertIsInstance(detected, str)
        self.assertTrue(len(detected) > 0)

    def test_hooks_json_valid_if_present(self):
        """Verify that generated hooks.json contains valid hooks and existing target scripts."""
        hooks_json_path = os.path.join(ROOT_DIR, "hooks.json")
        if not os.path.isfile(hooks_json_path):
            render_hooks(plugin_dir=ROOT_DIR)

        self.assertTrue(os.path.isfile(hooks_json_path), f"hooks.json not found at {hooks_json_path}")

        with open(hooks_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("hooks", data)
        hooks = data["hooks"]
        for phase in ["PreInvocation", "PreToolUse", "PostToolUse", "Stop"]:
            self.assertIn(phase, hooks)

        commands = extract_commands(data)
        self.assertGreater(len(commands), 0, "No commands found in hooks.json")

        for cmd in commands:
            self.assertNotIn("{{PYTHON}}", cmd, f"Command '{cmd}' contains unrendered {{{{PYTHON}}}}")
            self.assertNotIn("{{PLUGIN_DIR}}", cmd, f"Command '{cmd}' contains unrendered {{{{PLUGIN_DIR}}}}")

            match = re.search(r"scripts[/\\]([a-zA-Z0-9_]+\.py)", cmd)
            self.assertIsNotNone(match, f"Could not extract target script from command '{cmd}'")
            script_file = os.path.join(ROOT_DIR, "scripts", match.group(1))
            self.assertTrue(os.path.isfile(script_file), f"Target script does not exist: {script_file}")

    def test_setup_utf8_streams(self):
        """Verify setup_utf8_streams() runs without exception on standard sys.stdin, sys.stdout, sys.stderr."""
        from hooks.utils import setup_utf8_streams
        setup_utf8_streams()

    def test_stop_hook_configured(self):
        """Verify hooks.template.json contains Stop lifecycle hook invoking stop.py."""
        template_path = os.path.join(ROOT_DIR, "hooks.template.json")
        with open(template_path, "r", encoding="utf-8") as f:
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
