"""Tests for README.md and README.zh-TW.md documentation integrity."""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def english_readme():
    path = REPO_ROOT / "README.md"
    assert path.is_file(), "README.md must exist"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def chinese_readme():
    path = REPO_ROOT / "README.zh-TW.md"
    assert path.is_file(), "README.zh-TW.md must exist"
    return path.read_text(encoding="utf-8")


def test_readme_files_exist_and_populated():
    """Verify both documentation files exist and are substantial."""
    en_path = REPO_ROOT / "README.md"
    zh_path = REPO_ROOT / "README.zh-TW.md"

    assert en_path.is_file()
    assert zh_path.is_file()
    assert en_path.stat().st_size > 3000, "README.md must be populated"
    assert zh_path.stat().st_size > 3000, "README.zh-TW.md must be populated"


def test_hero_banner_and_language_switch(english_readme, chinese_readme):
    """Verify hero banner and language switch bar in both READMEs."""
    for content in [english_readme, chinese_readme]:
        assert "![Oh-My-Antigravity](assets/banner.svg)" in content
        assert "[English](README.md)" in content
        assert "[繁體中文](README.zh-TW.md)" in content


def test_badges_present(english_readme, chinese_readme):
    """Verify all 5 required shields.io badges are present."""
    required_badge_snippets = [
        "badge/Antigravity-2.22.0%2B-blue",
        "badge/Python-3.13%2B-blue",
        "badge/License-MIT-green",
        "badge/Tests-Passing-brightgreen",
        "badge/Release-v0.2.0-orange",
    ]
    for content in [english_readme, chinese_readme]:
        for snippet in required_badge_snippets:
            assert snippet in content, f"Missing badge snippet: {snippet}"


def test_mermaid_diagrams_present(english_readme, chinese_readme):
    """Verify Mermaid flowchart and sequence diagram are present and well-formed."""
    for content in [english_readme, chinese_readme]:
        assert "```mermaid" in content
        assert "flowchart TD" in content
        assert "sequenceDiagram" in content


def test_all_11_agents_roster(english_readme, chinese_readme):
    """Verify all 11 agents are listed in both README rosters."""
    agents = [
        "sisyphus",
        "atlas",
        "prometheus",
        "metis",
        "momus",
        "hephaestus",
        "sisyphus-junior",
        "explore",
        "librarian",
        "oracle",
        "multimodal-looker",
    ]
    for content in [english_readme, chinese_readme]:
        for agent in agents:
            assert f"`{agent}`" in content, f"Missing agent {agent} in documentation"


def test_all_43_skills_catalog(english_readme, chinese_readme):
    """Verify all 43 skills are cataloged in both READMEs with slash triggers."""
    skills = [
        "agent-browser",
        "antigravity-hooks",
        "antigravity-subagents",
        "ast-grep",
        "call-atlas",
        "call-prometheus",
        "coding-agent-sessions",
        "comment-checker",
        "data-scientist",
        "debugging",
        "dev-browser",
        "frontend",
        "get-unpublished-changes",
        "git-master",
        "github-triage",
        "hyperplan",
        "init",
        "init-deep",
        "lsp",
        "lsp-setup",
        "omomomo",
        "pi-goal",
        "pre-publish-review",
        "programming",
        "publish",
        "refactor",
        "remove-ai-slops",
        "remove-deadcode",
        "review-work",
        "rules",
        "security-research",
        "start-work",
        "teammode",
        "tech-debt-audit",
        "ultimate-browsing",
        "ultraresearch",
        "ultrawork",
        "ulw-loop",
        "ulw-plan",
        "ulw-research",
        "visual-qa",
        "visualize",
        "work-with-pr",
    ]
    assert len(skills) == 43
    for content in [english_readme, chinese_readme]:
        for skill in skills:
            assert f"/{skill}" in content, f"Missing slash trigger /{skill}"
            assert f"`{skill}`" in content, f"Missing skill identifier `{skill}`"


test_all_42_skills_catalog = test_all_43_skills_catalog


def test_installation_methods(english_readme, chinese_readme):
    """Verify all 3 prominent installation methods are detailed."""
    for content in [english_readme, chinese_readme]:
        assert "agy plugin install https://github.com/HengWeiBin/oh-my-antigravity.git" in content
        assert "install.sh" in content
        assert "install.ps1" in content
        assert "~/.gemini/config/plugins/oh-my-antigravity" in content


def test_attribution_and_license(english_readme, chinese_readme):
    """Verify upstream attribution to code-yeongyu/oh-my-openagent and MIT license."""
    for content in [english_readme, chinese_readme]:
        assert "code-yeongyu/oh-my-openagent" in content
        assert "LICENSE" in content
        assert "CONTRIBUTING.md" in content


def test_relative_markdown_links_valid():
    """Verify all relative markdown links in README.md and README.zh-TW.md point to real files."""
    link_pattern = re.compile(r'\[.*?\]\((?!http[s]?://)(.*?)\)')
    image_pattern = re.compile(r'!\[.*?\]\((?!http[s]?://)(.*?)\)')

    for readme_name in ["README.md", "README.zh-TW.md"]:
        file_path = REPO_ROOT / readme_name
        content = file_path.read_text(encoding="utf-8")

        links = link_pattern.findall(content) + image_pattern.findall(content)
        for link in links:
            # Strip anchor if present
            clean_link = link.split("#")[0]
            if not clean_link:
                continue
            target = (REPO_ROOT / clean_link).resolve()
            assert target.exists(), f"Broken relative link in {readme_name}: {link} (resolved to {target})"
