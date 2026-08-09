from __future__ import annotations

import os
import sys

# Ensure scripts path is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.hooks.models import AgentRole
from scripts.hooks.permission import PermissionPolicy


def test_orchestrator_code_edits_denied_or_ask() -> None:
    res = PermissionPolicy.evaluate(
        role=AgentRole.ORCHESTRATOR,
        tool_name="write_to_file",
        target_path="src/app.py",
    )
    assert not res.allowed
    assert res.decision == "ask"
    assert res.reason is not None
    assert "Lead Orchestrator agents do not edit source code directly" in res.reason


def test_orchestrator_allowed_paths() -> None:
    for path in [
        "plans/plan.md",
        ".omo/boulder.json",
        ".agents/hooks.json",
        "task_list.md",
        "docs/spec.md",
    ]:
        res = PermissionPolicy.evaluate(
            role=AgentRole.ORCHESTRATOR,
            tool_name="write_to_file",
            target_path=path,
        )
        assert res.allowed, f"Failed on path: {path}"
        assert res.decision == "allow"


def test_worker_restrictions() -> None:
    # Subagent writing to .omo/plans/plan.md should be denied
    res1 = PermissionPolicy.evaluate(
        role=AgentRole.WORKER,
        tool_name="write_to_file",
        target_path=".omo/plans/plan.md",
    )
    assert not res1.allowed
    assert res1.decision == "deny"
    assert res1.reason is not None
    assert "Subagents (workers) are forbidden from modifying .omo/" in res1.reason

    # Subagent writing to .omo/drafts/draft.md should be denied
    res2 = PermissionPolicy.evaluate(
        role=AgentRole.WORKER,
        tool_name="write_to_file",
        target_path=".omo/drafts/draft.md",
    )
    assert not res2.allowed
    assert res2.decision == "deny"

    # Subagent writing to .agents/ should be denied
    res3 = PermissionPolicy.evaluate(
        role=AgentRole.WORKER,
        tool_name="write_to_file",
        target_path=".agents/hooks.json",
    )
    assert not res3.allowed
    assert res3.decision == "deny"

    # Subagent writing to rules/ should be denied
    res4 = PermissionPolicy.evaluate(
        role=AgentRole.WORKER,
        tool_name="write_to_file",
        target_path="rules/oh-my-openagent-rules.md",
    )
    assert not res4.allowed
    assert res4.decision == "deny"


def test_worker_allowed_paths() -> None:
    # Subagent writing to .omo/notepads/learnings.md should be allowed
    res1 = PermissionPolicy.evaluate(
        role=AgentRole.WORKER,
        tool_name="write_to_file",
        target_path=".omo/notepads/learnings.md",
    )
    assert res1.allowed
    assert res1.decision == "allow"

    # Subagent writing to .omo/boulder.json should be allowed
    res2 = PermissionPolicy.evaluate(
        role=AgentRole.WORKER,
        tool_name="write_to_file",
        target_path=".omo/boulder.json",
    )
    assert res2.allowed
    assert res2.decision == "allow"

    # Subagent writing to source code should be allowed
    res3 = PermissionPolicy.evaluate(
        role=AgentRole.WORKER,
        tool_name="write_to_file",
        target_path="src/app.py",
    )
    assert res3.allowed
    assert res3.decision == "allow"


def test_read_tools_always_allowed() -> None:
    res = PermissionPolicy.evaluate(
        role=AgentRole.ORCHESTRATOR,
        tool_name="view_file",
        target_path="src/app.py",
    )
    assert res.allowed
    assert res.decision == "allow"
