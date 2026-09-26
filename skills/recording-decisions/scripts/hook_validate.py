#!/usr/bin/env python3
"""PostToolUse hook: validate the ADR directory after an ADR or its index is written."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adr  # noqa: E402


def main() -> int:
    event = json.load(sys.stdin)
    root = Path(event.get("cwd") or ".").resolve()
    path = Path(event.get("tool_input", {}).get("file_path", ""))
    path = (path if path.is_absolute() else root / path).resolve()
    adr_dir = adr.adr_dir_for(path)
    if adr_dir is None or path.parent != adr_dir:
        return 0
    if adr.ADR_FILE.match(path.name):
        errors = adr.check(adr_dir, files=[path])
    elif path.name == "README.md":
        errors = adr.check(adr_dir, files=[])
    else:
        return 0
    if not errors:
        return 0
    print("ADR check failed:\n" + "\n".join(errors), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
