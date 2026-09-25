# AGENTS.md

## Quality invariant

This repository requires **100% statement coverage and 100% branch coverage** for the
`yt_transcript` package.

This is a project invariant, not a one-time target. Any agent or human changing source code
must preserve it.

Before considering a task complete, run:

```bash
uv run python scripts/check.py
```

A change is not complete if any of the following is true:

- a test fails;
- statement coverage is below 100%;
- branch coverage is below 100%;
- Ruff formatting or linting fails;
- mypy fails;
- code is excluded from coverage only to bypass this invariant.

When new or modified behavior introduces a reachable path, add or adapt behavioral tests that
exercise that path.

If a branch is genuinely unreachable or redundant, prefer simplifying or removing the code
instead of adding an artificial test solely to satisfy coverage.

Do not weaken the coverage threshold, disable branch coverage, add blanket coverage exclusions,
or mark reachable production code as untestable without an explicit project decision.
