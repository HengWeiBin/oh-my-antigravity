from __future__ import annotations

import os
import re

from scripts.hooks.engine import BaseHook
from scripts.hooks.models import HookContext, HookResult
from scripts.hooks.skill_resolver import SkillResolver
from scripts.hooks.utils import extract_user_prompt

# Keyword → skill name mapping
KEYWORD_SKILLS: dict[str, str] = {
    "$start-work": "start-work",
    "$ultrawork": "ultrawork",
    "$ulw": "ultrawork",
    "$review-work": "review-work",
    "$hyperplan": "hyperplan",
    "$ulw-plan": "ulw-plan",
    "$ulw-research": "ulw-research",
    "$programming": "programming",
    "$frontend": "frontend",
    "$debugging": "debugging",
    "$init": "init",
}


# Forwarded report and quote markers
FORWARDED_START_RE = re.compile(
    r"^\s*(?:\[REPORT\]|\[[\w\-\s]+->[\w\-\s]+\])",
    re.IGNORECASE,
)
FORWARDED_MARKER_RE = re.compile(
    r"\[REPORT\]|\[[\w\-\s]+->[\w\-\s]+\]",
    re.IGNORECASE,
)

# Negation phrases preceding keyword (~20-30 chars on the same line)
ENGLISH_NEGATION = (
    r"\b(?:no|not|without|skip|(?:don['’]?t|do\s+not)\s+(?:use|run))\s+(?:the\s+|a\s+|any\s+)?"
)
CHINESE_NEGATION = (
    r"(?:不要使用|不使用|不要|別用|别用|別使用|别使用|不觸發|不触发|不用|忽略)\s*(?:這個|这个|此)?"
)
NEGATION_PATTERN = re.compile(
    rf"(?:{ENGLISH_NEGATION}|{CHINESE_NEGATION})\s*$",
    re.IGNORECASE,
)
KEYWORD_PATTERN = re.compile(r"(?<![a-zA-Z0-9_\-\$])\$([a-zA-Z0-9_\-]+)")


def format_skill_instruction(skill_name: str, skill_content: str) -> str:
    """Format skill content into <skill-instruction> block."""
    content = skill_content.strip()
    return f"<skill-instruction>\n{content}\n</skill-instruction>"


def get_keyword_detector_messages(payload: dict) -> list[dict]:
    """
    Detects special $keyword commands in the user prompt and triggers
    corresponding skill loading. Complements the existing /skill-name parsing.
    Filters out keywords within forwarded reports, blockquotes, or negated phrases.
    Returns list of {'ephemeralMessage': str} dicts.
    """
    prompt = extract_user_prompt(payload)
    if not prompt:
        return []

    # Entire prompt is a forwarded report
    if FORWARDED_START_RE.match(prompt):
        return []

    valid_keywords: list[str] = []
    in_forwarded_block = False

    for line in prompt.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Skip blockquote lines (starts with >)
        if stripped.startswith(">"):
            continue

        # Check for forwarded markers on this line
        if FORWARDED_MARKER_RE.search(stripped):
            in_forwarded_block = True
            continue

        # If inside a forwarded report section, ignore until boundary separator
        if in_forwarded_block:
            if stripped.startswith(("---", "===", "***")):
                in_forwarded_block = False
            continue

        # Extract keywords from line and filter out negated ones
        for m in KEYWORD_PATTERN.finditer(line):
            kw = f"${m.group(1)}"
            if kw not in KEYWORD_SKILLS:
                continue

            preceding = line[:m.start()]
            window = preceding[max(0, len(preceding) - 30):]
            if NEGATION_PATTERN.search(window):
                continue

            valid_keywords.append(kw)

    seen_skills: set[str] = set()
    messages: list[dict] = []

    plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    for keyword in valid_keywords:
        skill_name = KEYWORD_SKILLS.get(keyword)

        if not skill_name or skill_name in seen_skills:
            continue

        seen_skills.add(skill_name)

        skill_path = os.path.join(plugin_dir, "skills", skill_name, "SKILL.md")
        if os.path.isfile(skill_path):
            try:
                with open(skill_path, "r", encoding="utf-8") as f:
                    skill_content = f.read()
                formatted = format_skill_instruction(skill_name, skill_content)
                messages.append({"ephemeralMessage": formatted})
            except OSError:
                pass

    return messages


run_keyword_detector = get_keyword_detector_messages


class KeywordDetectorHook(BaseHook):
    def __init__(self, skill_resolver: SkillResolver | None = None) -> None:
        self.skill_resolver = skill_resolver or SkillResolver()

    @property
    def name(self) -> str:
        return "keyword_detector"

    def execute(self, context: HookContext) -> HookResult:
        messages = get_keyword_detector_messages(context.raw_payload)
        return HookResult(injected_steps=messages)
