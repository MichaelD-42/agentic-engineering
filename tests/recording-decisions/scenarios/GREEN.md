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
