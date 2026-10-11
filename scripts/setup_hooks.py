#!/usr/bin/env python3
"""Cross-platform hooks configuration generator for oh-my-antigravity.

Renders hooks.json from hooks.template.json by substituting {{PYTHON}} and {{PLUGIN_DIR}}.
Supports automated detection of Python 3.13+ runtime and normalization of paths across
Windows, Linux, and macOS.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def detect_python() -> str:
    """Detect an appropriate Python binary for running hooks.

    Prefers sys.executable if Python >= 3.13, otherwise searches PATH for python3 or python.
    """
    if sys.version_info >= (3, 13) and sys.executable:
        py_path = sys.executable.replace("\\", "/")
        if " " in py_path and not (py_path.startswith('"') and py_path.endswith('"')):
            return f'"{py_path}"'
        return py_path

    # Check python3 and python in PATH
    for candidate in ["python3", "python"]:
        p = shutil.which(candidate)
        if p:
            try:
                res = subprocess.run(
                    [p, "-c", "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)"],
                    capture_output=True,
                    check=False,
                )
                if res.returncode == 0:
                    return candidate
            except (subprocess.SubprocessError, OSError):
                pass

    return "python3" if sys.platform != "win32" else "python"


def normalize_dir_path(path: str | Path) -> str:
    """Normalize directory path with forward slashes and no trailing slash."""
    norm = str(Path(path).resolve()).replace("\\", "/")
    return norm.rstrip("/")


def render_hooks(
    plugin_dir: str | Path | None = None,
    python_cmd: str | None = None,
    template_name: str = "hooks.template.json",
    output_name: str = "hooks.json",
) -> Path:
    """Render hooks.json from template file.

    Args:
        plugin_dir: Root directory of the plugin. Defaults to parent of scripts/.
        python_cmd: Python executable or command string. Defaults to detected Python.
        template_name: Template filename (default hooks.template.json).
        output_name: Output filename (default hooks.json).

    Returns:
        Path to the generated hooks.json file.
    """
    if plugin_dir is None:
        # Default: os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    plugin_dir_path = Path(plugin_dir).resolve()
    norm_plugin_dir = normalize_dir_path(plugin_dir_path)

    if not python_cmd:
        python_cmd = detect_python()
    else:
        python_cmd = python_cmd.replace("\\", "/")
        if " " in python_cmd and not (python_cmd.startswith('"') and python_cmd.endswith('"')):
            python_cmd = f'"{python_cmd}"'

    template_path = plugin_dir_path / template_name
    if not template_path.is_file():
        raise FileNotFoundError(f"Hooks template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    rendered = (
        template_content
        .replace("{{PYTHON}}", python_cmd)
        .replace("{{PLUGIN_DIR}}", norm_plugin_dir)
    )

    # Validate JSON syntax
    try:
        parsed = json.loads(rendered)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Rendered hooks configuration is invalid JSON: {exc}") from exc

    # Validate required structure
    if "hooks" not in parsed:
        raise ValueError("Rendered hooks configuration missing top-level 'hooks' object")

    output_path = plugin_dir_path / output_name
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render hooks.json from hooks.template.json for cross-platform execution."
    )
    parser.add_argument(
        "--python",
        dest="python_cmd",
        default=None,
        help="Path or command for Python binary (default: auto-detected >= 3.13)",
    )
    parser.add_argument(
        "--plugin-dir",
        dest="plugin_dir",
        default=None,
        help="Path to oh-my-antigravity plugin root directory (default: auto-resolved)",
    )

    args = parser.parse_args()

    try:
        out_file = render_hooks(plugin_dir=args.plugin_dir, python_cmd=args.python_cmd)
        print(f"[setup_hooks] Successfully generated hooks config: {out_file}")
        return 0
    except Exception as err:  # noqa: BLE001
        sys.stderr.write(f"[setup_hooks] Error rendering hooks: {err}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
