# Project Index Helper

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Agent Workflow](agent-workflow.md) | [Update Triggers](update-triggers.md) | [Project Structure](../structure.md)

This page is the source of truth for SCiv's unified project-index helper at [`scripts/index.py`](../../scripts/index.py).

The helper exists for both humans and coding agents.

It owns the generated inventory artifacts, provides targeted lookup commands, and offers a small health/freshness workflow so users do not have to read the full JSON manifest just to answer a focused question.

## What it manages

The helper generates and reads these artifacts:

- [`meta/generated/project-index.json`](../generated/project-index.json) — machine-readable inventory of docs, entry points, routes, areas, and modules
- [`meta/generated/doc-routing.json`](../generated/doc-routing.json) — machine-readable routing manifest for guarded subsystems
- [`meta/structure.md`](../structure.md) — human-readable project map

The canonical entrypoint is:

- `python3 scripts/index.py`

Legacy compatibility wrappers still exist during the transition period:

- `python3 scripts/generate_project_index.py`
- `python3 scripts/query_project_index.py`

Those wrappers forward to the unified helper and print deprecation warnings on stderr.

## Command overview

| Command | Purpose |
| --- | --- |
| `generate` | Regenerate the project index, routing manifest, and structure map. |
| `check` | CI-friendly freshness check for generated artifacts. |
| `search <query>` | Fuzzy search across docs, routes, areas, entry points, and modules. |
| `show <target>` | Show an exact or partial match by path, route id, or module name. |
| `route <query>` | Focused lookup for routing-rule matches and required docs. |
| `area <query>` | Focused lookup for indexed runtime-area matches. |
| `list <slice>` | Browse one indexed slice such as docs, routes, areas, modules, entries, artifacts, or top-level items. |
| `stats` | Show inventory counts and freshness summary. |
| `doctor` / `validate` | Diagnose stale artifacts, missing outputs, and parse-error health. |

Run `python3 scripts/index.py --help` or any subcommand with `--help` for the current CLI contract and examples.

## Freshness behavior

Read-only commands such as `search`, `show`, `route`, `area`, `list`, and `stats` verify whether the generated outputs are missing or stale.

Default behavior:

- if generated artifacts are current, use them normally
- if generated artifacts are stale, warn and keep using the existing manifest
- if generated artifacts are missing, fail and tell the user how to generate them

Useful options:

- `--refresh-if-stale` — regenerate missing or stale artifacts before continuing
- `--require-fresh` — fail instead of reading stale artifacts

Use `check` when you need a strict pass/fail freshness command for CI or verification.

Use `doctor` when you want a more descriptive health report.

## Human workflow

A good local workflow is:

1. `search` when you are asking “where does this live?”
2. `route` when you want the must-read docs for a guarded subsystem
3. `show` when one result needs more detail
4. `list` when you want to browse a known slice such as routes or modules
5. `stats` or `doctor` when the manifest may be stale or unhealthy
6. `generate` after structural or routing changes
7. `check` before finishing or in automation

## AI and agent workflow

Repo-specialized agents should prefer the helper before reading the full JSON manifest when they need fast narrowing.

Recommended pattern:

1. start with [`meta/INDEX.md`](../INDEX.md)
2. use the `sciv-project-index` skill or `python3 scripts/index.py search "<topic>"`
3. use `route` when the task is obviously subsystem-driven
4. read the returned docs and source files before editing
5. run `generate` after changing the helper itself, routing docs, generated-doc rules, or related documentation surfaces

The helper narrows candidates; it does not replace source review.

## Output modes

Human-readable text is the default output for browse and query commands.

For automation or agent consumption, most read-oriented commands support `--json` so the caller can consume stable structured results instead of formatted text.

That includes:

- `search`
- `show`
- `route`
- `area`
- `list`
- `stats`
- `doctor`

## When to regenerate

Regenerate the artifacts when:

- the repo structure changes in a way the index should reflect
- a routing rule changes
- a new technical doc or skill/routing doc becomes part of the indexed surface
- the helper implementation changes in a way that affects generated content

After those changes, run:

- `python3 scripts/index.py generate`
- `python3 scripts/index.py check`

`make docs-refresh` and `make docs-check` are thin wrappers around those canonical commands.
