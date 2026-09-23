"""Unit and integration tests for install.sh and install.ps1."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def get_working_bash():
    """Find a functional bash or sh executable, avoiding WSL stubs on Windows."""
    candidates = []
    if sys.platform == "win32":
        git_exe = shutil.which("git")
        if git_exe:
            git_root = Path(git_exe).resolve().parent.parent
            candidates.extend([
                git_root / "bin" / "bash.exe",
                git_root / "usr" / "bin" / "bash.exe",
                git_root / "usr" / "bin" / "sh.exe",
                git_root / "bin" / "sh.exe",
            ])
    for cmd in ["bash", "sh"]:
        p = shutil.which(cmd)
        if p and "System32" not in p and "system32" not in p:
            candidates.append(Path(p))

    for cand in candidates:
        if cand.is_file():
            try:
                r = subprocess.run(
                    [str(cand), "-c", "echo ok"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    check=False,
                )
                if r.returncode == 0 and "ok" in r.stdout:
                    return str(cand)
            except (subprocess.SubprocessError, OSError):
                pass
    return None


def test_installer_files_exist():
    """Verify install.sh and install.ps1 exist in repository root."""
    install_sh = REPO_ROOT / "install.sh"
    install_ps1 = REPO_ROOT / "install.ps1"

    assert install_sh.is_file(), "install.sh must exist at repo root"
    assert install_ps1.is_file(), "install.ps1 must exist at repo root"
    assert install_sh.stat().st_size > 500, "install.sh should not be empty"
    assert install_ps1.stat().st_size > 500, "install.ps1 should not be empty"


def test_install_sh_content_requirements():
    """Verify install.sh contains required configuration and logic."""
    content = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")

    assert "#!/bin/sh" in content
    assert ".gemini/config/plugins/oh-my-antigravity" in content
    assert "ANTIGRAVITY_PLUGINS_DIR" in content
    assert "3, 13" in content or "3.13" in content
    assert "uv" in content
    assert "git pull --ff-only" in content
    assert "git clone" in content
    assert "plugin.json" in content
    assert "hooks.json" in content
    assert "agy plugin list" in content


def test_install_ps1_content_requirements():
    """Verify install.ps1 contains required configuration and logic."""
    content = (REPO_ROOT / "install.ps1").read_text(encoding="utf-8")

    assert ".gemini\\config\\plugins\\oh-my-antigravity" in content or ".gemini" in content
    assert "ANTIGRAVITY_PLUGINS_DIR" in content
    assert "3, 13" in content or "3.13" in content
    assert "uv" in content
    assert "git pull --ff-only" in content
    assert "git clone" in content
    assert "plugin.json" in content
    assert "hooks.json" in content
    assert "agy plugin list" in content


def test_install_sh_syntax():
    """Check install.sh syntax using bash -n or sh -n if available."""
    bash_path = get_working_bash()
    if not bash_path:
        pytest.skip("Functional bash or sh not found on system to check syntax")

    res = subprocess.run(
        [bash_path, "-n", str(REPO_ROOT / "install.sh")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"install.sh syntax check failed: {res.stderr}"


def test_install_ps1_syntax():
    """Check install.ps1 syntax using PowerShell language parser."""
    pwsh_path = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh_path:
        pytest.skip("PowerShell not found on system to check syntax")

    check_code = (
        f"$scriptPath = '{REPO_ROOT / 'install.ps1'}'; "
        "$errors = $null; $tokens = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile($scriptPath, [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_.Message }; exit 1 } else { exit 0 }"
    )

    res = subprocess.run(
        [pwsh_path, "-NoProfile", "-Command", check_code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"install.ps1 syntax check failed: {res.stderr}"


def test_install_sh_idempotent_dry_run(tmp_path):
    """Test install.sh directory resolution and update logic in a simulated environment."""
    bash_path = get_working_bash()
    if not bash_path:
        pytest.skip("Functional bash or sh not available for execution smoke test")

    test_plugin_dir = tmp_path / "custom_plugins" / "oh-my-antigravity"
    test_plugin_dir.mkdir(parents=True)
    # Initialize mock git repo
    subprocess.run(["git", "init"], cwd=str(test_plugin_dir), check=True, capture_output=True)
    (test_plugin_dir / "plugin.json").write_text("{}", encoding="utf-8")
    (test_plugin_dir / "hooks.json").write_text("{}", encoding="utf-8")

    env = os.environ.copy()
    # In Git Bash on Windows, convert Windows path if necessary
    env["ANTIGRAVITY_PLUGINS_DIR"] = str(tmp_path / "custom_plugins").replace("\\", "/")

    # Run install.sh with mocked target dir
    res = subprocess.run(
        [bash_path, str(REPO_ROOT / "install.sh")],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    # The script should detect existing repo, verify files, and succeed
    assert res.returncode == 0, f"install.sh failed with stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    assert "Integrity check passed" in res.stdout
    assert "successfully installed" in res.stdout


def test_install_ps1_idempotent_dry_run(tmp_path):
    """Test install.ps1 directory resolution and update logic in a simulated environment."""
    pwsh_path = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh_path:
        pytest.skip("PowerShell not available for execution smoke test")

    test_plugin_dir = tmp_path / "custom_plugins" / "oh-my-antigravity"
    test_plugin_dir.mkdir(parents=True)
    # Initialize mock git repo
    subprocess.run(["git", "init"], cwd=str(test_plugin_dir), check=True, capture_output=True)
    (test_plugin_dir / "plugin.json").write_text("{}", encoding="utf-8")
    (test_plugin_dir / "hooks.json").write_text("{}", encoding="utf-8")

    env = os.environ.copy()
    env["ANTIGRAVITY_PLUGINS_DIR"] = str(tmp_path / "custom_plugins")

    res = subprocess.run(
        [pwsh_path, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(REPO_ROOT / "install.ps1")],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"install.ps1 failed with stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    assert "Integrity check passed" in res.stdout
    assert "successfully installed" in res.stdout
