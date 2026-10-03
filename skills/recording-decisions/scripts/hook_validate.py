#!/usr/bin/env python3
"""PostToolUse hook: after an ADR or its index is written, refresh the index and check metadata."""

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
        files = [path]
    elif path.name == "README.md":
        files = []
    else:
        return 0
    adr.write_index(adr_dir)
    errors = adr.check(adr_dir, files=files)
    notes = adr.warnings(adr_dir, files=files)
    if errors:
        print("ADR check failed:\n" + "\n".join(errors + notes), file=sys.stderr)
        return 2
    if notes:
        context = "ADR warnings:\n" + "\n".join(notes)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse", "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
