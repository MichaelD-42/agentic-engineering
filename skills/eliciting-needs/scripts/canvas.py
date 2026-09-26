#!/usr/bin/env python3
"""Scaffold, check, gate and render AI need canvases (stdlib only)."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "templates" / "need-canvas.md"
PAGE = SKILL_DIR / "templates" / "canvas.html"
NEEDS_DIR = "docs/needs"
SECTIONS = (
    "Original idea",
    "Actual need",
    "Actors",
    "As-is process",
    "Cost of the problem",
    "Success criteria",
    "Context diagram",
    "Solution mode",
    "Constraints and risks",
    "Open questions",
    "Roast",
    "Solution sketch",
)
SCORED = SECTIONS[1:9]
MUST_SCORE_2 = ("Actual need", "Success criteria", "Solution mode")
STATUSES = ("draft", "roasted", "approved", "shipped", "reviewed")
SHIPPED = ("shipped", "reviewed")
REVIEW_DAYS = 5
FOLLOW_UP = "Follow-up"
MODES = ("automate", "augment", "agent", "classic", "process-change", "dont-build")
NO_BUILD = ("process-change", "dont-build")
FIELDS = ("title", "date", "status", "owner", "mode")
PLACEHOLDER = re.compile(r"\{fill:[^{}\n]*\}")
FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)
HEADING = re.compile(r"^## (.+?)[ \t]*$", re.M)
MEASURE = re.compile(r"\d+(?:[.,]\d+)?[ \t]*(?:%|€|\$|[A-Za-z]+)")
SCORE_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([0-2])\s*\|", re.M)
VERDICT = re.compile(r"^Verdict:[ \t]*(pass|reroute|kill)\b", re.M | re.I)


class CanvasError(Exception):
    """A user-facing error; main() prints it and exits 1."""


def slugify(title: str) -> str:
    ascii_title = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return slug[:60].rstrip("-") or "need"


def read(path: Path) -> str:
    if not path.is_file():
        raise CanvasError(f"{path}: no such file")
    return path.read_text().replace("\r\n", "\n")


def valid_date(value: str) -> bool:
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def set_front(head: str, key: str, value: str) -> str:
    """Set key in a frontmatter block (--- … ---), adding the line if missing."""
    line = f"{key}: {value}"
    if re.search(rf"^{re.escape(key)}:", head, re.M):
        return re.sub(rf"^{re.escape(key)}:.*$", line, head, count=1, flags=re.M)
    return head[: head.rindex("---")] + line + "\n---\n"


def parse(text: str) -> tuple[dict[str, str], dict[str, str]]:
    match = FRONT.match(text)
    if not match:
        raise CanvasError("missing frontmatter (--- block at the top)")
    meta = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    parts = HEADING.split(text[match.end() :])
    return meta, dict(zip(parts[1::2], parts[2::2]))


def roast_problems(roast: str, mode: str) -> list[str]:
    scores = {name: int(score) for name, score in SCORE_ROW.findall(roast)}
    found = [f"Roast: no score for {name}" for name in SCORED if name not in scores]
    verdict = VERDICT.search(roast)
    if not verdict:
        return found + ["Roast: no 'Verdict: pass|reroute|kill' line"]
    match verdict.group(1).lower():
        case "reroute":
            found.append("Roast: verdict is reroute — change the mode and roast again")
        case "kill":
            if mode not in NO_BUILD:
                found.append(
                    "Roast: kill verdict needs mode process-change or dont-build"
                )
        case _:
            found += [f"Roast: {n} scored 0" for n in SCORED if scores.get(n) == 0]
            found += [
                f"Roast: {n} must score 2 to pass"
                for n in MUST_SCORE_2
                if scores.get(n, 2) < 2
            ]
    return found


FOLLOW_VERDICT = re.compile(r"^Verdict:[ \t]*(keep|iterate|retire|extend)\b", re.M | re.I)
EVAL_LINE = re.compile(r"^Eval pass rate:[ \t]*\S", re.M)


def table_cells(text: str) -> list[list[str]]:
    """Stripped cells of each markdown table row after the header and separator."""
    rows = [
        [cell.strip() for cell in line.strip()[1:-1].split("|")]
        for line in text.splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    return [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]


def follow_up_problems(sections: dict[str, str]) -> list[str]:
    text = sections.get(FOLLOW_UP)
    if text is None:
        return [f"missing section: ## {FOLLOW_UP}"]
    if PLACEHOLDER.search(text):
        return [f"{FOLLOW_UP}: unfilled {{fill: …}} placeholder"]
    rows = {cells[0]: cells for cells in table_cells(text)}
    found = []
    for metric in (r[0] for r in table_cells(sections["Success criteria"]) if r[0]):
        row = rows.get(metric)
        if row is None:
            found.append(f"{FOLLOW_UP}: no row for '{metric}'")
        elif len(row) < 4 or not row[3]:
            found.append(f"{FOLLOW_UP}: '{metric}' has no measured value")
    if not EVAL_LINE.search(text):
        found.append(f"{FOLLOW_UP}: no 'Eval pass rate:' line")
    verdict = FOLLOW_VERDICT.search(text)
    if not verdict:
        found.append(f"{FOLLOW_UP}: no 'Verdict: keep|iterate|retire' line")
    elif verdict.group(1).lower() == "extend":
        found.append(f"{FOLLOW_UP}: verdict extend — re-run status shipped --review-in DAYS")
    return found


def problems(meta: dict[str, str], sections: dict[str, str], status: str) -> list[str]:
    found = [f"frontmatter: missing '{f}'" for f in FIELDS if f not in meta]
    found += [f"missing section: ## {s}" for s in SECTIONS if s not in sections]
    if status not in STATUSES:
        found.append(f"status: '{status}' not one of {', '.join(STATUSES)}")
    mode = meta.get("mode", "")
    if mode and mode not in MODES:
        found.append(f"mode: '{mode}' not one of {', '.join(MODES)}")
    if found:
        return found
    sketch = sections["Solution sketch"]
    if status == "draft":
        if PLACEHOLDER.sub("", sketch).strip():
            found.append("Solution sketch: filled before the roast passed")
        return found
    for name in SECTIONS[:-1]:
        if PLACEHOLDER.search(sections[name]):
            found.append(f"{name}: unfilled {{fill: …}} placeholder")
    verdict = VERDICT.search(sections["Roast"])
    # A kill may rest on these very gaps (no owner, no measurable success).
    killed = bool(verdict) and verdict.group(1).lower() == "kill" and mode in NO_BUILD
    if not killed and not meta["owner"]:
        found.append("owner: empty — someone must own this after launch")
    if not mode:
        found.append("mode: not set")
    if not killed and not MEASURE.search(
        PLACEHOLDER.sub("", sections["Success criteria"])
    ):
        found.append("Success criteria: no number with a unit")
    found += roast_problems(sections["Roast"], mode)
    if status in ("approved", *SHIPPED) and (PLACEHOLDER.search(sketch) or not sketch.strip()):
        found.append("Solution sketch: not filled")
    if status in SHIPPED:
        if mode == "dont-build":
            found.append("mode: dont-build — nothing to ship")
        if not valid_date(meta.get("review-by", "")):
            found.append("review-by: missing or not a YYYY-MM-DD date")
    if status == "reviewed":
        found += follow_up_problems(sections)
    return found


def check(path: Path) -> list[str]:
    meta, sections = parse(read(path))
    return problems(meta, sections, meta.get("status", ""))


def set_status(
    path: Path, target: str, today: dt.date | None = None, review_in: int = REVIEW_DAYS
) -> None:
    text = read(path)
    meta, sections = parse(text)
    current = meta.get("status", "")
    if target == "shipped" and current not in ("approved", "shipped"):
        raise CanvasError(f"cannot move to shipped from {current}: approve it first")
    if target == "reviewed" and current != "shipped":
        raise CanvasError(f"cannot move to reviewed from {current}: ship it first")
    front = FRONT.match(text)
    head = front.group(0)
    if target == "shipped":
        due = ((today or dt.date.today()) + dt.timedelta(days=review_in)).isoformat()
        head = set_front(head, "review-by", due)
        meta["review-by"] = due
    found = problems(meta, sections, target)
    if found:
        raise CanvasError(f"cannot move to {target}:\n" + "\n".join(found))
    path.write_text(set_front(head, "status", target) + text[front.end() :])

def render(path: Path, out: Path | None = None) -> Path:
    text = read(path)
    meta, _ = parse(text)
    body = FRONT.sub("", text, count=1)
    summary = (
        f"status: {meta.get('status', '')} · mode: {meta.get('mode') or '—'}"
        f" · owner: {meta.get('owner') or '—'}"
    )
    page = (
        PAGE.read_text()
        .replace("{{title}}", html.escape(meta.get("title", "Need canvas")))
        .replace("{{meta}}", html.escape(summary))
        .replace("{{markdown_json}}", json.dumps(body).replace("<", "\\u003c"))
    )
    out = out or path.with_suffix(".html")
    out.write_text(page)
    return out


def new(root: Path, title: str, today: dt.date, owner: str = "") -> Path:
    title = " ".join(title.split())
    if not title:
        raise CanvasError("title is empty")
    folder = root / NEEDS_DIR / f"{today.isoformat()}-{slugify(title)}"
    if folder.exists():
        raise CanvasError(f"{folder} already exists")
    folder.mkdir(parents=True)
    text = (
        TEMPLATE.read_text()
        .replace("{{title}}", title)
        .replace("{{date}}", today.isoformat())
        .replace("{{owner}}", owner)
    )
    path = folder / "canvas.md"
    path.write_text(text)
    return path


def stale(root: Path, today: dt.date) -> list[str]:
    """Shipped canvases whose review is due, and unreadable review dates."""
    found = []
    for path in sorted((root / NEEDS_DIR).glob("*/canvas.md")):
        try:
            meta, _ = parse(read(path))
        except CanvasError:
            continue
        if meta.get("status") != "shipped":
            continue
        review = meta.get("review-by", "")
        name = path.relative_to(root)
        if not valid_date(review):
            found.append(f"{name}: unreadable review-by '{review}'")
        elif dt.date.fromisoformat(review) <= today:
            found.append(f"{name}: review due (review-by {review})")
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="canvas.py", description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_new = sub.add_parser("new", help="scaffold docs/needs/<date>-<slug>/canvas.md")
    p_new.add_argument("title")
    p_new.add_argument("--owner", default="")
    p_check = sub.add_parser("check", help="validate a canvas against its own status")
    p_check.add_argument("path", type=Path)
    p_status = sub.add_parser(
        "status", help="move a canvas to a status if it qualifies"
    )
    p_status.add_argument("path", type=Path)
    p_status.add_argument("target", choices=STATUSES)
    p_status.add_argument("--review-in", type=int, default=REVIEW_DAYS)
    sub.add_parser("stale", help="list shipped canvases whose review is due")
    p_render = sub.add_parser(
        "render", help="write a self-contained HTML page for the canvas"
    )
    p_render.add_argument("path", type=Path)
    p_render.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "new":
            print(new(args.root, args.title, args.today, args.owner))
        elif args.cmd == "check":
            found = check(args.path)
            print("\n".join(found) if found else "ok")
            return 1 if found else 0
        elif args.cmd == "status":
            set_status(args.path, args.target, args.today, args.review_in)
            print(f"{args.path}: {args.target}")
        elif args.cmd == "stale":
            found = stale(args.root, args.today)
            if found:
                print("\n".join(found))
        elif args.cmd == "render":
            print(render(args.path, args.out))
    except CanvasError as exc:
        print(f"canvas.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
