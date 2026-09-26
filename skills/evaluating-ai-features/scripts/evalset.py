#!/usr/bin/env python3
"""Scaffold, check and gate eval sets for LLM steps (stdlib only)."""

from __future__ import annotations

import argparse
import csv
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


def load_cases(folder: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Header and non-blank rows of cases.csv; accepts Excel's ';' and BOM."""
    text = read(folder / "cases.csv")
    first = text.split("\n", 1)[0]
    delimiter = ";" if first.count(";") > first.count(",") else ","
    rows = list(csv.reader(text.splitlines(keepends=True), delimiter=delimiter))
    if not rows:
        return [], []
    header = [cell.strip() for cell in rows[0]]
    cases = [
        dict(zip(header, (cell.strip() for cell in row)), _width=str(len(row)))
        for row in rows[1:]
        if any(cell.strip() for cell in row)
    ]
    return header, cases


def examples(cases: list[dict[str, str]]) -> tuple[int, int]:
    """Distinct inputs, and how many of them come from a said case."""
    inputs = {case.get("input", "") for case in cases} - {""}
    said = {case.get("input", "") for case in cases if case.get("source") == "said"} - {""}
    return len(inputs), len(said)


def check(folder: Path) -> list[str]:
    meta, body = parse_front(read(folder / "plan.md"))
    found = []
    if not meta.get("name"):
        found.append("plan.md: name is empty")
    if meta.get("status") not in STATUSES:
        found.append(f"plan.md: status '{meta.get('status', '')}' not one of draft, ready")
    if not re.fullmatch(r"[1-9]\d*", meta.get("k", "")):
        found.append("plan.md: k must be an integer ≥ 1")
    criteria = table_rows(sections(body).get("Criteria", ""))
    if not criteria:
        found.append("plan.md: no criteria")
    ids = []
    for row in criteria:
        cid, text, grader, threshold = (row + ["", "", "", ""])[:4]
        ids.append(cid)
        if not cid or not text:
            found.append(f"plan.md: criterion '{cid}' needs an id and a text")
        if grader not in GRADERS:
            found.append(f"plan.md: {cid}: grader must be code or model")
        if not threshold:
            found.append(f"plan.md: {cid}: threshold is empty")

    header, cases = load_cases(folder)
    if header != HEADER:
        return found + [f"cases.csv: header must be {','.join(HEADER)}"]
    seen = set()
    for case in cases:
        cid = case["id"] or "?"
        if case.pop("_width") != str(len(HEADER)):
            found.append(f"cases.csv: case {cid}: needs {len(HEADER)} columns")
            continue
        if cid in seen:
            found.append(f"cases.csv: duplicate id {cid}")
        seen.add(cid)
        if case["criterion"] not in ids:
            found.append(f"cases.csv: case {cid}: unknown criterion {case['criterion']}")
        for field, allowed in (("source", SOURCES), ("kind", KINDS), ("grader", GRADERS)):
            if case[field] not in allowed:
                found.append(f"cases.csv: case {cid}: {field} must be {' or '.join(allowed)}")
        for field in ("input", "expected"):
            if not case[field]:
                found.append(f"cases.csv: case {cid}: {field} is empty")

    covered = {case.get("criterion") for case in cases}
    found += [f"coverage: {cid} has no cases" for cid in ids if cid and cid not in covered]
    # One input graded against several criteria is still one example.
    inputs, said = examples(cases)
    if inputs < MIN_CASES:
        found.append(f"count: {inputs} distinct inputs, need at least {MIN_CASES}")
    if said * 2 < inputs:
        found.append(f"said: {said} of {inputs} distinct inputs are real examples, need at least half")
    if not any(case.get("kind") == "refuse" for case in cases):
        found.append("refuse: no refuse case (an input the step must decline or flag)")
    return found


def set_status(folder: Path, target: str) -> None:
    if target == "ready":
        found = check(folder)
        if found:
            raise EvalError("cannot move to ready:\n" + "\n".join(found))
    path = folder / "plan.md"
    text = read(path)
    front = FRONT.match(text)
    if not front:
        raise EvalError("plan.md: missing frontmatter")
    head = re.sub(r"^status:.*$", f"status: {target}", front.group(0), count=1, flags=re.M)
    path.write_text(head + text[front.end() :])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evalset.py", description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_new = sub.add_parser("new", help="scaffold docs/evals/<slug>/plan.md and cases.csv")
    p_new.add_argument("title")
    p_new.add_argument("--canvas", type=Path)
    p_check = sub.add_parser("check", help="validate an eval set against the gate")
    p_check.add_argument("folder", type=Path)
    p_status = sub.add_parser("status", help="move an eval set to ready (if check passes) or draft")
    p_status.add_argument("folder", type=Path)
    p_status.add_argument("target", choices=STATUSES)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "new":
            print(new(args.root, args.title, args.canvas))
        elif args.cmd == "check":
            found = check(args.folder)
            if found:
                print("\n".join(found))
                return 1
            _, cases = load_cases(args.folder)
            inputs, said = examples(cases)
            print(f"eval set OK ({len(cases)} cases from {inputs} inputs, {said} real)")
        elif args.cmd == "status":
            set_status(args.folder, args.target)
            print(f"{args.folder}: {args.target}")
    except EvalError as exc:
        print(f"evalset.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
