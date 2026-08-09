from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure scripts directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.hooks.models import AgentRole
from scripts.hooks.session import SessionResolver


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
