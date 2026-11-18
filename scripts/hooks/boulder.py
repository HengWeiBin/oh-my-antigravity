from __future__ import annotations

import json
import os
from typing import Any

from scripts.hooks.utils import resolve_path


def _extract_boulder_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract work entries from Boulder schema v2 or v1."""
    works = data.get("works")
    if isinstance(works, dict):
        return [entry for entry in works.values() if isinstance(entry, dict)]
    if data.get("schema_version") == 2:
        return []
    return [data]


def _collect_search_dirs(payload: dict[str, Any], cwd: str = "") -> list[str]:
    """Collect unique resolved workspace directories from payload and cwd."""
    workspace_paths_raw = payload.get("workspacePaths", [])
    if not isinstance(workspace_paths_raw, list):
        workspace_paths_raw = []
    workspace_paths = [wp for wp in workspace_paths_raw if isinstance(wp, str) and wp]

    raw_cwd = payload.get("cwd")
    payload_cwd = raw_cwd if isinstance(raw_cwd, str) and raw_cwd else (cwd if isinstance(cwd, str) else "")

    resolved_cwd = resolve_path(payload_cwd) if payload_cwd else ""
    resolved_workspaces = [
        resolve_path(wp, resolved_cwd if resolved_cwd else None)
        for wp in workspace_paths
    ]

    dirs_to_check: list[str] = []
    seen_dirs: set[str] = set()
    for candidate in [*resolved_workspaces, resolved_cwd]:
        if not candidate:
            continue
        abs_candidate = os.path.abspath(candidate)
        if abs_candidate not in seen_dirs:
            seen_dirs.add(abs_candidate)
            dirs_to_check.append(candidate)

    return dirs_to_check


def _matches_conversation(session_ids: Any, conversation_id: str) -> bool:
    """Return True if conversation_id matches an exact or prefixed entry in session_ids."""
    if not isinstance(session_ids, list):
        return False
    suffix = f":{conversation_id}"
    return any(
        isinstance(sid, str) and (sid == conversation_id or sid.endswith(suffix))
        for sid in session_ids
    )


def get_bound_active_plans(
    payload: dict[str, Any],
    cwd: str = "",
    conversation_id: str = "",
) -> list[str]:
    """Return deduplicated active plan .md paths bound to the current conversationId via .omo/boulder.json."""
    raw_cid = conversation_id or payload.get("conversationId") or payload.get("conversation_id") or ""
    if not isinstance(raw_cid, str) or not raw_cid:
        return []
    cid = raw_cid

    dirs_to_check = _collect_search_dirs(payload, cwd=cwd)
    if not dirs_to_check:
        return []

    plan_files: list[str] = []
    seen_plans: set[str] = set()

    for d in dirs_to_check:
        boulder_path = os.path.join(d, ".omo", "boulder.json")
        if not os.path.isfile(boulder_path):
            continue
        try:
            with open(boulder_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue

        if not isinstance(data, dict):
            continue

        for entry in _extract_boulder_entries(data):
            status = entry.get("status")
            if status is not None and status != "active":
                continue

            if not _matches_conversation(entry.get("session_ids"), cid):
                continue

            active_plan = entry.get("active_plan")
            if not isinstance(active_plan, str) or not active_plan.strip():
                continue

            base_dir = d
            worktree_path = entry.get("worktree_path")
            if isinstance(worktree_path, str) and worktree_path:
                resolved_wt = resolve_path(worktree_path, d)
                if os.path.isdir(resolved_wt):
                    base_dir = resolved_wt

            plan_path = (
                active_plan
                if os.path.isabs(active_plan)
                else resolve_path(active_plan, base_dir)
            )
            abs_plan_path = os.path.abspath(plan_path)

            if (
                os.path.isfile(abs_plan_path)
                and abs_plan_path.endswith(".md")
                and not abs_plan_path.endswith(("-review.md", ".review.md"))
                and abs_plan_path not in seen_plans
            ):
                seen_plans.add(abs_plan_path)
                plan_files.append(abs_plan_path)

    return plan_files
