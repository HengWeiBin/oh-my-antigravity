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
from unittest.mock import patch, MagicMock

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


if __name__ == "__main__":
    unittest.main()
