from __future__ import annotations

import os

from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult


def check_comment_preservation(
    tool_name: str, tool_input: dict, tool_response: dict | None
) -> str | None:
    """
    After a file write, checks if comments were removed.
    Returns a warning string if significant comments were lost.
    Returns None if comment density looks OK.
    """
    valid_tools = {"write_to_file", "replace_file_content", "multi_replace_file_content"}
    if tool_name not in valid_tools:
        return None

    target_file = tool_input.get("TargetFile", "")
    if not target_file:
        return None

    _, ext = os.path.splitext(target_file)
    valid_exts = {".py", ".ts", ".js", ".tsx", ".sh"}
    if ext not in valid_exts:
        return None

    content = ""
    if tool_name == "write_to_file":
        content = tool_input.get("CodeContent", "")
    elif tool_name == "replace_file_content":
        content = tool_input.get("ReplacementContent", "")
    elif tool_name == "multi_replace_file_content":
        chunks = tool_input.get("ReplacementChunks", [])
        content = "\n".join(chunk.get("ReplacementContent", "") for chunk in chunks)

    if not content:
        return None

    lines = content.splitlines()
    total_lines = len(lines)

    if total_lines <= 20:
        return None

    comment_lines = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith(("#", "//", "*", "/*")) or '"""' in stripped or "'''" in stripped:
            comment_lines += 1

    if comment_lines == 0:
        return (
            f"⚠️ COMMENT CHECKER: The written content appears to have no comments for a "
            f"{total_lines}-line code file. Important comments, docstrings, or noqa annotations "
            f"may have been accidentally removed. Please verify that comments were intentionally omitted."
        )

    return None


run_comment_checker = check_comment_preservation


class CommentCheckerHook(BaseHook):
    @property
    def name(self) -> str:
        return "comment_checker"

    def execute(self, context: HookContext) -> HookResult:
        if context.tool_name not in {"write_to_file", "replace_file_content", "multi_replace_file_content"}:
            return HookResult()
        warning = check_comment_preservation(context.tool_name, context.tool_input, None)
        if warning:
            return HookResult(additional_context=warning)
        return HookResult()
