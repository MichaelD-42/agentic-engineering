# Stack profile (default)

Copy to `docs/stack.md` (project) or `~/.claude/stack.md` (personal) and edit. Sketches prefer these; any deviation needs a reason.

## Runtime AI
- LLM: Claude API — `claude-sonnet-5` by default, `claude-haiku-4-5-20251001` for high volume/low stakes
- Agents: Claude Agent SDK (Python)
- Workflow and integrations: n8n
- Evals: a golden-set CSV plus a pytest check run before every prompt change

## Classic
- Scripts: Python 3.12, single file, run with `uv run` (inline script dependencies)
- Internal apps/UI: Streamlit; a single self-contained HTML page for read-only tools
- Data: CSV/Excel in, SQLite for anything that needs a history
- Distribution: one command the driver can run (`uv run tool.py`), documented in a README
- Hosting: the driver's machine first; Docker on the existing server once shared
