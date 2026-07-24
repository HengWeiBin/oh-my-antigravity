from __future__ import annotations
import re

# Required sections for a valid plan
REQUIRED_SECTIONS = [
    '## TL;DR',
    '## Todos',
    '## Dependency Matrix',
]

def check_plan_format(tool_name: str, tool_input: dict, tool_response: dict | None) -> str | None:
    """
    After writing to .omo/plans/, validates plan format.
    Returns feedback string if plan is malformed.
    Returns None if valid or not a plan file.
    """
    if tool_name not in ['write_to_file', 'replace_file_content', 'multi_replace_file_content']:
        return None

    target_file = tool_input.get('TargetFile', '')
    if not target_file:
        return None

    # Normalize path to use forward slashes for easier checking
    normalized_path = target_file.replace('\\', '/')
    if '.omo/plans/' not in normalized_path or not normalized_path.endswith('.md'):
        return None

    content = ""
    if tool_name == 'write_to_file':
        content = tool_input.get('CodeContent', '')
    else:
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None

    missing_sections = []
    content_lower = content.lower()

    for section in REQUIRED_SECTIONS:
        if section.lower() not in content_lower:
            missing_sections.append(section)

    if '## Todos' not in missing_sections:
        # Extract Todos section to check for checkboxes
        todos_match = re.search(r'## todos\s*(.*?)(?=\n## |\Z)', content, re.IGNORECASE | re.DOTALL)
        if todos_match:
            todos_content = todos_match.group(1)
            if '- [ ]' not in todos_content:
                missing_sections.append('Checkboxes (at least one `- [ ]`) in Todos')
        else:
            if '- [ ]' not in content:
                missing_sections.append('Checkboxes (at least one `- [ ]`) in Todos')

    if missing_sections:
        missing_str = ', '.join(missing_sections)
        return (
            f"📋 PLAN FORMAT VALIDATOR: The plan file is missing required sections.\n\n"
            f"Missing: {missing_str}\n\n"
            f"Required format:\n"
            f"## TL;DR\n"
            f"(Brief summary)\n\n"
            f"## Todos\n"
            f"- [ ] Task 1\n\n"
            f"## Dependency Matrix\n"
            f"(Dependencies between tasks)"
        )

    return None

run_plan_format_validator = check_plan_format
