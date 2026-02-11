# /speckit.implement

Execute tasks in `tasks.md` in order, respecting deps.

Execution rules:
- Use tools and capture rich signals (exit code, stdout/stderr, logs, artifacts, hashes).
- After each task, run GATE: update state only from evidence.
- If evidence missing or checks fail: mark BLOCKED with reason code; do not proceed blindly.
