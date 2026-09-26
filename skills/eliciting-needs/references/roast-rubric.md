# Roast rubric

Blunt about the idea, never about the person. Every score below 2 names the question that would fix it.

## Scores per cell (Actual need … Constraints and risks)
- **0**: missing, or it's a solution in disguise ("need: a chatbot")
- **1**: vague, or rests on `(assumed)` claims
- **2**: specific, `(said)` by the driver, verifiable

Constraints and risks scores 2 only if it says what happens to people when the output is wrong (who notices, what it costs), not just that the model can err.
Cost of the problem scores 2 only if it separates the realistic from the optimistic figure.

Pass: no 0s, and Actual need, Success criteria and Solution mode all at 2.

## Kill criteria (override the score → `Verdict: kill`, mode dont-build or process-change)
- No measurable success criterion can be agreed.
- The cost of the problem is below a plausible build + run cost.
- The required data doesn't exist or can't legally be used.
- Nobody owns it after launch.

A kill also names what would have to change to revisit it ("if certificate volume passes ~50/month").

## Mode challenges (→ `Verdict: reroute`, change the mode, roast again)
- Runtime-AI mode, but the input is structured and the rules are expressible → classic.
- automate/agent with low error tolerance and unverifiable output → augment or classic.
- agent where a fixed sequence of steps would do → automate.
- classic for free text or judgment-heavy input → augment.

## Format
Fill the Roast table in the canvas, then `Kill criteria: …` and `Verdict: pass|reroute|kill`.
