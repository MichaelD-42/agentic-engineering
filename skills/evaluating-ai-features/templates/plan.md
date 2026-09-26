---
name: {{name}}
status: draft
canvas: {{canvas}}
k: 3
---

<!-- One row per success criterion. grader: code | model. threshold: e.g. "≥ 95% of cases pass all k runs"; refuse cases always 100%. Cases live in cases.csv next to this file. -->

## Criteria

| id | criterion | grader | threshold |
|---|---|---|---|
{{criteria}}

## Grading notes

<!-- Per criterion: the code check (exact match, JSON schema, regex, numeric tolerance) or the model rubric as observable pass/fail points. -->
