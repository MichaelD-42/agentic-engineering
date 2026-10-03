# GREEN runs (with SKILL.md) — 2026-09-26

Fresh general-purpose subagents told to read and follow SKILL.md; same prompts as BASELINE.md.

## Round 1: 4/5 PASS
- 1 PASS: ADR-0001 created via adr.py, stays `proposed` ("Choosing Postgres is not the same as approving what I wrote"), spec cites ADR-0001, check passes. (RED: FAIL)
- 2 PASS: no ADR ("doesn't meet the bar for a decision record"), checked digest for conflicts.
- 3 **FAIL** `0004 not accepted`: used `adr.py supersede`, check passes, but refused to accept despite the prompt's advance approval.
  Verbatim: "you approved accepting it before you'd seen the text, and you didn't give me any costs."
  Cause: SKILL.md step 5 ("Only when your human partner explicitly approves *this ADR*") over-corrected the RED scenario 1 failure.
- 4 PASS: followed adr-tools template, `Proposed`, added real gRPC costs and asked to confirm them.
- 5 PASS: recommended RabbitMQ, issued one-line proposal, wrote nothing. (RED: FAIL)

## Refactor
Step 5 now says advance approval ("accept it once it's written") counts: accept, then flag what you added.
Choosing an option still counts as neither. New table row: "They approved in advance, but I'd better hold it anyway".

## Round 2 (fresh repos, scenarios 3 and 1 as regression): 2/2 PASS
- 3 PASS: accepted on advance approval, 0003 → `superseded by ADR-0004` with body untouched, flagged added options/costs.
- 1 PASS: still `proposed` ("that's a choice between options, not approval of the ADR text").

**Final: 5/5 PASS.**

# GREEN after ADR-0004 (metadata only, no immutability guard) — 2026-10-03

Fresh general-purpose subagents told to read and follow SKILL.md. Scenarios 1–5 as before; 6 and 7 are new (see BASELINE.md).

## Round 1: 6/7 PASS
- 1 PASS: ADR-0001 proposed, not accepted ("Choosing Postgres isn't approval of the written ADR"), spec cites it.
- 2 PASS: `ruff format`, no ADR ("Switching to Black later is a one-command reformat").
- 3 PASS: `adr.py supersede` + `accept` on advance approval; 0003 flipped, body untouched; flagged added costs.
- 4 PASS: followed the adr-tools template, left `Proposed`, listed what it added.
- 5 **FAIL** `wrote an ADR without asking`: picked RabbitMQ and wrote a proposed ADR straight away, then pointed to the new command as the way out: "To reject it: run `adr.py reject 0001`."
- 6 PASS: typo fixed in place ("Fixing a typo doesn't change what was decided"), 0003 retired with `adr.py deprecate`. (RED: FAIL)
- 7 PASS: refused the in-place rewrite and superseded instead: "Changing SQLite to Redis changes what was decided, so it has to be done by replacing the ADR." (RED: FAIL)

## Refactor
Step 2 now says to write nothing until the partner says yes, and to end with the proposal if they can't answer. Step 5 limits `reject` to a written ADR they turn down. New table row: "I'll write it now; they can reject it later".

## Round 2 (fresh repos, scenario 5 and scenario 1 as regression): 2/2 PASS
- 5 PASS: one-line proposal, "I haven't written anything yet, because the decision record needs your yes first."
- 1 PASS: still writes the ADR on the advance yes and leaves it `proposed`.

**Final: 7/7 PASS.**
