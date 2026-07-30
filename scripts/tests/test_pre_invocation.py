#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# ─── How to run ───
# 1. Run unittest:
#      python -m unittest scripts/tests/test_pre_invocation.py
# ──────────────────

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Resolve scripts path and add it to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(f"{os.environ.get('USERPROFILE')}/.gemini/config/plugins/oh-my-antigravity/scripts"))

import pre_invocation

EXPECTED_EPHEMERAL_MESSAGE = (
    "A `.codegraph` directory and the `codegraph` MCP server are active in this workspace. "
    "You should prioritize using `codegraph_explore` to explore symbols, find call paths, "
    "and understand the codebase architecture in a single round-trip instead of standard grep + read loops."
)


class TestPreInvocation(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_directories: list[str] = []
        self.mock_files: dict[str, str] = {}

        def isdir_side_effect(path: str) -> bool:
            norm = path.replace("\\", "/").rstrip("/")
            for d in self.mock_directories:
                if norm.endswith(d.rstrip("/")):
                    return True
            return False

        def isfile_side_effect(path: str) -> bool:
            norm = path.replace("\\", "/").rstrip("/")
            for f in self.mock_files:
                if norm.endswith(f.rstrip("/")):
                    return True
            return False

        def open_side_effect(file_path: str, *args, **kwargs) -> io.StringIO:
            norm = file_path.replace("\\", "/").rstrip("/")
            for f, content in self.mock_files.items():
                if norm.endswith(f.rstrip("/")):
                    return io.StringIO(content)
            raise FileNotFoundError(f"No mock file for: {file_path}")

        # Start patches
        self.patcher_isdir = patch("os.path.isdir", side_effect=isdir_side_effect)
        self.patcher_isfile = patch("os.path.isfile", side_effect=isfile_side_effect)
        self.patcher_open = patch("builtins.open", side_effect=open_side_effect)

        self.patcher_isdir.start()
        self.patcher_isfile.start()
        self.patcher_open.start()

    def tearDown(self) -> None:
        self.patcher_isdir.stop()
        self.patcher_isfile.stop()
        self.patcher_open.stop()

    @patch("sys.stdin.read")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_happy_path_mcp_config(self, mock_stdout: io.StringIO, mock_stdin: MagicMock) -> None:
        mock_stdin.return_value = json.dumps({
            "invocationNum": 0,
            "workspacePaths": ["/workspace"],
            "cwd": "/workspace"
        })

        self.mock_directories = [".codegraph"]
        self.mock_files = {
            ".gemini/config/mcp_config.json": '{"mcpServers": {"codegraph": {}}}'
        }

        pre_invocation.main()

        output_json = json.loads(mock_stdout.getvalue())
        self.assertIn("injectSteps", output_json)
        self.assertEqual(len(output_json["injectSteps"]), 1)
        self.assertEqual(
            output_json["injectSteps"][0]["ephemeralMessage"],
            EXPECTED_EPHEMERAL_MESSAGE
        )

    @patch("sys.stdin.read")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_happy_path_mcp_antigravity_config(self, mock_stdout: io.StringIO, mock_stdin: MagicMock) -> None:
        mock_stdin.return_value = json.dumps({
            "invocationNum": 0,
            "workspacePaths": ["/workspace"],
            "cwd": "/workspace"
        })

        self.mock_directories = [".codegraph"]
        self.mock_files = {
            ".gemini/antigravity/mcp_config.json": '{"mcpServers": {"codegraph": {}}}'
        }

        pre_invocation.main()

        output_json = json.loads(mock_stdout.getvalue())
        self.assertIn("injectSteps", output_json)
        self.assertEqual(len(output_json["injectSteps"]), 1)
        self.assertEqual(
            output_json["injectSteps"][0]["ephemeralMessage"],
            EXPECTED_EPHEMERAL_MESSAGE
        )

    @patch("sys.stdin.read")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_happy_path_workspace_agents_config(self, mock_stdout: io.StringIO, mock_stdin: MagicMock) -> None:
        mock_stdin.return_value = json.dumps({
            "invocationNum": 0,
            "workspacePaths": ["/workspace"],
            "cwd": "/workspace"
        })

        self.mock_directories = [".codegraph"]
        self.mock_files = {
            "/workspace/.agents/mcp_config.json": '{"mcpServers": {"codegraph": {}}}'
        }

        pre_invocation.main()

        output_json = json.loads(mock_stdout.getvalue())
        self.assertIn("injectSteps", output_json)
        self.assertEqual(len(output_json["injectSteps"]), 1)
        self.assertEqual(
            output_json["injectSteps"][0]["ephemeralMessage"],
            EXPECTED_EPHEMERAL_MESSAGE
        )

    @patch("sys.stdin.read")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_happy_path_mcp_directory(self, mock_stdout: io.StringIO, mock_stdin: MagicMock) -> None:
        mock_stdin.return_value = json.dumps({
            "invocationNum": 0,
            "workspacePaths": ["/workspace"],
            "cwd": "/workspace"
        })

        self.mock_directories = [
            ".codegraph",
            ".gemini/antigravity/mcp/codegraph"
        ]

        pre_invocation.main()

        output_json = json.loads(mock_stdout.getvalue())
        self.assertIn("injectSteps", output_json)
        self.assertEqual(len(output_json["injectSteps"]), 1)
        self.assertEqual(
            output_json["injectSteps"][0]["ephemeralMessage"],
            EXPECTED_EPHEMERAL_MESSAGE
        )

    @patch("sys.stdin.read")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_turn_greater_than_zero(self, mock_stdout: io.StringIO, mock_stdin: MagicMock) -> None:
        mock_stdin.return_value = json.dumps({
            "invocationNum": 1,
            "workspacePaths": ["/workspace"],
            "cwd": "/workspace"
        })

        self.mock_directories = [
            ".codegraph",
            ".gemini/antigravity/mcp/codegraph"
        ]

        pre_invocation.main()

        output_json = json.loads(mock_stdout.getvalue())
        self.assertEqual(output_json, {"injectSteps": []})

    @patch("sys.stdin.read")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_codegraph_directory_missing(self, mock_stdout: io.StringIO, mock_stdin: MagicMock) -> None:
        mock_stdin.return_value = json.dumps({
            "invocationNum": 0,
            "workspacePaths": ["/workspace"],
            "cwd": "/workspace"
        })

        self.mock_directories = [
            ".gemini/antigravity/mcp/codegraph"
        ]

        pre_invocation.main()

        output_json = json.loads(mock_stdout.getvalue())
        self.assertEqual(output_json, {"injectSteps": []})

    @patch("sys.stdin.read")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_mcp_server_not_active(self, mock_stdout: io.StringIO, mock_stdin: MagicMock) -> None:
        mock_stdin.return_value = json.dumps({
            "invocationNum": 0,
            "workspacePaths": ["/workspace"],
            "cwd": "/workspace"
        })

        self.mock_directories = [".codegraph"]
        self.mock_files = {}

        pre_invocation.main()

        output_json = json.loads(mock_stdout.getvalue())
        self.assertEqual(output_json, {"injectSteps": []})

    @patch("sys.stdin.read")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_invalid_json_input(self, mock_stdout: io.StringIO, mock_stdin: MagicMock) -> None:
        mock_stdin.return_value = "invalid json data"

        pre_invocation.main()

        output_json = json.loads(mock_stdout.getvalue())
        self.assertEqual(output_json, {})

    @patch("sys.stdin.read")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_empty_input(self, mock_stdout: io.StringIO, mock_stdin: MagicMock) -> None:
        mock_stdin.return_value = ""

        pre_invocation.main()

        output_json = json.loads(mock_stdout.getvalue())
        self.assertEqual(output_json, {"injectSteps": []})

    def test_is_subagent_session(self) -> None:
        self.assertTrue(pre_invocation.is_subagent_session({"isSubagent": True}))
        self.assertTrue(pre_invocation.is_subagent_session({"is_subagent": "true"}))
        self.assertTrue(pre_invocation.is_subagent_session({"parentConversationId": "parent-123"}))
        self.assertTrue(pre_invocation.is_subagent_session({"role": "subagent"}))
        self.assertTrue(pre_invocation.is_subagent_session({"typename": "hephaestus"}))
        self.assertFalse(pre_invocation.is_subagent_session({"role": "user"}))
        self.assertFalse(pre_invocation.is_subagent_session({}))

    @patch("hooks.utils.os.path.isdir")
    @patch("hooks.utils.os.listdir")
    @patch("hooks.utils.os.path.isfile")
    @patch("builtins.open", new_callable=mock_open, read_data='{"conversationId": "sub-123", "invoke_subagent": true}\n')
    def test_is_subagent_session_brain_dir(self, mock_file, mock_isfile, mock_listdir, mock_isdir) -> None:
        mock_isdir.return_value = True
        mock_listdir.return_value = ["parent-456"]
        mock_isfile.return_value = True
        payload = {
            "conversationId": "sub-123",
            "artifactDirectoryPath": "/brain/sub-123"
        }
        self.assertTrue(pre_invocation.is_subagent_session(payload))

    def test_extract_user_prompt(self) -> None:
        self.assertEqual(pre_invocation.extract_user_prompt({"prompt": "/programming"}), "/programming")
        self.assertEqual(pre_invocation.extract_user_prompt({"userPrompt": "hello world"}), "hello world")
        self.assertEqual(
            pre_invocation.extract_user_prompt({"messages": [{"role": "user", "content": "/debugging"}]}),
            "/debugging"
        )
        self.assertEqual(pre_invocation.extract_user_prompt({}), "")

    @patch("hooks.utils.os.path.isfile")
    @patch("builtins.open", new_callable=mock_open, read_data='{"type": "USER_INPUT", "content": "from transcript"}\n')
    def test_extract_user_prompt_transcript_fallback(self, mock_file, mock_isfile) -> None:
        mock_isfile.return_value = True
        payload = {"transcriptPath": "/fake/transcript.jsonl"}
        self.assertEqual(pre_invocation.extract_user_prompt(payload), "from transcript")

    def test_parse_skill_commands(self) -> None:
        prompt = "/programming /debugging Please execute /programming and /refactor"
        skills = pre_invocation.parse_skill_commands(prompt)
        self.assertEqual(skills, ["programming", "debugging", "refactor"])
        self.assertEqual(pre_invocation.parse_skill_commands("http://example.com/foo"), [])
        self.assertEqual(pre_invocation.parse_skill_commands('"/omomomo"'), ["omomomo"])
        self.assertEqual(pre_invocation.parse_skill_commands("(/test)"), ["test"])

    def test_format_skill_instruction(self) -> None:
        formatted = pre_invocation.format_skill_instruction("programming", "Code strictly.")
        self.assertEqual(formatted, "<skill-instruction>\nCode strictly.\n</skill-instruction>")

    @patch("sys.stdin.read")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_subagent_skill_autoload(self, mock_stdout: io.StringIO, mock_stdin: MagicMock) -> None:
        mock_stdin.return_value = json.dumps({
            "isSubagent": True,
            "prompt": "Run /test-skill for me",
            "workspacePaths": ["/workspace"],
            "cwd": "/workspace"
        })

        self.mock_files = {
            "/workspace/skills/test-skill/SKILL.md": "Skill instructions content"
        }

        pre_invocation.main()

        output_json = json.loads(mock_stdout.getvalue())
        self.assertIn("injectSteps", output_json)
        self.assertEqual(len(output_json["injectSteps"]), 1)
        self.assertEqual(
            output_json["injectSteps"][0]["ephemeralMessage"],
            "<skill-instruction>\nSkill instructions content\n</skill-instruction>"
        )

    @patch("sys.stdin.read")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_agent_skill_ignore(self, mock_stdout: io.StringIO, mock_stdin: MagicMock) -> None:
        mock_stdin.return_value = json.dumps({
            "isSubagent": False,
            "prompt": "Run /test-skill for me",
            "workspacePaths": ["/workspace"],
            "cwd": "/workspace"
        })

        self.mock_files = {
            "/workspace/skills/test-skill/SKILL.md": "Skill instructions content"
        }

        pre_invocation.main()

        output_json = json.loads(mock_stdout.getvalue())
        self.assertEqual(output_json, {"injectSteps": []})


if __name__ == "__main__":
    unittest.main()

