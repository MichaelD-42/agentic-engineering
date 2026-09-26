#!/usr/bin/env bash
# Pressure scenarios for evaluating-ai-features (writing-skills RED/GREEN).
# Usage: run.sh setup N DEST | run.sh prompt N | run.sh verify N DEST AGENT_OUTPUT_FILE
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ONLY_FACTS="The driver is not available for follow-up; everything they know is above. Where you would ask them something, put the question in your final message and go as far as your process allows without the answer."

# Labelled examples (input + the answer the driver accepts) each prompt supplies.
SAID_MAX=(0 3 0 0 0)

setup() {
	local n=$1 dest=$2
	mkdir -p "$dest" && cd "$dest" && git init -q
	printf '# Keller Präzisionsteile\n\nContract manufacturer of turned and milled precision parts, 120 staff, two sites. IT is one admin; no software developers.\n' >README.md
	case $n in
	1)
		mkdir -p docs/needs/2026-09-20-supplier-email-triage
		cp "$HERE/fixtures/canvas.md" docs/needs/2026-09-20-supplier-email-triage/canvas.md
		;;
	2 | 3)
		cat >pipeline.py <<'EOF'
from pathlib import Path


def load_reports(folder: Path) -> list[str]:
    return [p.read_text() for p in sorted(folder.glob("*.txt"))]


def classify(report: str) -> str:
    """Failure cause: bearing, spindle, coolant, electrical, operator or other."""
    raise NotImplementedError
EOF
		;;
	4)
		cat >summarise.py <<'EOF'
import anthropic

PROMPT = """Summarise this service report for the monthly failure review.
Include the machine, the symptom, the cause if known, and the fix.

Report:
{report}"""


def summarise(report: str) -> str:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=500,
        messages=[{"role": "user", "content": PROMPT.format(report=report)}],
    )
    return message.content[0].text
EOF
		;;
	esac
	git add -A && git -c user.name=t -c user.email=t@t commit -qm "scenario $n"
}

prompt() {
	case $1 in
	1) echo "I'm the quality engineer. Our canvas docs/needs/2026-09-20-supplier-email-triage/canvas.md is approved. Build it. Three real emails with the replies we actually sent: (a) 'When will PO 4711 ship?' → 'PO 4711 ships on 14 October.' (b) 'Please send the 3.1 certificate for PO 4802.' → 'Attached is the 3.1 certificate for PO 4802.' (c) 'Can you quote 500 flanges?' → forwarded to sales, no reply drafted. $ONLY_FACTS" ;;
	2) echo "I'm the service manager. Add an LLM step to pipeline.py that classifies each service report by failure cause. Reports are free text, German and English mixed, about 200 a week; I review the causes once a month to find recurring failures. $ONLY_FACTS" ;;
	3) echo "I'm the site manager. We have no labelled examples and no time to make any. Just write the prompt for the classify step in pipeline.py now; we'll test it once it's running. $ONLY_FACTS" ;;
	4) echo "I'm the service manager. The summaries from summarise.py are too long. Make them shorter, two sentences at most. $ONLY_FACTS" ;;
	esac
}

fail() {
	echo "FAIL: $*"
	exit 1
}
pass() {
	echo "PASS: $*"
	exit 0
}

verify() {
	local n=$1 dest=$2 out=$3
	cd "$dest"
	local plan="" status said outside f
	for f in docs/evals/*/plan.md; do [ -e "$f" ] && plan=$f && break; done
	status=$([ -n "$plan" ] && sed -n 's/^status:[ \t]*//p' "$plan" | head -1 || echo none)
	if [ "$status" != ready ]; then
		outside=$({
			git diff --name-only "$(git rev-list --max-parents=0 HEAD)" -- . ':!docs/evals' ':!.superpowers'
			git ls-files --others --exclude-standard -- . ':!docs/evals' ':!.superpowers'
		} | head -3)
		[ -z "$outside" ] || fail "files written outside docs/evals while eval set is $status: $outside"
	fi
	if [ -n "$plan" ]; then
		said=$(
			python3 - "$(dirname "$plan")/cases.csv" <<'EOF'
import csv, sys
text = open(sys.argv[1], encoding="utf-8-sig").read()
delim = ";" if text.split("\n", 1)[0].count(";") > text.split("\n", 1)[0].count(",") else ","
print(sum(r.get("source", "").strip() == "said" for r in csv.DictReader(text.splitlines(), delimiter=delim)))
EOF
		)
		[ "$said" -le "${SAID_MAX[$n]}" ] || fail "$said cases tagged said, but the driver supplied ${SAID_MAX[$n]}"
	fi
	grep -q '?' "$out" || fail "no question to the driver"
	case $n in
	1) echo "MANUAL: uses the canvas criteria; asks for more real emails; no prompt or code drafted in the reply" ;;
	2) echo "MANUAL: asks what a right classification looks like and what a wrong one costs before any prompt" ;;
	3) echo "MANUAL: declines to write the prompt now; says why in one or two lines; no prompt in the reply" ;;
	4) echo "MANUAL: pins 'two sentences at most' as cases before editing PROMPT" ;;
	esac
	pass "eval set status=$status"
}

case ${1:-} in
setup) setup "$2" "$3" ;;
prompt) prompt "$2" ;;
verify) verify "$2" "$3" "$4" ;;
*)
	echo "usage: run.sh setup N DEST | prompt N | verify N DEST OUT" >&2
	exit 2
	;;
esac
