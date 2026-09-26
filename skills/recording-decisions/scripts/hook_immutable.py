#!/usr/bin/env python3
"""PreToolUse hook: block body edits to decided (non-proposed) ADRs."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adr  # noqa: E402

ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def rejection(old: str, new: str, tool_input: dict, tool_name: str) -> str | None:
    """Why this change to a decided ADR is not allowed, or None if it is."""
    if tool_name != "Write" and tool_input.get("old_string", "") not in old:
        return "could not verify this edit (old_string not found verbatim)"
    if adr.status_kind(new) in ("", "proposed"):
        return "a decided ADR cannot go back to proposed"
    meta, _ = adr.split_frontmatter(new)
    for key in ("date", "review-by"):
        if key in meta and not ISO_DATE.fullmatch(meta[key]):
            return f"{key} must be YYYY-MM-DD"
    if adr.immutable_part(old) != adr.immutable_part(new):
        return "only status, date and review-by may change"
    return None


def main() -> int:
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    root = Path(event.get("cwd") or ".").resolve()
    path = Path(tool_input.get("file_path", ""))
    path = (path if path.is_absolute() else root / path).resolve()
    adr_dir = adr.adr_dir_for(path)
    if (
        adr_dir is None
        or path.parent != adr_dir
        or not adr.ADR_FILE.match(path.name)
        or not path.exists()
    ):
        return 0
    old = path.read_text()
    if adr.status_kind(old) in ("", "proposed"):
        return 0
    tool_name = event.get("tool_name", "")
    if tool_name == "Write":
        new = tool_input.get("content", "")
    else:
        before, after = (
            tool_input.get("old_string", ""),
            tool_input.get("new_string", ""),
        )
        new = (
            old.replace(before, after)
            if tool_input.get("replace_all")
            else old.replace(before, after, 1)
        )
    reason = rejection(old, new, tool_input, tool_name)
    if reason is None:
        return 0
    print(
        f"{path.name} is '{adr.get_status(old)}' and immutable: {reason}. "
        f'Record the change with: adr.py supersede {int(path.name[:4])} "<new decision>"',
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
