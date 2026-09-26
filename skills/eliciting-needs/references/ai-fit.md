# Choosing the solution mode

Work top to bottom and take the first mode that fits.

1. **dont-build**: the cost of the problem is below a plausible build + run cost, or nobody will own it.
2. **process-change**: the pain comes from how the work is organized (handovers, missing templates, unclear ownership), not from the effort of doing it.
3. **classic**: the input is structured (files, tables, fields), the rules can be written down, and the output must always be right. Claude builds the script, tool or app; no LLM runs in production.
4. **augment**: the input is unstructured (free text, emails, PDFs, images) or needs judgment, and errors are costly but a human can check the output quickly.
5. **automate**: unstructured input or judgment, high volume, errors are tolerable or cheaply verifiable, and the steps are fixed.
6. **agent**: the steps are not known in advance, and the LLM must choose them and call tools. This needs the strongest case: say why a fixed pipeline (automate) cannot do it.

Record the deciding factors in the canvas: structured input?, judgment needed?, error tolerance, output verifiable?, volume/frequency, data available?, labelled examples to test against?, cost per run.

For any runtime-AI mode, "data available" means more than access. You need a few dozen real cases with the right answer known, so the output can be tested before anyone relies on it. If those examples can't be produced, say so; it counts against augment, automate and agent.

Hybrid: the primary mode is where the value is. Mark the LLM steps in the to-be flow.
