from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LifecycleEvent(Enum):
    PRE_INVOCATION = "PreInvocation"
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"


class AgentRole(Enum):
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    RESEARCH = "research"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class HookContext:
    lifecycle: LifecycleEvent
    conversation_id: str
    cwd: str
    tool_name: str | None = None
    tool_input: dict[str, Any] = field(default_factory=dict)
    tool_output: str | None = None
    user_prompt: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class HookResult:
    injected_steps: list[dict[str, Any]] = field(default_factory=list)
    decision: str | None = None  # "allow" | "deny" | "ask"
    reason: str | None = None
    additional_context: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
