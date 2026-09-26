#!/usr/bin/env python3
"""Scaffold, check and gate eval sets for LLM steps (stdlib only)."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PLAN_TEMPLATE = SKILL_DIR / "templates" / "plan.md"
CASES_TEMPLATE = SKILL_DIR / "templates" / "cases.csv"
EVALS_DIR = "docs/evals"
HEADER = ["id", "criterion", "source", "kind", "input", "expected", "grader"]
STATUSES = ("draft", "ready")
SOURCES = ("said", "assumed")
KINDS = ("normal", "edge", "refuse")
GRADERS = ("code", "model")
MIN_CASES = 20
FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)
HEADING = re.compile(r"^## (.+?)[ \t]*$", re.M)
SEPARATOR = re.compile(r"^\|[\s|:-]+\|$")
PLACEHOLDER = re.compile(r"\{fill:[^{}\n]*\}")


class EvalError(Exception):
    """A user-facing error; main() prints it and exits 1."""


def slugify(title: str) -> str:
    ascii_title = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return slug[:60].rstrip("-") or "eval"


def read(path: Path) -> str:
    if not path.is_file():
        raise EvalError(f"{path}: no such file")
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def parse_front(text: str) -> tuple[dict[str, str], str]:
    match = FRONT.match(text)
    if not match:
        raise EvalError("missing frontmatter (--- block at the top)")
    meta = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return meta, text[match.end() :]


def sections(body: str) -> dict[str, str]:
    parts = HEADING.split(body)
    return dict(zip(parts[1::2], parts[2::2]))


def table_rows(section: str) -> list[list[str]]:
    """Cells of each markdown table row after the header row."""
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not (line.startswith("|") and line.endswith("|")) or SEPARATOR.match(line):
            continue
        cells = re.split(r"(?<!\\)\|", line[1:-1])
        rows.append([c.strip().replace("\\|", "/") for c in cells])
    return rows[1:]


def canvas_criteria(canvas: Path) -> list[str]:
    _, body = parse_front(read(canvas))
    rows = table_rows(sections(body).get("Success criteria", ""))
    found = [
        f"{metric}: {baseline} → {target}"
        for metric, baseline, target, *_ in (r + ["", "", ""] for r in rows)
        if metric and not PLACEHOLDER.search(metric + baseline + target)
    ]
    if not found:
        raise EvalError(f"{canvas}: no filled rows under ## Success criteria")
    return found


def new(root: Path, title: str, canvas: Path | None = None) -> Path:
    title = " ".join(title.split())
    if not title:
        raise EvalError("title is empty")
    criteria = canvas_criteria(canvas) if canvas else [""]
    folder = root / EVALS_DIR / slugify(title)
    if folder.exists():
        raise EvalError(f"{folder} already exists")
    folder.mkdir(parents=True)
    rows = "\n".join(
        f"| c{n} | {text.replace('|', '/')} |  |  |"
        for n, text in enumerate(criteria, start=1)
    )
    (folder / "plan.md").write_text(
        PLAN_TEMPLATE.read_text()
        .replace("{{name}}", title)
        .replace("{{canvas}}", str(canvas) if canvas else "")
        .replace("{{criteria}}", rows)
    )
    (folder / "cases.csv").write_text(CASES_TEMPLATE.read_text())
    return folder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evalset.py", description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_new = sub.add_parser("new", help="scaffold docs/evals/<slug>/plan.md and cases.csv")
    p_new.add_argument("title")
    p_new.add_argument("--canvas", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "new":
            print(new(args.root, args.title, args.canvas))
    except EvalError as exc:
        print(f"evalset.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
