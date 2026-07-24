from __future__ import annotations

import os

def get_compaction_todo_messages(payload: dict) -> list[dict]:
    """
    On high invocation numbers (>= 15, suggesting context compaction),
    scans .omo/plans/ and .omo/drafts/ for unchecked TODOs and returns
    ephemeral messages to re-inject them.
    Returns list of {'ephemeralMessage': str} dicts, or empty list.
    """
    invocation_num = payload.get("invocationNum", 0)
    if not isinstance(invocation_num, int) or invocation_num < 15:
        return []

    workspace_paths_raw = payload.get("workspacePaths", [])
    workspace_paths = []
    if isinstance(workspace_paths_raw, list):
        for wp in workspace_paths_raw:
            if isinstance(wp, str) and wp:
                workspace_paths.append(wp)
                
    cwd = payload.get("cwd", "")
    if isinstance(cwd, str) and cwd and cwd not in workspace_paths:
        workspace_paths.append(cwd)

    if not workspace_paths:
        return []

    dirs_to_check = []
    for wp in workspace_paths:
        plans_dir = os.path.join(wp, ".omo", "plans")
        drafts_dir = os.path.join(wp, ".omo", "drafts")
        if plans_dir not in dirs_to_check:
            dirs_to_check.append(plans_dir)
        if drafts_dir not in dirs_to_check:
            dirs_to_check.append(drafts_dir)

    messages = []
    files_processed = 0

    for d in dirs_to_check:
        if not os.path.isdir(d):
            continue
        try:
            for fname in sorted(os.listdir(d)):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(d, fname)
                if not os.path.isfile(fpath):
                    continue

                unchecked_items = []
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        for line in f:
                            stripped = line.strip()
                            if stripped.startswith("- [ ]") or stripped.startswith("* [ ]"):
                                unchecked_items.append(stripped)
                                if len(unchecked_items) >= 10:
                                    break
                except Exception:
                    continue

                if unchecked_items:
                    msg_lines = [
                        "🔄 COMPACTION TODO PRESERVER: Active plan TODOs detected (context may have been compacted).",
                        "Remaining unchecked items:",
                        f"[{fname}]"
                    ]
                    for item in unchecked_items:
                        msg_lines.append(item)
                    msg_lines.append("Please ensure you continue working on these items.")
                    messages.append({"ephemeralMessage": "\n".join(msg_lines)})
                    
                    files_processed += 1
                    if files_processed >= 3:
                        return messages
        except Exception:
            pass

    return messages

run_compaction_todo_preserver = get_compaction_todo_messages
