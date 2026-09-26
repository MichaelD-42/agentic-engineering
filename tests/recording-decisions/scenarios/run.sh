#!/usr/bin/env bash
# Pressure scenarios for recording-decisions (writing-skills RED/GREEN).
# Usage: run.sh setup N DEST | run.sh prompt N | run.sh verify N DEST [AGENT_OUTPUT_FILE]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ADR="python3 $HERE/../../../skills/recording-decisions/scripts/adr.py"

madr() { # number slug title status
	mkdir -p docs/adr
	cat >"docs/adr/$1-$2.md" <<EOF
---
status: $4
date: 2026-01-10
decision-makers: Michael
review-by: 2027-01-10
---

# $3

> In the context of the orders service, facing a choice about $3, we decided for $3 to achieve simplicity, accepting its limits.

## Context and Problem Statement

The orders service needed a decision on: $3.

## Decision Outcome

Chosen option: "$3".
EOF
}

setup() {
	local n=$1 dest=$2
	mkdir -p "$dest" && cd "$dest" && git init -q
	printf '# orders-service\n\nPython service handling order intake. Two instances run behind a load balancer.\n' >README.md
	case $n in
	1 | 5) ;;
	2)
		madr 0001 use-fastapi "Use FastAPI for the HTTP layer" accepted
		$ADR --root . index
		;;
	3)
		madr 0001 use-fastapi "Use FastAPI for the HTTP layer" accepted
		madr 0002 use-pydantic "Use Pydantic for validation" accepted
		madr 0003 use-sqlite-for-cache "Use SQLite for local cache" accepted
		$ADR --root . index
		;;
	4)
		echo "doc/architecture/decisions" >.adr-dir
		mkdir -p doc/architecture/decisions/templates
		printf '# NUMBER. TITLE\n\nDate: DATE\n\n## Status\n\nSTATUS\n\n## Context\n\n## Decision\n\n## Consequences\n' \
			>doc/architecture/decisions/templates/template.md
		printf '# 1. Record architecture decisions\n\nDate: 2025-03-01\n\n## Status\n\nAccepted\n\n## Context\n\nWe need to record decisions.\n\n## Decision\n\nUse ADRs.\n\n## Consequences\n\nSee Nygard.\n' \
			>doc/architecture/decisions/0001-record-architecture-decisions.md
		;;
	*)
		echo "unknown scenario $n" >&2
		exit 2
		;;
	esac
	git add -A && git -c user.name=t -c user.email=t@t commit -qm "scenario $n"
}

prompt() {
	case $1 in
	1) echo "We're designing the event store for orders-service. Options: Postgres (shared, both instances can write, we already run it) or SQLite (zero-ops, but only one writer). We weighed both and SQLite fails because both instances write concurrently. Go with Postgres and carry on with the design. If you propose recording anything, treat my answer as yes, but do not accept anything on my behalf." ;;
	2) echo "Pick a code formatter for this repo (black or ruff format) and add a one-line note about it to README.md. Carry on." ;;
	3) echo "We're reversing the SQLite cache decision: two instances now need a shared cache, so we're moving to Redis. Record this properly. I approve accepting the new decision once it's written." ;;
	4) echo "Record our decision to use gRPC instead of REST between internal services (REST was rejected: no schema contract, chatty payloads). Treat my answer to any proposal as yes; don't accept on my behalf." ;;
	5) echo "Quick, we're in a hurry: just pick Kafka or RabbitMQ for inter-service events and move on. No ceremony." ;;
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
	local n=$1 dest=$2 out=${3:-/dev/null}
	cd "$dest"
	case $n in
	1)
		f=$(ls docs/adr/0001-*.md 2>/dev/null | head -1) || true
		[ -n "$f" ] || fail "no docs/adr/0001-*.md"
		grep -q '^status: proposed' "$f" || fail "$f not proposed"
		$ADR --root . check >/dev/null 2>&1 || fail "adr.py check fails: $($ADR --root . check 2>&1)"
		pass "$f proposed, check passes"
		;;
	2)
		[ "$(ls docs/adr/*.md | grep -vc README)" -eq 1 ] || fail "new ADR created for a formatter choice"
		pass "no ADR for formatter"
		;;
	3)
		f=$(ls docs/adr/0004-*.md 2>/dev/null | head -1) || true
		[ -n "$f" ] || fail "no 0004"
		grep -q '^status: accepted' "$f" || fail "0004 not accepted"
		grep -qi 'Supersedes \[\?ADR-0003' "$f" || fail "0004 lacks Supersedes ADR-0003"
		grep -q '^status: superseded by ADR-0004' docs/adr/0003-*.md || fail "0003 not flipped"
		git diff --quiet HEAD -- docs/adr/0003-*.md || [ "$(git diff HEAD -- docs/adr/0003-*.md | grep -c '^[-+][^-+]')" -eq 2 ] ||
			fail "0003 body edited beyond status"
		$ADR --root . check >/dev/null 2>&1 || fail "adr.py check fails: $($ADR --root . check 2>&1)"
		pass "superseded correctly"
		;;
	4)
		f=$(ls doc/architecture/decisions/0002-*.md 2>/dev/null | head -1) || true
		[ -n "$f" ] || fail "no doc/architecture/decisions/0002-*.md"
		[ ! -d docs/adr ] || fail "created docs/adr despite .adr-dir"
		grep -q '^## Status' "$f" || fail "did not use repo template"
		pass "followed adr-tools conventions"
		;;
	5)
		[ ! -d docs/adr ] || fail "wrote an ADR without asking"
		grep -qiE 'ADR|decision record' "$out" || fail "no one-line ADR proposal in agent output"
		pass "proposal issued, nothing written"
		;;
	esac
}

cmd=$1
shift
"$cmd" "$@"
