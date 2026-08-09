from __future__ import annotations

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
plugin_root = os.path.dirname(script_dir)
if plugin_root not in sys.path:
    sys.path.insert(0, plugin_root)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from scripts.hooks.engine import HookEngine, LifecycleEvent


def main() -> int:
    return HookEngine.run(LifecycleEvent.POST_TOOL_USE, sys.stdin)


if __name__ == "__main__":
    sys.exit(main())
