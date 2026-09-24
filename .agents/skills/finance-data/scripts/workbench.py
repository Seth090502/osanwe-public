"""Locate the owning workspace/package runtime without copying its implementation."""
from pathlib import Path
import runpy
import sys

for root in Path(__file__).resolve().parents:
    runtime = root / "tools/fis/workbench.py"
    if runtime.is_file() and ((root / "AGENTS.md").is_file() or (root / ".codex-plugin/plugin.json").is_file()):
        sys.path.insert(0, str(runtime.parent))
        runpy.run_path(str(runtime), run_name="__main__")
        break
else:
    raise SystemExit("Osanwe runtime not found; use the complete workspace or verified portable package.")
