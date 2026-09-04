from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure scripts directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.hooks.models import AgentRole
from scripts.hooks.session import SessionResolver, find_conversation_ids


def test_session_resolver_orchestrator_default(tmp_path: Path) -> None:
    brain_dir = tmp_path / "brain"
    brain_dir.mkdir()

    role = SessionResolver.resolve_role("non-existent-id", str(brain_dir))
    assert role == AgentRole.ORCHESTRATOR


def test_session_resolver_worker_from_transcript(tmp_path: Path) -> None:
    brain_dir = tmp_path / "brain"
    brain_dir.mkdir()

    parent_cid = "parent-cid-100"
    child_cid = "sub-cid-200"

    parent_dir = brain_dir / parent_cid / ".system_generated" / "logs"
    parent_dir.mkdir(parents=True)

    transcript_file = parent_dir / "transcript.jsonl"

    # Line 1: invocation of subagent with TypeName 'hephaestus'
    step_invoke = json.dumps({
        "type": "message",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "invoke_subagent",
                    "input": {
                        "Subagents": [
                            {
                                "TypeName": "hephaestus",
                                "Role": "Deep Worker",
                                "Prompt": "Implement feature",
                            }
                        ]
                    },
                }
            ],
        },
    })

    # Line 2: tool result returning child conversation ID
    step_result = json.dumps({
        "type": "message",
        "message": {
            "role": "toolResult",
            "toolName": "invoke_subagent",
            "content": json.dumps([{"conversationId": child_cid}]),
        },
    })

    transcript_file.write_text(f"{step_invoke}\n{step_result}\n", encoding="utf-8")

    typename = SessionResolver.resolve_typename(child_cid, str(brain_dir))
    assert typename == "hephaestus"

    role = SessionResolver.resolve_role(child_cid, str(brain_dir))
    assert role == AgentRole.WORKER


def test_session_resolver_orchestrator_from_transcript(tmp_path: Path) -> None:
    brain_dir = tmp_path / "brain"
    brain_dir.mkdir()

    parent_cid = "parent-cid-300"
    child_cid = "sub-cid-400"

    parent_dir = brain_dir / parent_cid / ".system_generated" / "logs"
    parent_dir.mkdir(parents=True)

    transcript_file = parent_dir / "transcript.jsonl"

    step_invoke = json.dumps({
        "name": "invoke_subagent",
        "subagents": [{"TypeName": "prometheus"}],
    })

    step_result = json.dumps({
        "conversationId": child_cid,
        "invoke_subagent": True,
    })

    transcript_file.write_text(f"{step_invoke}\n{step_result}\n", encoding="utf-8")

    role = SessionResolver.resolve_role(child_cid, str(brain_dir))
    assert role == AgentRole.ORCHESTRATOR


def test_find_conversation_ids_embedded_uuid_and_json() -> None:
    uuid_1 = "12345678-1234-1234-1234-123456789abc"
    uuid_2 = "abcdef01-2345-6789-abcd-ef0123456789"

    # String with embedded UUID surrounded by text and punctuation
    text = f"Invoked subagent {uuid_1}. Finished successfully!"
    assert find_conversation_ids(text) == [uuid_1]

    # Multiple UUIDs in arbitrary text
    multi_text = f"Spawned workers: {uuid_1} and {uuid_2}."
    assert find_conversation_ids(multi_text) == [uuid_1, uuid_2]

    # JSON-encoded tool result string with conversationId
    json_result = json.dumps([{"conversationId": uuid_1}])
    assert find_conversation_ids(json_result) == [uuid_1]

    # JSON-encoded tool result string with embedded UUID text
    json_embedded = json.dumps({"output": f"Subagent id is {uuid_2}."})
    assert find_conversation_ids(json_embedded) == [uuid_2]

    # Dict with conversationId and custom probable ID
    assert find_conversation_ids({"conversationId": "sub-worker-99"}) == ["sub-worker-99"]

    # Deduplication and known agent exclusion
    mixed = json.dumps({
        "conversationId": uuid_1,
        "details": f"Subagent {uuid_1} run by sisyphus",
    })
    assert find_conversation_ids(mixed) == [uuid_1]


def test_session_resolver_embedded_uuid_and_json_tool_result(tmp_path: Path) -> None:
    brain_dir = tmp_path / "brain"
    brain_dir.mkdir()

    parent_cid = "parent-cid-900"
    child_cid = "12345678-abcd-1234-cdef-1234567890ab"

    parent_dir = brain_dir / parent_cid / ".system_generated" / "logs"
    parent_dir.mkdir(parents=True)

    transcript_file = parent_dir / "transcript.jsonl"

    # Line 1: invoke_subagent call for 'hephaestus'
    step_invoke = json.dumps({
        "type": "message",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "invoke_subagent",
                    "input": {
                        "Subagents": [
                            {
                                "TypeName": "hephaestus",
                                "Role": "Deep Worker",
                                "Prompt": "Implement feature",
                            }
                        ]
                    },
                }
            ],
        },
    })

    # Line 2: tool result where content is a JSON-encoded string with embedded UUID text
    step_result = json.dumps({
        "type": "message",
        "message": {
            "role": "toolResult",
            "toolName": "invoke_subagent",
            "content": json.dumps({"status": "ok", "message": f"Created subagent {child_cid}."}),
        },
    })

    transcript_file.write_text(f"{step_invoke}\n{step_result}\n", encoding="utf-8")

    typename = SessionResolver.resolve_typename(child_cid, str(brain_dir))
    assert typename == "hephaestus"

    role = SessionResolver.resolve_role(child_cid, str(brain_dir))
    assert role == AgentRole.WORKER

