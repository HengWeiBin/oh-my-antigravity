"""Comprehensive release-readiness verification suite for oh-my-antigravity v0.1.0.

Validates:
1. Manifest & Config integrity (plugin.json, hooks.json, pyproject.toml).
2. Vector Assets compliance (assets/logo.svg, assets/banner.svg).
3. Installer scripts robustness (install.sh, install.ps1).
4. Documentation & Community suite completeness (bilingual READMEs, CONTRIBUTING.md,
   LICENSE attribution, GitHub templates, link validation, 11 agents, 42 skills).
"""

import json
import re
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

EXPECTED_11_AGENTS = {
    "atlas",
    "explore",
    "hephaestus",
    "librarian",
    "metis",
    "momus",
    "multimodal-looker",
    "oracle",
    "prometheus",
    "sisyphus",
    "sisyphus-junior",
}

EXPECTED_42_SKILLS = [
    "hyperplan",
    "ulw-plan",
    "teammode",
    "domain-modeling",
    "codebase-design",
    "start-work",
    "programming",
    "refactor",
    "remove-ai-slops",
    "remove-deadcode",
    "ast-grep",
    "tdd",
    "prototype",
    "visual-qa",
    "review-work",
    "pre-publish-review",
    "debugging",
    "diagnosing-bugs",
    "comment-checker",
    "agent-browser",
    "dev-browser",
    "ultimate-browsing",
    "playwright-cli",
    "git-master",
    "git-sync-upstream",
    "github-triage",
    "work-with-pr",
    "publish",
    "whats-new",
    "get-unpublished-changes",
    "antigravity-hooks",
    "antigravity-subagents",
    "lsp",
    "lsp-setup",
    "rules",
    "init",
    "init-deep",
    "call-atlas",
    "call-prometheus",
    "coding-agent-sessions",
    "security-research",
    "tech-debt-audit",
]


# ==============================================================================
# a) Manifest & Config Validation
# ==============================================================================


def test_manifest_plugin_json():
    """Verify plugin.json schema, identity, version, and logo resolution."""
    manifest_path = REPO_ROOT / "plugin.json"
    assert manifest_path.is_file(), "plugin.json must exist at repo root"

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data.get("name") == "oh-my-antigravity", "Plugin name must be 'oh-my-antigravity'"
    assert data.get("version") == "0.1.0", "Plugin version must be '0.1.0'"
    assert data.get("description"), "Plugin must contain a non-empty description"

    logo_rel = data.get("logo")
    assert logo_rel == "assets/logo.svg", "Logo path must be 'assets/logo.svg'"
    logo_file = REPO_ROOT / logo_rel
    assert logo_file.is_file(), f"Referenced logo file does not exist: {logo_file}"
    assert logo_file.stat().st_size > 0, "Referenced logo file must not be empty"


def test_manifest_hooks_json():
    """Verify hooks.json structure and standard interceptor registrations."""
    hooks_path = REPO_ROOT / "hooks.json"
    assert hooks_path.is_file(), "hooks.json must exist at repo root"

    data = json.loads(hooks_path.read_text(encoding="utf-8"))
    assert "hooks" in data, "hooks.json must contain top-level 'hooks' key"
    hooks = data["hooks"]

    # Must contain standard hook phases
    for phase in ["PreInvocation", "PreToolUse", "PostToolUse", "Stop"]:
        assert phase in hooks, f"Missing required hook phase: {phase}"

    # Verify script targets exist
    for phase, hook_list in hooks.items():
        assert isinstance(hook_list, list), f"Phase {phase} hooks must be a list"
        for item in hook_list:
            if "command" in item:
                cmd_parts = item["command"].split()
                if len(cmd_parts) >= 2 and cmd_parts[0] == "python":
                    script_path = REPO_ROOT / cmd_parts[1]
                    assert script_path.is_file(), f"Hook script does not exist: {script_path}"


def test_manifest_pyproject_toml():
    """Verify pyproject.toml metadata, version, and python requirement."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    assert pyproject_path.is_file(), "pyproject.toml must exist at repo root"

    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    assert project.get("name") == "oh-my-antigravity", "Project name must match"
    assert project.get("version") == "0.1.0", "Project version must be '0.1.0'"
    assert ">=3.13" in project.get("requires-python", ""), "Python 3.13+ required"


# ==============================================================================
# b) Vector Assets Validation
# ==============================================================================


def test_vector_asset_logo():
    """Verify assets/logo.svg XML well-formedness, dimensions, and viewBox."""
    logo_path = REPO_ROOT / "assets" / "logo.svg"
    assert logo_path.is_file(), "assets/logo.svg must exist"
    assert logo_path.stat().st_size > 0, "assets/logo.svg must not be empty"

    tree = ET.parse(logo_path)
    root = tree.getroot()
    assert root.tag.endswith("svg"), "Root tag must be svg"
    assert root.attrib.get("viewBox") == "0 0 256 256", "Logo viewBox must be '0 0 256 256'"
    assert root.attrib.get("width") == "256", "Logo width must be '256'"
    assert root.attrib.get("height") == "256", "Logo height must be '256'"

    content = logo_path.read_text(encoding="utf-8")
    for color in ["#6366F1", "#06B6D4", "#8B5CF6"]:
        assert color in content, f"Missing brand color {color} in logo.svg"


def test_vector_asset_banner():
    """Verify assets/banner.svg XML well-formedness, dimensions, and text badges."""
    banner_path = REPO_ROOT / "assets" / "banner.svg"
    assert banner_path.is_file(), "assets/banner.svg must exist"
    assert banner_path.stat().st_size > 0, "assets/banner.svg must not be empty"

    tree = ET.parse(banner_path)
    root = tree.getroot()
    assert root.tag.endswith("svg"), "Root tag must be svg"
    assert root.attrib.get("viewBox") == "0 0 1200 360", "Banner viewBox must be '0 0 1200 360'"
    assert root.attrib.get("width") == "1200", "Banner width must be '1200'"
    assert root.attrib.get("height") == "360", "Banner height must be '360'"

    content = banner_path.read_text(encoding="utf-8")
    for text_token in [
        "OH-MY-ANTIGRAVITY",
        "Google Antigravity 2.0",
        "11 Orchestrated Agents",
        "42 Bundled Skills",
        "Python 3.13",
    ]:
        assert text_token in content, f"Missing banner label '{text_token}'"


# ==============================================================================
# c) Installer Scripts Validation
# ==============================================================================


def test_installer_scripts_validation():
    """Verify install.sh and install.ps1 exist, non-empty, and check Python 3.13 and paths."""
    install_sh = REPO_ROOT / "install.sh"
    install_ps1 = REPO_ROOT / "install.ps1"

    assert install_sh.is_file(), "install.sh must exist"
    assert install_ps1.is_file(), "install.ps1 must exist"
    assert install_sh.stat().st_size > 500, "install.sh must be populated"
    assert install_ps1.stat().st_size > 500, "install.ps1 must be populated"

    sh_content = install_sh.read_text(encoding="utf-8")
    ps1_content = install_ps1.read_text(encoding="utf-8")

    # Target directory verification
    assert "ANTIGRAVITY_PLUGINS_DIR" in sh_content
    assert ".gemini/config/plugins/oh-my-antigravity" in sh_content
    assert "ANTIGRAVITY_PLUGINS_DIR" in ps1_content
    assert ".gemini" in ps1_content

    # Python 3.13 validation
    assert ("3.13" in sh_content) or ("3, 13" in sh_content), "install.sh must check Python 3.13"
    assert ("3.13" in ps1_content) or ("3, 13" in ps1_content), "install.ps1 must check Python 3.13"

    # uv package manager validation
    assert "uv" in sh_content
    assert "uv" in ps1_content


# ==============================================================================
# d) Documentation & Community Suite Validation
# ==============================================================================


def test_documentation_and_community_files_exist():
    """Verify all key documentation, license, and GitHub community files exist and are non-empty."""
    required_files = [
        "README.md",
        "README.zh-TW.md",
        "CONTRIBUTING.md",
        "LICENSE",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
    ]

    for rel_path in required_files:
        file_path = REPO_ROOT / rel_path
        assert file_path.is_file(), f"Required community/doc file missing: {rel_path}"
        assert file_path.stat().st_size > 50, f"File appears unexpectedly empty: {rel_path}"


def test_license_upstream_attribution():
    """Verify LICENSE contains valid MIT terms and attribution to code-yeongyu/oh-my-openagent."""
    license_path = REPO_ROOT / "LICENSE"
    content = license_path.read_text(encoding="utf-8")

    assert "MIT License" in content
    assert "code-yeongyu/oh-my-openagent" in content, "LICENSE must attribute upstream oh-my-openagent"
    assert "HengWeiBin" in content, "LICENSE must include current maintainer copyright"


def test_markdown_relative_links_and_images_integrity():
    """Verify relative links and images in core documentation files resolve to real paths."""
    link_pattern = re.compile(r"\[.*?\]\((?!https?://|mailto:|file://|#)(.*?)\)")
    img_pattern = re.compile(r"!\[.*?\]\((?!https?://|mailto:|file://)(.*?)\)")

    doc_files = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "README.zh-TW.md",
        REPO_ROOT / "CONTRIBUTING.md",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md",
    ]
    if (REPO_ROOT / "docs").is_dir():
        doc_files.extend((REPO_ROOT / "docs").rglob("*.md"))

    for doc_file in doc_files:
        if not doc_file.is_file():
            continue
        text = doc_file.read_text(encoding="utf-8", errors="ignore")
        urls = link_pattern.findall(text) + img_pattern.findall(text)
        for raw_url in urls:
            clean_url = raw_url.split("#")[0].strip()
            if not clean_url:
                continue
            # Resolve relative to current doc file or repo root
            if clean_url.startswith("/"):
                target = (REPO_ROOT / clean_url.lstrip("/")).resolve()
            else:
                target = (doc_file.parent / clean_url).resolve()

            assert target.exists(), (
                f"Broken link '{raw_url}' in {doc_file.relative_to(REPO_ROOT)}: "
                f"Resolved target '{target}' does not exist on disk."
            )


def test_all_11_agent_profiles():
    """Verify all 11 agent profile files exist in agents/ with matching frontmatter declarations."""
    agents_dir = REPO_ROOT / "agents"
    assert agents_dir.is_dir(), "agents directory must exist"

    agent_files = list(agents_dir.glob("*.md"))
    agent_names = {f.stem for f in agent_files}
    assert agent_names == EXPECTED_11_AGENTS, (
        f"Agents mismatch! Difference: {agent_names.symmetric_difference(EXPECTED_11_AGENTS)}"
    )

    for agent_file in agent_files:
        content = agent_file.read_text(encoding="utf-8")
        assert content.startswith("---"), f"{agent_file.name} must start with YAML frontmatter"
        assert f"name: {agent_file.stem}" in content, (
            f"Agent {agent_file.name} frontmatter 'name' must match filename stem"
        )
        assert agent_file.stat().st_size > 1000, f"Agent profile {agent_file.name} must be substantial"


def test_all_42_skills_catalog_and_filesystem():
    """Verify all 42 skills are cataloged in READMEs and all skills on disk are well-formed."""
    assert len(EXPECTED_42_SKILLS) == 42, "Must declare exactly 42 skills"

    en_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    zh_readme = (REPO_ROOT / "README.zh-TW.md").read_text(encoding="utf-8")

    # 1. Verify 42 skills cataloged in both bilingual READMEs
    for readme_content, name in [(en_readme, "README.md"), (zh_readme, "README.zh-TW.md")]:
        for skill in EXPECTED_42_SKILLS:
            assert f"/{skill}" in readme_content, f"Missing trigger /{skill} in {name}"
            assert f"`{skill}`" in readme_content, f"Missing skill `{skill}` in {name}"

    # 2. Verify all skill directories under skills/ have a valid, non-empty SKILL.md
    skills_dir = REPO_ROOT / "skills"
    assert skills_dir.is_dir(), "skills/ directory must exist"

    skill_folders = [d for d in skills_dir.iterdir() if d.is_dir()]
    assert len(skill_folders) >= 40, f"Expected at least 40 skill folders in skills/, found {len(skill_folders)}"

    for folder in skill_folders:
        skill_md = folder / "SKILL.md"
        assert skill_md.is_file(), f"Missing SKILL.md in {folder.name}"
        assert skill_md.stat().st_size > 0, f"Empty SKILL.md in {folder.name}"
        first_lines = skill_md.read_text(encoding="utf-8", errors="ignore").splitlines()[:10]
        full_head = "\n".join(first_lines)
        assert f"name: {folder.name}" in full_head, (
            f"SKILL.md in {folder.name} frontmatter 'name' must match folder name"
        )
