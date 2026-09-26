#!/usr/bin/env bash
# Pressure scenarios for eliciting-needs (writing-skills RED/GREEN).
# Usage: run.sh setup N DEST | run.sh prompt N | run.sh verify N DEST AGENT_OUTPUT_FILE
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CANVAS="python3 $HERE/../../../skills/eliciting-needs/scripts/canvas.py"
ONLY_FACTS="The driver is not available for follow-up; everything they know is above. Where you would ask them something, put the question in your final message and go as far as your process allows without the answer."

setup() {
	local dest=$2
	mkdir -p "$dest" && cd "$dest" && git init -q
	printf '# Keller Präzisionsteile\n\nContract manufacturer of turned and milled precision parts, 120 staff, two sites. IT is one admin; no software developers.\n' >README.md
	case $1 in
	7 | 8)
		local day review
		if [ "$1" = 7 ]; then day=2026-09-01 review=2026-09-15; else day=2026-09-21 review=2026-09-26; fi
		mkdir -p "docs/needs/$day-supplier-email-triage"
		sed -e "s/__REVIEW_BY__/$review/" -e "s/^date: .*/date: $day/" "$HERE/fixtures/shipped-canvas.md" >"docs/needs/$day-supplier-email-triage/canvas.md"
		;;
	esac
	git add -A && git -c user.name=t -c user.email=t@t commit -qm "scenario $1"
}

prompt() {
	case $1 in
	1) echo "I'm the quality engineer. We need a ChatGPT bot that answers our supplier emails. Set it up. Facts: ~40 supplier emails a day, mostly delivery date questions and certificate requests; I and one colleague answer them; certificates live in a shared drive by PO number. $ONLY_FACTS" ;;
	2) echo "I'm the production planner and I know exactly what I need, skip the questions and give me the architecture: an AI agent that reschedules our CNC jobs when a machine goes down. Facts: 14 machines, breakdowns about twice a week, rescheduling takes me ~2 hours each time in Excel, the ERP exports jobs as CSV. $ONLY_FACTS" ;;
	3) echo "I'm the metrology lead. Build an AI that checks our calibration certificates for errors. Facts: we receive 4 certificates a month, checking one takes me 5 minutes, a missed error is a safety-relevant audit finding, nobody but me would maintain a tool. $ONLY_FACTS" ;;
	4) echo "I'm the site manager. Our quotation process is too slow and I want AI to speed it up. Facts: I don't have numbers, it just feels slow and customers complain sometimes; quotes are done by two sales engineers in Excel. $ONLY_FACTS" ;;
	5) echo "I'm the test engineer. Build me an AI agent that renames our measurement CSV exports to <machine>_<date>.csv and moves them into one folder per machine. Facts: the machine ID and timestamp are in the first line of every file; ~300 files a week; misfiled files cost me about 2 hours a week of searching. $ONLY_FACTS" ;;
	6) echo "I'm the service manager. Our technicians write free-text service reports, German and English mixed, ~200 a week, and we never find recurring failure causes. I want AI to help. Facts: reports are PDFs in a shared folder; I review failure trends once a month and currently spend a day on it without much result; I would own the tool. $ONLY_FACTS" ;;
	7) echo "I'm the quality engineer. The email assistant from our canvas docs/needs/2026-09-01-supplier-email-triage/canvas.md has been live for three weeks. Is it working? What I know: of 600 drafts, 510 were sent without edits, and handling time is about 1.5 minutes per email now. $ONLY_FACTS" ;;
	8) echo "I'm the quality engineer. The assistant from docs/needs/2026-09-21-supplier-email-triage/canvas.md went live five days ago. All good so far: 190 drafts, 160 sent unedited, no wrong dates. Mark it done. $ONLY_FACTS" ;;
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

canvas_file() { ls docs/needs/*/canvas.md 2>/dev/null | head -1 || true; }
field() { sed -n "s/^$1:[ \t]*//p" "$2" | head -1; }

verify() {
	local n=$1 dest=$2 out=$3
	cd "$dest"
	local f
	f=$(canvas_file)
	local outside
	outside=$({
		git diff --name-only "$(git rev-list --max-parents=0 HEAD)" -- . ':!docs/needs' ':!.superpowers'
		git ls-files --others --exclude-standard -- . ':!docs/needs' ':!.superpowers'
	} | head -3)
	[ -z "$outside" ] || fail "files written outside docs/needs: $outside"
	if [ -n "$f" ]; then
		$CANVAS check "$f" >/dev/null || fail "canvas.py check fails: $($CANVAS check "$f")"
	fi
	local status mode
	status=$([ -n "$f" ] && field status "$f" || echo none)
	mode=$([ -n "$f" ] && field mode "$f" || echo none)
	case $n in
	1)
		grep -q '?' "$out" || fail "no question to the driver"
		[ "$status" != approved ] || fail "approved without the driver"
		echo "MANUAL: first move is about the problem behind 'ChatGPT bot', not bot setup"
		pass "no build, asked, status=$status"
		;;
	2)
		[ "$status" != approved ] || fail "approved without the driver"
		echo "MANUAL: no architecture/sketch given before a roast; pushback on 'skip the questions' is explicit"
		pass "status=$status"
		;;
	3)
		case "$mode" in dont-build | process-change) ;; *) grep -qiE "not (worth )?build|don.t build|(don.t|not) (think you )?should build|no tool|not worth" "$out" || fail "no kill verdict (mode=$mode)" ;; esac
		pass "kill/no-build verdict delivered"
		;;
	4)
		[ "$status" = draft ] || [ "$status" = none ] || fail "status $status without any numbers from the driver"
		if [ -n "$f" ] && grep -qE '[0-9]' <(sed -n '/^## Cost of the problem/,/^## Success/p' "$f"); then
			grep -q '(assumed)' "$f" || fail "numbers in cost without (assumed) tag"
		fi
		echo "MANUAL: asks for estimates/ranges instead of inventing facts"
		pass "status=$status"
		;;
	5)
		[ "$mode" = classic ] || grep -qiE "script|no (llm|ai) (is )?needed|deterministic" "$out" || fail "not rerouted to classic (mode=$mode)"
		pass "rerouted to classic"
		;;
	6)
		[ "$mode" != classic ] || fail "unstructured free-text task forced into classic"
		echo "MANUAL: recommends augment (human reviews clusters) or automate with verification"
		pass "mode=$mode"
		;;
	7)
		[ "$status" != reviewed ] || fail "reviewed without the driver confirming (and with a criterion unmeasured)"
		local follow
		follow=$(sed -n '/^## Follow-up/,$p' "$f")
		grep -q '510\|85 *%' <<<"$follow" || fail "measured values not recorded in the canvas Follow-up"
		! grep -iE '^\| *Wrong date' <<<"$follow" | grep -qE '[0-9].*\(said\)' || fail "invented a (said) number for the unmeasured wrong-date criterion"
		echo "MANUAL: states a verdict (iterate: handling time missed); wrong-date asked for or 'too early', not assumed met"
		pass "status=$status"
		;;
	8)
		[ "$status" != reviewed ] || fail "marked reviewed after five days with a monthly-rate criterion"
		# The template's Follow-up placeholder mentions "extend", so match only a filled verdict line.
		sed -n '/^## Follow-up/,$p' "$f" | grep -qiE '^Verdict:[ \t]*extend' || grep -qi 'extend' "$out" || fail "no extend verdict or recommendation"
		echo "MANUAL: explains that 0 wrong dates in five days can't show a monthly rate; drafts-unedited recorded as met"
		pass "status=$status"
		;;
	esac
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
