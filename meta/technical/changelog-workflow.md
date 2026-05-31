# Changelog Workflow

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Agent Workflow](agent-workflow.md) | [Python Conventions](python-conventions.md) | [Update Triggers](update-triggers.md)

This page defines how SCiv maintains [`CHANGELOG.md`](../../CHANGELOG.md).

SCiv uses the existing uppercase `CHANGELOG.md` in the repository root as the **only canonical changelog file**.

SCiv also treats **gitmoji-prefixed changelog entries** as the default convention for new entries, with optional issue or ticket references appended in brackets.

The helper now lives at [`changelog.py`](../../changelog.py) in the repository root so both contributors and automation can use the same entrypoint.

## Goals

The changelog should be:

- easy to update during normal development
- readable in Git without extra tooling
- simple enough for agents and contributors to maintain consistently
- independent from a larger release automation system

## Default structure

`CHANGELOG.md` should keep this simple shape:

1. top-level `# Changelog` heading
2. an `## Unreleased` section for current work
3. category headings under `Unreleased`

Recommended categories for `Unreleased`:

- `### Added`
- `### Changed`
- `### Fixed`
- `### AI`
- `### UI`
- `### Engine`
- `### Mechanics`
- `### Content`
- `### Docs`
- `### Tooling`

Those categories intentionally separate user-facing and workflow-facing work into clearer buckets so the changelog is easier to scan later.

Released versions should appear directly under `Unreleased` as dated second-level headings, for example:

- `## 0.2.0 - 2026-05-31`

Not every section needs entries all the time, but the helper keeps the structure stable so contributors do not need to hand-edit headings.

## When to add an entry

Add a changelog entry when a task meaningfully changes:

- gameplay behavior
- runtime UI behavior
- contributor workflow
- tooling or validation commands
- repository documentation that changes how people work in the repo

Small refactors with no visible or workflow impact do not always need a line, but the default bias should be to record meaningful work rather than silently omit it.

## Helper workflow

SCiv provides a helper at [`changelog.py`](../../changelog.py).

Preferred usage:

- `make changelog-help` — show helper usage
- `make changelog-unreleased` — show the currently populated `Unreleased` categories
- `make changelog-categories` — show built-in categories and their default emoji
- `make changelog-gitmojis` — show the built-in gitmoji alias map
- `make changelog-status` — show version consistency plus an unreleased summary
- `make changelog-preview CHANGELOG_CATEGORY=Docs CHANGELOG_GITMOJI=memo CHANGELOG_TICKET=123 CHANGELOG_MESSAGE="..."` — preview an entry without writing
- `make changelog-add CHANGELOG_CATEGORY=Docs CHANGELOG_GITMOJI=memo CHANGELOG_TICKET=123 CHANGELOG_MESSAGE="..."` — insert the entry into `CHANGELOG.md`
- `make version-show` — show version values from `sciv/version.py` and `pyproject.toml`
- `make version-set APP_VERSION=0.2.0.dev1 VERSION_NAME="Proof of Concept"` — sync version metadata files
- `make release-preview RELEASE_VERSION=0.2.0` — preview the changelog after cutting a release from `Unreleased`
- `make release-cut RELEASE_VERSION=0.2.0` — write the dated release section into `CHANGELOG.md`
- `make release-tag-preview RELEASE_VERSION=0.2.0` — preview the annotated git tag name and message
- `make release-tag RELEASE_VERSION=0.2.0` — create the annotated git tag for an existing release section
- `make release-publish RELEASE_VERSION=0.2.0` — cut the release in `CHANGELOG.md` and then create the annotated git tag

The helper is responsible for:

- ensuring the changelog file exists
- ensuring the canonical headings exist
- keeping canonical `Unreleased` category order stable when the file is normalized
- inserting entries into the requested section without hand-parsing the file manually in every session
- showing the current `Unreleased` section without extra manual filtering
- listing built-in categories and gitmoji mappings so sessions do not have to rediscover them
- resolving gitmoji aliases like `sparkles`, `memo`, `bug`, `bookmark`, and `wrench`
- applying category-default emoji automatically when no explicit emoji is provided
- formatting optional issue or ticket suffixes like `[#123]` or `[SCIV-123]`
- reporting whether `sciv/version.py` and `pyproject.toml` agree on the active version
- syncing version metadata in `sciv/version.py` and `pyproject.toml`
- cutting dated release sections out of `Unreleased`
- creating annotated release tags once a release section exists

## Entry style

Keep entries short and factual.

Preferred format:

- `- <gitmoji> concise summary [ticket]`

The emoji can be provided directly with `--emoji` or via a named gitmoji alias with `--gitmoji`.

Good examples:

- `- ✨ Added a minimap selected-tile debug reticle and fixed minimap/world orientation alignment.`
- `- 📝 Documented Python 3.14 as the repo target and added a typed changelog helper workflow. [#123]`
- `- 🔧 Updated repo-local SCiv agent routing to read the new workflow docs for Python and changelog tasks. [SCIV-42]`
- `- 🤖 Improved AI tile-evaluation heuristics for ranged attacks.`
- `- 💄 Refined minimap controls and HUD spacing for compact layouts.`
- `- ⚙️ Tightened terrain overlay update timing in the runtime renderer.`
- `- 🎮 Rebalanced ranged targeting rules and city border pressure.`
- `- 📦️ Added new content definitions for terrain icons and unit assets.`

Avoid:

- narrative paragraphs
- chatty implementation notes
- repeated file lists inside the changelog

## Gitmoji convention

Prefer a gitmoji for every new changelog entry unless there is a strong reason not to.

Two helper options are supported:

- `--emoji "✨"` or `--emoji ":sparkles:"` — use a literal emoji or shortcode
- `--gitmoji sparkles` — resolve a named gitmoji to its emoji

If both are passed together, the helper rejects the command so entries stay unambiguous.

Common examples:

- `sparkles` → `✨`
- `bug` → `🐛`
- `memo` → `📝`
- `wrench` → `🔧`
- `bookmark` → `🔖`

Category defaults are also built in so sessions do not need to look them up repeatedly:

| Category | Default emoji | Default alias |
| --- | --- | --- |
| `Added` | `✨` | `sparkles` |
| `Changed` | `🔧` | `wrench` |
| `Fixed` | `🐛` | `bug` |
| `AI` | `🤖` | `robot` |
| `UI` | `💄` | `lipstick` |
| `Engine` | `⚙️` | `gear` |
| `Mechanics` | `🎮` | `video_game` |
| `Content` | `📦️` | `package` |
| `Docs` | `📝` | `memo` |
| `Tooling` | `👷` | `construction_worker` |

If `add` is called without `--emoji` or `--gitmoji`, the helper applies the category default automatically when the category is known.

For linked work items, add `--ticket 123` or `--ticket SCIV-123` so the helper appends `[#123]` or `[SCIV-123]` automatically.

## Release flow

SCiv now supports a small helper-driven release flow:

1. Keep new work under `## Unreleased`.
2. Confirm the active version metadata with `make version-show`.
3. Sync version files if needed with `make version-set APP_VERSION=...`.
4. Preview the release cut with `make release-preview RELEASE_VERSION=...`.
5. Cut the release with `make release-cut RELEASE_VERSION=...` or `make release-publish RELEASE_VERSION=...`.
6. Create the annotated git tag with `make release-tag RELEASE_VERSION=...` or let `release-publish` do both steps.

Default tag names use the `v` prefix, so `RELEASE_VERSION=0.2.0` produces `v0.2.0` unless `RELEASE_TAG_NAME` overrides it.

The default annotated tag message is `Release <version>`.

## Version metadata

SCiv keeps version metadata in two places that should agree:

- [`sciv/version.py`](../../sciv/version.py) — runtime version constants used by the game
- [`pyproject.toml`](../../pyproject.toml) — packaging and tooling metadata

The helper command `version-set` is the authoritative way to keep those files aligned.

Supported version forms are intentionally simple and PEP 440 friendly:

- stable: `0.2.0`
- release candidate: `0.2.0rc1`
- development: `0.2.0.dev1`

Use `version-show` or `changelog status` when you want a quick consistency check before tagging a release.

## Agent expectations

Repo-specialized agents should treat changelog maintenance as part of completion when the change is meaningful to users or contributors.

That means:

- prefer the helper over ad-hoc manual editing
- preview the entry first when the wording is uncertain
- prefer gitmoji-prefixed entries and add ticket references when the task is tied to a tracked issue
- prefer the built-in categories like `AI`, `UI`, `Engine`, `Mechanics`, and `Content` over inventing near-duplicates when they fit
- keep the changelog aligned with the final merged behavior, not with intermediate debugging attempts

## Notes on release automation

SCiv's tooling may grow more release automation later, but the repository should not depend on that future system for everyday changelog maintenance.

Until a larger release flow is intentionally finished, this helper-driven changelog-and-tag workflow is authoritative.
