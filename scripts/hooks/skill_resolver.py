from __future__ import annotations

import os
from dataclasses import dataclass

from scripts.hooks.utils import get_home_dir, resolve_path


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    path: str
    content: str


class SkillResolver:
    def __init__(self, search_roots: list[str] | None = None) -> None:
        self.custom_search_roots = search_roots
        self._cache: dict[tuple[str, tuple[str, ...], str], SkillDefinition | None] = {}

    def get_search_paths(
        self,
        skill_name: str,
        workspace_paths: list[str] | None = None,
        cwd: str | None = None,
    ) -> list[str]:
        if not skill_name:
            return []

        paths: list[str] = []

        if self.custom_search_roots:
            for root in self.custom_search_roots:
                paths.append(os.path.join(root, skill_name, "SKILL.md"))
                paths.append(os.path.join(root, "skills", skill_name, "SKILL.md"))
            return paths

        home = get_home_dir()
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        plugin_dir = os.path.dirname(script_dir)

        dirs_to_check: list[str] = []
        if workspace_paths:
            for wp in workspace_paths:
                if wp and wp not in dirs_to_check:
                    dirs_to_check.append(wp)
        if cwd and cwd not in dirs_to_check:
            dirs_to_check.append(cwd)

        # 1. Workspace skills
        for d in dirs_to_check:
            paths.append(os.path.join(d, "skills", skill_name, "SKILL.md"))
            paths.append(os.path.join(d, ".agents", "skills", skill_name, "SKILL.md"))
            paths.append(os.path.join(d, ".gemini", "skills", skill_name, "SKILL.md"))

        # 2. Plugin skills
        paths.append(os.path.join(plugin_dir, "skills", skill_name, "SKILL.md"))

        # 2.5 Sibling plugin directories
        plugins_dir = os.path.dirname(plugin_dir)
        if os.path.isdir(plugins_dir):
            try:
                for entry in os.listdir(plugins_dir):
                    d = os.path.join(plugins_dir, entry)
                    if os.path.isdir(d) and entry != os.path.basename(plugin_dir):
                        paths.append(os.path.join(d, "skills", skill_name, "SKILL.md"))
            except OSError:
                pass

        # 3. User config skills
        paths.append(os.path.join(home, ".gemini", "config", "skills", skill_name, "SKILL.md"))

        # 4. Builtin skills
        paths.append(
            os.path.join(home, ".gemini", "antigravity", "builtin", "skills", skill_name, "SKILL.md")
        )

        return paths

    def resolve_skill(
        self,
        skill_name: str,
        workspace_paths: list[str] | None = None,
        cwd: str | None = None,
    ) -> SkillDefinition | None:
        if not skill_name:
            return None

        wp_tuple = tuple(workspace_paths) if workspace_paths else ()
        cwd_str = cwd or ""
        cache_key = (skill_name, wp_tuple, cwd_str)

        if cache_key in self._cache:
            return self._cache[cache_key]

        search_paths = self.get_search_paths(skill_name, workspace_paths, cwd)
        for raw_path in search_paths:
            resolved = resolve_path(raw_path)
            if os.path.isfile(resolved):
                try:
                    with open(resolved, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    defn = SkillDefinition(name=skill_name, path=resolved, content=content)
                    self._cache[cache_key] = defn
                    return defn
                except OSError:
                    pass

        self._cache[cache_key] = None
        return None

    def format_instruction_block(
        self,
        skill_name: str,
        workspace_paths: list[str] | None = None,
        cwd: str | None = None,
    ) -> str | None:
        skill_def = self.resolve_skill(skill_name, workspace_paths, cwd)
        if not skill_def:
            return None
        content = skill_def.content.strip()
        return f"<skill-instruction>\n{content}\n</skill-instruction>"
