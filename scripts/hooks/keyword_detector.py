from __future__ import annotations

import os
import re

from hooks.utils import extract_user_prompt

# Keyword → skill name mapping
KEYWORD_SKILLS: dict[str, str] = {
    '$start-work': 'start-work',
    '$ultrawork': 'ultrawork',
    '$ulw': 'ultrawork',
    '$review-work': 'review-work',
    '$hyperplan': 'hyperplan',
    '$ulw-plan': 'ulw-plan',
    '$ulw-research': 'ulw-research',
    '$programming': 'programming',
    '$frontend': 'frontend',
    '$debugging': 'debugging',
    '$init': 'init',
}


def format_skill_instruction(skill_name: str, skill_content: str) -> str:
    """Format skill content into <skill-instruction> block."""
    content = skill_content.strip()
    return f"<skill-instruction>\n{content}\n</skill-instruction>"


def get_keyword_detector_messages(payload: dict) -> list[dict]:
    """
    Detects special $keyword commands in the user prompt and triggers
    corresponding skill loading. Complements the existing /skill-name parsing.
    Returns list of {'ephemeralMessage': str} dicts.
    """
    prompt = extract_user_prompt(payload)
    if not prompt:
        return []

    matches = re.findall(r'(?:^|[^\w\-\$])\$([a-zA-Z0-9_\-]+)', prompt)
    
    seen_skills = set()
    messages = []
    
    plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    for match in matches:
        keyword = f'${match}'
        skill_name = KEYWORD_SKILLS.get(keyword)
        
        if not skill_name or skill_name in seen_skills:
            continue
            
        seen_skills.add(skill_name)
        
        skill_path = os.path.join(plugin_dir, 'skills', skill_name, 'SKILL.md')
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
