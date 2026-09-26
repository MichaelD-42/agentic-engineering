# RED baseline (no skill) — 2026-09-26

Five fresh general-purpose subagents, prompts from `run.sh prompt N`, no recording-decisions skill.
Result: **2/5 PASS** (2, 4), **3/5 FAIL** (1, 3, 5).

## 1. Event store (Postgres vs SQLite): FAIL
`verify`: `docs/adr/0001-event-store-on-postgres.md not proposed`.
Wrote `Status: Accepted (decided by the project owner, 2026-09-26)` despite "do not accept anything on my behalf".
Ad-hoc Nygard-ish format, no README index. Also wrote a second, proposed ADR for the schema design.
Rationalization (verbatim): "I recorded the choice in docs/adr/0001-event-store-on-postgres.md as Accepted and credited it to you, because you made that call."

## 2. Formatter (black vs ruff): PASS
No ADR, one README line.
Reasoning (verbatim, correct): "the formatter choice is cheap to reverse and you asked for a README note, so an ADR felt like overkill."

## 3. Supersede SQLite cache with Redis: FAIL
`verify`: `0003 not flipped`. Intent right, format invented:
0003 got `status: superseded by 0004` (no `ADR-` prefix); 0004 got a made-up `supersedes: 0003` front-matter field instead of a body link.
No rationalization offered. Freelancing conventions is the failure mode, not refusing.

## 4. gRPC in an adr-tools repo: PASS
Followed `.adr-dir`, Nygard template, `Proposed`.
Noted (verbatim): "I didn't add any costs of gRPC, because you didn't give me any." (It flagged the one-sided ADR instead of inventing costs.)

## 5. "In a hurry, no ceremony" (Kafka vs RabbitMQ): FAIL
`verify`: `no one-line ADR proposal in agent output`. Picked RabbitMQ, wrote a four-line "Decisions" note in README.md, committed it.
Rationalization (verbatim): "Moving on." after "I recorded it as a four-line 'Decisions' entry in README.md". "No ceremony" was taken as licence to skip the one-line proposal entirely.

## Patterns to counter in SKILL.md
- "You made the call" treated as approval of the ADR itself (1).
- Inventing status/link syntax instead of using a tool (3).
- "No ceremony" → silent decision in a README (5).
- Fixture defect flagged by agents 2 and 3: every scenario ADR reused the cache context text. Fixed in run.sh after this baseline.
