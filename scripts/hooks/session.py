from __future__ import annotations

import json
import os
import re
from typing import Any

from scripts.hooks.models import AgentRole

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)
UUID_SEARCH_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE
)
KNOWN_AGENTS = {
    "sisyphus",
    "atlas",
    "prometheus",
    "metis",
    "momus",
    "hephaestus",
    "sisyphus-junior",
    "explore",
    "librarian",
}

CONDUCTOR_ROLES = {"sisyphus", "atlas", "prometheus", "metis", "momus"}
WORKER_ROLES = {"hephaestus", "sisyphus-junior", "explore", "librarian"}


def is_probable_conversation_id(val: Any) -> bool:
    if not isinstance(val, str):
        return False
    val_stripped = val.strip()
    if val_stripped.lower() in KNOWN_AGENTS:
        return False
    if UUID_PATTERN.match(val_stripped):
        return True
    if "-" in val_stripped:
        parts = val_stripped.split("-")
        if len(parts) >= 2 and parts[-1].isdigit():
            return True
        if len(val_stripped) == 36 and val_stripped.count("-") == 4:
            return True
    return False


def find_invoke_subagent_calls(obj: Any) -> list[list[str]]:
    calls: list[list[str]] = []
    if isinstance(obj, dict):
        is_invoke = False
        for k, v in obj.items():
            if k in ("name", "tool", "toolName") and v == "invoke_subagent":
                is_invoke = True
                break
        if is_invoke:
            subagents = None
            for k, v in obj.items():
                if k.lower() == "subagents":
                    subagents = v
                    break
                if isinstance(v, dict):
                    for sk, sv in v.items():
                        if sk.lower() == "subagents":
                            subagents = sv
                            break
                elif isinstance(v, str) and (
                    (v.strip().startswith("{") and v.strip().endswith("}"))
                    or (v.strip().startswith("[") and v.strip().endswith("]"))
                ):
                    try:
                        parsed_v = json.loads(v)
                        if isinstance(parsed_v, dict):
                            for sk, sv in parsed_v.items():
                                if sk.lower() == "subagents":
                                    subagents = sv
                                    break
                    except Exception:  # noqa: BLE001, S110
                        pass
            if isinstance(subagents, list):
                type_names: list[str] = []
                for sa in subagents:
                    if isinstance(sa, dict):
                        tn = sa.get("TypeName") or sa.get("typename") or sa.get("type_name")
                        if tn:
                            type_names.append(tn)
                if type_names:
                    calls.append(type_names)
        else:
            for v in obj.values():
                calls.extend(find_invoke_subagent_calls(v))
    elif isinstance(obj, list):
        for item in obj:
            calls.extend(find_invoke_subagent_calls(item))
    elif isinstance(obj, str):
        if (obj.strip().startswith("{") and obj.strip().endswith("}")) or (
            obj.strip().startswith("[") and obj.strip().endswith("]")
        ):
            try:
                parsed = json.loads(obj)
                calls.extend(find_invoke_subagent_calls(parsed))
            except Exception:  # noqa: BLE001, S110
                pass
    return calls


def find_conversation_ids(obj: Any) -> list[str]:
    cids: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("conversationId", "conversation_id") and isinstance(v, str):
                if v not in cids and v.lower() not in KNOWN_AGENTS:
                    cids.append(v)
            elif isinstance(v, (dict, list, str)):
                cids.extend(find_conversation_ids(v))
    elif isinstance(obj, list):
        for item in obj:
            cids.extend(find_conversation_ids(item))
    elif isinstance(obj, str):
        stripped = obj.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or (
            stripped.startswith("[") and stripped.endswith("]")
        ):
            try:
                parsed = json.loads(obj)
                cids.extend(find_conversation_ids(parsed))
            except Exception:  # noqa: BLE001, S110
                pass
        for match in UUID_SEARCH_PATTERN.finditer(obj):
            cid = match.group(0)
            if cid not in cids and cid.lower() not in KNOWN_AGENTS:
                cids.append(cid)
        if is_probable_conversation_id(obj) and obj not in cids:
            cids.append(obj)
    return list(dict.fromkeys(cids))


def parse_typename_from_log(
    log_path: str, target_conversation_id: str, parent_cid: str
) -> str | None:
    pending_type_names: list[list[str]] = []
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:  # noqa: BLE001, S112
                    continue

                calls = find_invoke_subagent_calls(obj)
                if calls:
                    pending_type_names.extend(calls)
                    continue

                line_lower = line.lower()
                has_cid_match = (
                    "conversationid" in line_lower
                    or "conversation_id" in line_lower
                    or UUID_SEARCH_PATTERN.search(line) is not None
                )
                if (
                    ("invoke_subagent" in line_lower or "subagent" in line_lower)
                    and has_cid_match
                    and pending_type_names
                ):
                    cids: list[str] = []
                    found_cids = find_conversation_ids(obj)
                    for cid in found_cids:
                        if cid != parent_cid and cid not in cids:
                            cids.append(cid)
                    if cids:
                        tns = pending_type_names.pop(0)
                        for i in range(min(len(tns), len(cids))):
                            if cids[i] == target_conversation_id:
                                return tns[i]
    except Exception:  # noqa: BLE001, S110
        pass
    return None


class SessionResolver:
    @classmethod
    def resolve_typename(cls, conversation_id: str, brain_dir: str) -> str | None:
        if not conversation_id or not brain_dir or not os.path.exists(brain_dir):
            return None

        try:
            entries = sorted(
                os.listdir(brain_dir),
                key=lambda x: os.path.getmtime(os.path.join(brain_dir, x)) if os.path.exists(os.path.join(brain_dir, x)) else 0,
                reverse=True
            )
        except OSError:
            return None

        for cid in entries:
            if cid == conversation_id:
                continue
            cid_dir = os.path.join(brain_dir, cid)
            if not os.path.isdir(cid_dir):
                continue
            subagent_file = os.path.join(cid_dir, ".system_generated", "subagents", f"{conversation_id}.json")
            if os.path.exists(subagent_file):
                try:
                    with open(subagent_file, "r", encoding="utf-8") as sf:
                        data = json.load(sf)
                        tn = data.get("subagentDescriptor", {}).get("typeName")
                        if tn:
                            return tn
                except Exception:  # noqa: BLE001, S110
                    pass
            logs_dir = os.path.join(cid_dir, ".system_generated", "logs")
            if not os.path.exists(logs_dir):
                continue
            for name in ["transcript.jsonl", "transcript_full.jsonl"]:
                log_path = os.path.join(logs_dir, name)
                if os.path.exists(log_path):
                    parsed_typename = parse_typename_from_log(log_path, conversation_id, cid)
                    if parsed_typename:
                        return parsed_typename
        return None

    @classmethod
    def resolve_role(cls, conversation_id: str, brain_dir: str) -> AgentRole:
        typename = cls.resolve_typename(conversation_id, brain_dir)
        if typename is None:
            return AgentRole.ORCHESTRATOR

        typename_lower = typename.lower()
        if typename_lower in WORKER_ROLES:
            return AgentRole.WORKER
        elif typename_lower in CONDUCTOR_ROLES:
            return AgentRole.ORCHESTRATOR
        else:
            # Any non-None subagent typename not in conductor set is treated as worker
            return AgentRole.WORKER
