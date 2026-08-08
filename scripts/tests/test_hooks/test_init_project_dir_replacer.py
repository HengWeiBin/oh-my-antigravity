from unittest.mock import mock_open, patch

from hooks.init_project_dir_replacer import (
    get_project_dir,
    run_init_project_dir_replacer,
)


def test_get_project_dir_workspace_paths():
    payload = {"workspacePaths": ["C:/workspace/my-repo"], "cwd": "C:/workspace/other"}
    project_dir = get_project_dir(payload)
    assert "my-repo" in project_dir.replace("\\", "/")


def test_init_skill_replacer_replaces_project_dir():
    payload = {
        "prompt": "Please /init for this repo",
        "workspacePaths": ["C:/workspace/my-repo"]
    }
    mock_skill_content = "Create AGENTS.md at {project_dir}/AGENTS.md"

    with patch("os.path.isfile", return_value=True), patch("builtins.open", mock_open(read_data=mock_skill_content)):
        msgs = run_init_project_dir_replacer(payload)
        assert len(msgs) == 1
        assert "my-repo" in msgs[0]["ephemeralMessage"]
        assert "{project_dir}" not in msgs[0]["ephemeralMessage"]
        assert "<skill-instruction>" in msgs[0]["ephemeralMessage"]


def test_init_skill_replacer_ignored_when_no_init():
    payload = {
        "prompt": "Just normal work here",
        "workspacePaths": ["C:/workspace/my-repo"]
    }
    msgs = run_init_project_dir_replacer(payload)
    assert len(msgs) == 0
