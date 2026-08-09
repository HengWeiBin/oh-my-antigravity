from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure scripts directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.hooks.skill_resolver import SkillResolver


def test_skill_resolver_custom_roots(tmp_path: Path) -> None:
    root1 = tmp_path / "root1"
    root2 = tmp_path / "root2"

    skill_file1 = root1 / "skills" / "my-skill" / "SKILL.md"
    skill_file1.parent.mkdir(parents=True)
    skill_file1.write_text("Instruction from root1", encoding="utf-8")

    resolver = SkillResolver(search_roots=[str(root1), str(root2)])

    skill_def = resolver.resolve_skill("my-skill")
    assert skill_def is not None
    assert skill_def.name == "my-skill"
    assert skill_def.content == "Instruction from root1"

    instruction = resolver.format_instruction_block("my-skill")
    assert instruction == "<skill-instruction>\nInstruction from root1\n</skill-instruction>"


def test_skill_resolver_workspace_precedence(tmp_path: Path) -> None:
    ws_dir = tmp_path / "workspace"
    plugin_dir = tmp_path / "plugin"

    ws_skill = ws_dir / ".agents" / "skills" / "custom-skill" / "SKILL.md"
    ws_skill.parent.mkdir(parents=True)
    ws_skill.write_text("Workspace skill instruction", encoding="utf-8")

    plugin_skill = plugin_dir / "skills" / "custom-skill" / "SKILL.md"
    plugin_skill.parent.mkdir(parents=True)
    plugin_skill.write_text("Plugin skill instruction", encoding="utf-8")

    resolver = SkillResolver()
    skill_def = resolver.resolve_skill("custom-skill", workspace_paths=[str(ws_dir)], cwd=str(ws_dir))
    assert skill_def is not None
    assert skill_def.content == "Workspace skill instruction"


def test_skill_resolver_caching(tmp_path: Path) -> None:
    root = tmp_path / "skills_root"
    skill_file = root / "skills" / "cached-skill" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text("Original content", encoding="utf-8")

    resolver = SkillResolver(search_roots=[str(root)])

    first_res = resolver.resolve_skill("cached-skill")
    assert first_res is not None
    assert first_res.content == "Original content"

    # Modify file on disk
    skill_file.write_text("Modified content", encoding="utf-8")

    # Second lookup should return cached definition
    second_res = resolver.resolve_skill("cached-skill")
    assert second_res is not None
    assert second_res.content == "Original content"


def test_skill_resolver_nonexistent() -> None:
    resolver = SkillResolver()
    skill_def = resolver.resolve_skill("non-existent-skill-xyz")
    assert skill_def is None

    instruction = resolver.format_instruction_block("non-existent-skill-xyz")
    assert instruction is None
