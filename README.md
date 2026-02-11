# MVP v0.2 — Spec Kit scaffold (memory + task preferences)

This repository is a **minimal Spec Kit** scaffold for an agentic system whose only durable identity is:

- **Memory:** proven observations with provenance
- **Task preferences:** deterministic ranking/routing preferences under constraints

The SSOT is `.specify/memory/constitution.md`.

## Workflow (Plan → Execute → Gate)

- **Plan:** produce a bounded work DAG (`{reqs,deps,provs,assert}`) and evidence obligations.
- **Execute:** run tools with rich signals (exit codes, stdout/stderr, logs, artifacts, hashes).
- **Gate:** update state **only** from gathered evidence. DONE requires satisfied obligations.

## Spec Kit layout

- `.specify/memory/constitution.md` — SSOT principles (project constitution)
- `.specify/templates/*.md` — templates for spec / plan / tasks
- `.specify/specs/001-mvpv0_2-memory-task-preferences/` — initial feature artifacts
- `.claude/commands/` and `.github/prompts/` — minimal slash-command prompts

## Using with Spec Kit

If you already use Spec Kit in your environment, you can initialize/upgrade templates as needed using `specify init --here --force` and your preferred agent.

See GitHub Spec Kit docs for setup and supported agents. (https://github.com/github/spec-kit)
