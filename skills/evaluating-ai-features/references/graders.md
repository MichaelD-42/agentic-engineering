# Choosing graders, k and thresholds

## Code graders first
Use a code grader whenever the right output can be checked mechanically:
- exact match (a category, a PO number, a date);
- JSON schema or required fields;
- regex (format, "no more than two sentences");
- numeric tolerance (a price within 1%);
- set membership (one of the allowed causes).

Write the check in `plan.md` under Grading notes, per criterion.

## Model graders only for judgment
When correctness needs judgment (tone, completeness, a faithful summary), grade with a model against a rubric. The rubric is a short list of observable points, each pass or fail ("names the machine", "states the cause if the report gives one", "invents nothing"). No 1–10 scores: they drift and can't be thresholded honestly.

## k: runs per case
LLM output varies between runs. A case passes only if all k runs pass.
- k = 1: deterministic settings (temperature 0 and a code grader), or cost forbids more.
- k = 3: the default.
- k = 5: automate or agent mode, where nobody reviews the output before it has an effect.

## Thresholds from error tolerance
- `refuse` cases: always 100%. A step that answers what it should decline is not ready.
- augment (a human reviews every output): normal cases may accept less than 100%; take the target from the canvas (e.g. "80% sent without edits").
- automate and agent: the threshold is the error rate the canvas says is tolerable; if the canvas says none, the mode is wrong; send it back to the roast.
