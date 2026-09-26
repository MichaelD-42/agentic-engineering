#!/usr/bin/env python3
"""Manage MADR-style Architecture Decision Records (stdlib only)."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CANDIDATE_DIRS = ("docs/adr", "docs/decisions", "doc/architecture/decisions")
ADR_FILE = re.compile(r"^(\d{4})-.+\.md$")
STATUS = re.compile(
    r"^(?:proposed|accepted|rejected|deprecated|superseded by \[?(?:ADR-)?(\d+)\b.*)$",
    re.I,
)
SUPERSEDES = re.compile(r"^Supersedes \[(?:ADR-)?(\d+)\b", re.I | re.M)
NYGARD_STATUS = re.compile(r"^## Status[ \t]*\n(?:[ \t]*\n)*(.+)$", re.M)
PLACEHOLDER = re.compile(
    r"\{(?:list everyone|situation|concern|option \d|quality|downside|2-3 sentences|one line"
    r"|justification|positive consequence|negative consequence|decision driver \d|how compliance)[^{}\n]*\}"
)
INDEX_START, INDEX_END = "<!-- adr-index:start -->", "<!-- adr-index:end -->"


class AdrError(Exception):
    """A user-facing error; main() prints it and exits 1."""


def find_adr_dir(root: Path) -> Path | None:
    marker = root / ".adr-dir"
    if marker.is_file():
        return (root / marker.read_text().strip()).resolve()
    for rel in CANDIDATE_DIRS:
        if (root / rel).is_dir():
            return (root / rel).resolve()
    return None


def adr_dir_for(path: Path) -> Path | None:
    """The ADR directory containing path, found from the file's own ancestors (not the session cwd)."""
    for root in (path.parent, *path.parent.parents):
        if find_adr_dir(root) == path.parent:
            return path.parent
    return None


def require_adr_dir(root: Path) -> Path:
    adr_dir = find_adr_dir(root)
    if adr_dir is None or not adr_dir.is_dir():
        raise AdrError(
            f"no ADR directory under {root} (looked for .adr-dir, {', '.join(CANDIDATE_DIRS)})"
        )
    return adr_dir


def list_adrs(adr_dir: Path) -> list[tuple[int, Path]]:
    if not adr_dir.is_dir():
        return []
    return sorted(
        (int(m.group(1)), p)
        for p in adr_dir.iterdir()
        if p.is_file() and (m := ADR_FILE.match(p.name))
    )


def adr_path(adr_dir: Path, number: int) -> Path:
    for n, path in list_adrs(adr_dir):
        if n == number:
            return path
    raise AdrError(f"ADR-{number:04d} not found in {adr_dir}")


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 3)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "#")):
            meta[key.strip()] = value.strip().strip('"')
    return meta, text[end + 5 :]


def get_status(text: str) -> str | None:
    meta, _ = split_frontmatter(text)
    if "status" in meta:
        return meta["status"]
    m = NYGARD_STATUS.search(text)
    return m.group(1).strip() if m else None


def status_kind(text: str) -> str:
    return (get_status(text) or "").partition(" ")[0].lower()


def title_of(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return re.sub(r"^\d+\.\s+", "", line[2:].strip())
    return ""


def y_statement(text: str) -> str:
    _, body = split_frontmatter(text)
    for line in body.splitlines():
        if line.startswith("> "):
            return line[2:].strip()
    return ""


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60].rstrip("-")
    if not slug:
        raise AdrError(f"title {title!r} has no letters or digits")
    return slug


def load_template(adr_dir: Path, full: bool) -> str:
    for custom in (adr_dir / "templates" / "template.md", adr_dir / "template.md"):
        if custom.is_file():
            return custom.read_text()
    return (
        SKILL_DIR / "templates" / ("adr-full.md" if full else "adr-minimal.md")
    ).read_text()


def fill(template: str, number: int, title: str, date: str) -> str:
    if "{{title}}" in template:
        return (
            template.replace("{{number}}", f"{number:04d}")
            .replace("{{date}}", date)
            .replace("{{title}}", title)
        )
    # adr-tools token style; TITLE last so a title containing "DATE" survives
    for token, value in (
        ("NUMBER", str(number)),
        ("DATE", date),
        ("STATUS", "Proposed"),
        ("TITLE", title),
    ):
        template = template.replace(token, value)
    return template


def render_index(adr_dir: Path) -> str:
    rows = ["| ADR | Title | Status |", "| --- | --- | --- |"]
    for number, path in list_adrs(adr_dir):
        text = path.read_text()
        title = title_of(text).replace("|", "\\|")
        rows.append(
            f"| [{number:04d}]({path.name}) | {title} | {(get_status(text) or '?').replace('|', chr(92) + '|')} |"
        )
    return "\n".join(rows)


def write_index(adr_dir: Path) -> None:
    readme = adr_dir / "README.md"
    block = f"{INDEX_START}\n{render_index(adr_dir)}\n{INDEX_END}"
    if not readme.exists():
        readme.write_text(f"# Architecture Decision Records\n\n{block}\n")
        return
    text = readme.read_text()
    if INDEX_START in text and INDEX_END in text:
        before, _, rest = text.partition(INDEX_START)
        _, _, after = rest.partition(INDEX_END)
        readme.write_text(before + block + after)
    else:
        readme.write_text(text.rstrip("\n") + "\n\n" + block + "\n")


def new_adr(root: Path, title: str, full: bool, today: dt.date) -> Path:
    slug = slugify(title)
    adr_dir = find_adr_dir(root) or (root / CANDIDATE_DIRS[0])
    adr_dir.mkdir(parents=True, exist_ok=True)
    existing = list_adrs(adr_dir)
    number = (existing[-1][0] if existing else 0) + 1
    path = adr_dir / f"{number:04d}-{slug}.md"
    path.write_text(
        fill(load_template(adr_dir, full), number, title, today.isoformat())
    )
    write_index(adr_dir)
    return path


PARSER = argparse.ArgumentParser(prog="adr.py", description=__doc__)
PARSER.add_argument(
    "--root", type=Path, default=None, help="project root (default: cwd)"
)
PARSER.add_argument(
    "--today", type=dt.date.fromisoformat, default=None, help=argparse.SUPPRESS
)
SUBCOMMANDS = PARSER.add_subparsers(dest="cmd", required=True)


def arg(*flags, **kwargs):
    return flags, kwargs


def command(*arguments):
    def register(fn):
        sub = SUBCOMMANDS.add_parser(fn.__name__.removeprefix("cmd_"), help=fn.__doc__)
        for flags, kwargs in arguments:
            sub.add_argument(*flags, **kwargs)
        sub.set_defaults(handler=fn)
        return fn

    return register


@command(
    arg("title"),
    arg(
        "--full", action="store_true", help="full MADR template for contested decisions"
    ),
)
def cmd_new(args) -> int:
    """Create a proposed ADR from the template and update the index."""
    print(new_adr(args.root, args.title, args.full, args.today))
    return 0


@command()
def cmd_index(args) -> int:
    """Regenerate the README index table."""
    write_index(require_adr_dir(args.root))
    return 0


REVIEW_DAYS = 365


def set_field(text: str, key: str, value: str) -> str:
    """Set a front-matter field; Nygard files (no front matter) are returned unchanged."""
    end = text.find("\n---\n", 3) if text.startswith("---\n") else -1
    if end == -1:
        return text
    head, rest = text[:end], text[end:]
    line = f"{key}: {value}"
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.M)
    head = pattern.sub(lambda _: line, head, count=1) if pattern.search(head) else f"{head}\n{line}"
    return head + rest


def set_status(text: str, status: str) -> str:
    meta, _ = split_frontmatter(text)
    if meta:
        return set_field(text, "status", status)
    m = NYGARD_STATUS.search(text)
    if not m:
        raise AdrError("no 'status:' front matter or '## Status' section")
    return text[:m.start(1)] + status[0].upper() + status[1:] + text[m.end(1):]


def supersedes(text: str) -> set[int]:
    return {int(n) for n in SUPERSEDES.findall(text)}


def superseded_by(text: str) -> int | None:
    m = STATUS.match(get_status(text) or "")
    return int(m.group(1)) if m and m.group(1) else None


def add_supersedes(text: str, number: int, filename: str) -> str:
    lines = text.split("\n")
    title = next(i for i, line in enumerate(lines) if line.startswith("# "))
    lines[title + 1:title + 1] = ["", f"Supersedes [ADR-{number:04d}]({filename})"]
    return "\n".join(lines)


def accept(root: Path, number: int, today: dt.date) -> Path:
    adr_dir = require_adr_dir(root)
    path = adr_path(adr_dir, number)
    text = path.read_text()
    if status_kind(text) != "proposed":
        raise AdrError(f"{path.name} is '{get_status(text)}'; only proposed ADRs can be accepted")
    if PLACEHOLDER.search(text):
        raise AdrError(f"{path.name} still has template placeholders like {PLACEHOLDER.search(text).group(0)}")
    text = set_status(text, "accepted")
    text = set_field(text, "date", today.isoformat())
    text = set_field(text, "review-by", (today + dt.timedelta(days=REVIEW_DAYS)).isoformat())
    path.write_text(text)
    for old in supersedes(text):
        old_path = adr_path(adr_dir, old)
        old_path.write_text(set_status(old_path.read_text(), f"superseded by ADR-{number:04d}"))
    write_index(adr_dir)
    return path


@command(arg("number", type=int))
def cmd_accept(args) -> int:
    """Mark a proposed ADR accepted; flips any ADR it supersedes."""
    print(accept(args.root, args.number, args.today))
    return 0


@command(arg("number", type=int), arg("title"), arg("--full", action="store_true"))
def cmd_supersede(args) -> int:
    """Create a proposed ADR that supersedes NNNN (old flips on accept)."""
    old = adr_path(require_adr_dir(args.root), args.number)
    kind = status_kind(old.read_text())
    if kind == "superseded":
        raise AdrError(f"{old.name} is already superseded")
    if kind == "proposed":
        raise AdrError(f"{old.name} is only proposed; edit it instead of superseding")
    path = new_adr(args.root, args.title, args.full, args.today)
    path.write_text(add_supersedes(path.read_text(), args.number, old.name))
    print(path)
    return 0


MUTABLE_FIELDS = re.compile(r"^(?:status|date|review-by):.*\n", re.M)


def content_lines(text: str) -> int:
    _, body = split_frontmatter(text)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    return sum(1 for line in body.splitlines() if line.strip())


def immutable_part(text: str) -> str:
    """Text with the mutable fields removed, for comparing two versions of a decided ADR."""
    end = text.find("\n---\n", 3) if text.startswith("---\n") else -1
    if end != -1:
        return MUTABLE_FIELDS.sub("", text[:end + 1]) + text[end + 1:]
    m = NYGARD_STATUS.search(text)
    return text[:m.start(1)] + text[m.end(1):] if m else text


def committed_text(path: Path) -> str | None:
    result = subprocess.run(["git", "-C", str(path.parent), "show", f"HEAD:./{path.name}"],
                            capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def file_errors(path: Path, text: str) -> list[str]:
    name, status = path.name, get_status(text)
    if status is None:
        return [f"{name}: missing status ('status:' front matter or '## Status' section)"]
    errors = []
    if not STATUS.match(status):
        errors.append(f"{name}: invalid status '{status}'")
    meta, _ = split_frontmatter(text)
    if meta and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", meta.get("date", "")):
        errors.append(f"{name}: front matter needs date: YYYY-MM-DD")
    if not title_of(text):
        errors.append(f"{name}: missing '# ' title")
    kind = status_kind(text)
    if kind != "proposed" and PLACEHOLDER.search(text):
        errors.append(f"{name}: unfilled template placeholder in a {kind} ADR")
    cap = 90 if "## Pros and Cons of the Options" in text else 60
    if kind == "proposed" and (n := content_lines(text)) > cap:
        errors.append(f"{name}: {n} content lines exceeds cap of {cap}; move detail to the spec")
    old = committed_text(path)
    if old is not None and status_kind(old) not in ("", "proposed") and immutable_part(old) != immutable_part(text):
        errors.append(f"{name}: body of a {status_kind(old)} ADR changed since HEAD; supersede it instead")
    return errors


def link_errors(adrs: list[tuple[int, Path]], texts: dict[int, str]) -> list[str]:
    names = {number: path.name for number, path in adrs}
    errors = []
    for number, text in texts.items():
        newer = superseded_by(text)
        if newer is not None:
            if newer not in texts:
                errors.append(f"{names[number]}: superseded by missing ADR-{newer:04d}")
            elif number not in supersedes(texts[newer]):
                errors.append(f"{names[number]}: ADR-{newer:04d} does not say 'Supersedes ADR-{number:04d}'")
        for older in supersedes(text):
            if older not in texts:
                errors.append(f"{names[number]}: supersedes missing ADR-{older:04d}")
            elif status_kind(text) == "accepted" and superseded_by(texts[older]) != number:
                errors.append(f"{names[number]}: accepted and supersedes ADR-{older:04d}, "
                              f"but that ADR's status is not 'superseded by ADR-{number:04d}'")
    return errors


def index_errors(adr_dir: Path) -> list[str]:
    readme = adr_dir / "README.md"
    text = readme.read_text() if readme.exists() else ""
    if INDEX_START not in text or INDEX_END not in text:
        return ["README.md index missing; run: adr.py index"]
    current = text.partition(INDEX_START)[2].partition(INDEX_END)[0].strip()
    return [] if current == render_index(adr_dir) else ["README.md index out of date; run: adr.py index"]


def check(adr_dir: Path, files: list[Path] | None = None) -> list[str]:
    adrs = list_adrs(adr_dir)
    if not adrs:
        return []
    errors, texts, seen = [], {}, {}
    for number, path in adrs:
        if number in seen:
            errors.append(f"{path.name}: duplicate number {number:04d} (also {seen[number].name})")
        seen[number] = path
        texts[number] = path.read_text()
    targets = None if files is None else {f.resolve() for f in files}
    for number, path in adrs:
        if targets is None or path.resolve() in targets:
            errors += file_errors(path, path.read_text())
    return errors + link_errors(adrs, texts) + index_errors(adr_dir)


@command(arg("files", nargs="*", type=Path))
def cmd_check(args) -> int:
    """Validate ADR format, numbering, supersede links, index and immutability."""
    adr_dir = find_adr_dir(args.root)
    if adr_dir is None:
        print("no ADR directory; nothing to check")
        return 0
    errors = check(adr_dir, [f.resolve() for f in args.files] or None)
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print(f"ADR check passed ({len(list_adrs(adr_dir))} ADRs)")
    return 1 if errors else 0


DIGEST_CAP, DIGEST_WIDTH = 30, 240
PATH_REF = re.compile(r"`([A-Za-z0-9_.\-/]+)`")


def stale(adr_dir: Path, root: Path, today: dt.date) -> list[str]:
    """Review candidates: accepted ADRs past review-by, or citing slash-paths that no longer exist."""
    found = []
    for _, path in list_adrs(adr_dir):
        text = path.read_text()
        if status_kind(text) != "accepted":
            continue
        review = split_frontmatter(text)[0].get("review-by")
        if review:
            try:
                if dt.date.fromisoformat(review) < today:
                    found.append(f"{path.name}: review overdue (review-by {review})")
            except ValueError:
                found.append(f"{path.name}: unreadable review-by '{review}'")
        for ref in sorted(set(PATH_REF.findall(text))):
            if "/" in ref and not (root / ref).exists() and not (adr_dir / ref).exists():
                found.append(f"{path.name}: dead reference `{ref}`")
    return found


def digest(adr_dir: Path | None) -> str:
    if adr_dir is None:
        return ""
    lines = []
    for number, path in list_adrs(adr_dir):
        text = path.read_text()
        if status_kind(text) == "accepted":
            summary = y_statement(text)
            line = f"ADR-{number:04d} {title_of(text)}" + (f": {summary}" if summary else "")
            lines.append(line if len(line) <= DIGEST_WIDTH else line[:DIGEST_WIDTH - 1] + "…")
    if not lines:
        return ""
    shown = lines[:DIGEST_CAP]
    if len(lines) > DIGEST_CAP:
        shown.append(f"… and {len(lines) - DIGEST_CAP} more in {adr_dir / 'README.md'}")
    return f"Accepted decisions ({adr_dir}):\n" + "\n".join(shown)


@command()
def cmd_stale(args) -> int:
    """List accepted ADRs due for review; exit 1 when any are found."""
    adr_dir = find_adr_dir(args.root)
    found = stale(adr_dir, args.root, args.today) if adr_dir else []
    print("\n".join(found) if found else "no stale ADRs")
    return 1 if found else 0


@command()
def cmd_digest(args) -> int:
    """One line per accepted ADR, for loading decisions into context."""
    text = digest(find_adr_dir(args.root))
    if text:
        print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = PARSER.parse_args(argv)
    args.root = (args.root or Path.cwd()).resolve()
    args.today = args.today or dt.date.today()
    try:
        return args.handler(args)
    except AdrError as exc:
        print(f"adr.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
