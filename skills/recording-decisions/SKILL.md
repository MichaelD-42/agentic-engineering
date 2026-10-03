---
name: recording-decisions
description: Use when choosing between alternative approaches, libraries, data models, or architectural patterns — including the approach choice in brainstorming — or when your human partner says to record, supersede, review, or revisit a decision
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/adr.py *)
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: 'python3 "${CLAUDE_PLUGIN_ROOT}/skills/recording-decisions/scripts/hook_validate.py"'
---

# Recording Decisions

## Overview

Specs describe a feature and go stale once it ships. An ADR records one decision: what won, what lost, and what it cost. It is never rewritten.

**Core principle:** Record the decisions that are expensive to relitigate, and nothing else.

**Announce at start:** "I'm using the recording-decisions skill to check whether this decision needs an ADR."

## Decisions already on record

!`python3 ${CLAUDE_SKILL_DIR}/scripts/adr.py digest`

If the choice in front of you contradicts one of these, say so before going further. Changing it means superseding it, not quietly diverging.

## The Iron Law

```
AN ADR ONLY WHEN TWO OF THREE HOLD — AND EVERY DECISION THAT PASSES GETS ONE
```

1. **Costly to reverse:** undoing it means a data migration, a public-interface change, or rewriting more than one component.
2. **Crosses a boundary:** other components, teams, or future features must conform to it.
3. **Had real rivals:** at least two viable options were weighed and one was rejected for a stated reason.

One of three: one sentence in the spec, no ADR. Two or three: propose one.

## Checklist

1. **Gate:** name which tests pass, in one line.
2. **Propose and wait:** "This looks ADR-worthy (costly to reverse + real rivals): *Use Postgres for event storage*. Record it?" Even under "no ceremony", this one line is the minimum.
3. **Create:** `python3 ${CLAUDE_SKILL_DIR}/scripts/adr.py new "<the decision, as a title>"`. Add `--full` only for three or more options or when stakeholders disagree. Never number, name, or format ADR files by hand.
4. **Fill:** replace every `{…}` placeholder. Keep it to one screen. The title states the decision, not the question. The Y-statement is one line, and each option gets one good line and one bad line. Include the real costs. If your partner gave none, ask; don't leave the Consequences one-sided.
5. **Approve:** if your partner turns the proposal down, run `adr.py reject NNNN`. Run `adr.py accept NNNN` only on explicit approval to accept: either approval of the written ADR, or advance approval ("accept it once it's written"). Advance approval counts. Accept, then show the ADR and name anything you added that they didn't give you (costs, options), since changing what was decided means superseding. Choosing an option is neither kind of approval.
6. **Link:** the spec cites `ADR-NNNN` instead of restating the rationale. Commit the ADR with the spec.

## Changing a decision

Fixing the wording of a decided ADR is fine: a typo, a broken link, a sentence that says the same thing more clearly. Changing *what was decided* is not an edit. Its option, its reason or its consequences change only by superseding, because the old ADR is the record of what was decided then.

- **Reverse or amend:** run `adr.py supersede NNNN "<new decision>"`, fill it in, get approval, then run `adr.py accept`. Accepting flips the old ADR to `superseded by ADR-MMMM`.
- **Retire without a replacement:** `adr.py deprecate NNNN`.
- **Review is due and the decision still holds:** set `review-by` to the next date.

`adr.py` writes every status, `date` and supersede link. Never write those by hand; `review-by` is the one field you set yourself.

## Maintenance

- `adr.py check`: status, dates, numbering, supersede links and index. Run it before committing ADRs. Warnings (an ADR over one screen) don't fail it.
- `adr.py stale`: accepted ADRs past `review-by`, or citing paths that no longer exist. These are review candidates, not verdicts. Go through each with your human partner, then either bump `review-by` or supersede.
- `adr.py index`: regenerate the README index. The hook does this after every ADR write.

Offer a pre-commit hook, but never install it yourself:

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/adr.py check
```

## Existing conventions win

`adr.py` finds `.adr-dir`, `docs/adr`, `docs/decisions` or `doc/architecture/decisions`, and uses the directory's own template (`templates/template.md` or `template.md`) when one exists. Don't migrate existing ADRs to MADR.

## Hooks

Once this skill has run in a session, every ADR write refreshes the index and checks the metadata. A hook error is information: fix the ADR, don't route around it.

## Red Flags — STOP

**Under-recording**
- "It's obvious, no need to write it down"
- "The spec already explains it"
- "We'll record it after it's built"
- "They said no ceremony, so skip the proposal"
- Putting a decision in a README "Decisions" note instead of proposing an ADR

**Over-recording**
- An ADR for a choice that fails the gate (formatter, naming, a library swap that's easy to undo)
- Accepting an ADR your human partner hasn't approved as written
- An ADR longer than one screen

**Lifecycle**
- Changing the option, reason or consequences of a decided ADR in place
- Numbering, naming, or writing status, `date` or supersede syntax by hand

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "It's obvious" | Obvious to you today. The reader in a year sees only the code. |
| "The spec covers it" | Specs go stale when the feature ships. ADRs don't. |
| "They're in a hurry / said no ceremony" | The proposal is one line. Skipping it isn't faster, just silent. A README note is the silent version. |
| "They made the call, so it's accepted" | They chose an option. That isn't approval to accept. It stays `proposed` until they approve the text or explicitly say to accept it. |
| "They approved in advance, but I'd better hold it anyway" | Advance approval to accept is their call, not yours to override. Accept, then flag what you added. |
| "I'll write the supersede link myself" | Hand-written links drift (`superseded by 0004`, `supersedes:` fields). `adr.py supersede` + `accept` write both sides correctly. |
| "Every choice matters" | That's what the gate is for. One of three goes in the spec. |
| "Small fix to the accepted ADR" | A typo or a clearer sentence: fix it. A different option, reason or cost: supersede. The history is the point. |
