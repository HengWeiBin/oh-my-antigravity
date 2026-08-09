from __future__ import annotations

import glob
import os

from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult


def get_rules_messages(payload: dict) -> list[dict]:
    """
    Scans workspace for rule files and injects matched rules.
    Returns list of {'ephemeralMessage': str} dicts.
    """
    context = payload.get("context", {})
    workspace_uri = context.get("workspaceUri", "")
    workspace_root = ""
    if workspace_uri.startswith("file:///"):
        workspace_root = workspace_uri[8:].replace("/", os.sep)
    elif workspace_uri:
        workspace_root = workspace_uri

    cwd = context.get("cwd", "")

    if not workspace_root:
        # Fallback if no workspace is provided
        workspace_root = cwd if cwd else os.getcwd()

    search_locations = [
        os.path.join(workspace_root, ".rules"),
        os.path.join(workspace_root, "rules", "*.md"),
        os.path.join(workspace_root, ".agents", "rules", "*.md"),
        os.path.join(workspace_root, ".gemini", "rules", "*.md"),
    ]

    if cwd and os.path.abspath(cwd) != os.path.abspath(workspace_root):
        search_locations.append(os.path.join(cwd, ".rules"))

    found_files = []
    for loc in search_locations:
        if "*" in loc:
            matches = glob.glob(loc)
            for m in matches:
                found_files.append(os.path.abspath(m))
        else:
            if os.path.exists(loc):
                found_files.append(os.path.abspath(loc))

    # Deduplicate by path
    unique_files = []
    seen = set()
    for f in found_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)

    # Filter by extension and limit to 5
    valid_exts = {".md", ".rules", ".txt"}
    rule_files_to_read = []
    for f in unique_files:
        if not os.path.isfile(f):
            continue
        # .rules could have no extension from splitext
        name = os.path.basename(f)
        _, ext = os.path.splitext(f)
        if ext.lower() in valid_exts or name == ".rules":
            rule_files_to_read.append(f)
            if len(rule_files_to_read) >= 5:
                break

    messages = []
    for f in rule_files_to_read:
        try:
            with open(f, "r", encoding="utf-8") as file:
                content = file.read(2048)
                rel_path = os.path.relpath(f, workspace_root)
                messages.append({
                    "ephemeralMessage": f"📜 Rules from {rel_path}:\n\n{content}"
                })
        except Exception:  # noqa: BLE001, S110
            pass

    return messages


run_rules_injector = get_rules_messages


class RulesInjectorHook(BaseHook):
    @property
    def name(self) -> str:
        return "rules_injector"

    def execute(self, context: HookContext) -> HookResult:
        messages = get_rules_messages(context.raw_payload)
        return HookResult(injected_steps=messages)
