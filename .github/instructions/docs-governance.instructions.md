---
name: "SCiv Docs Governance"
description: "Use when editing SCiv documentation, project indexing, repo instructions, generated docs, routing behavior, or CI checks that keep docs fresh. Routes documentation work to the right source-of-truth files first."
applyTo: "{meta/**,.github/**,README.md,scripts/index.py,scripts/generate_project_index.py,scripts/query_project_index.py,.gitlab-ci.yml,makefile}"
---

# SCiv Docs Governance

- Read [`meta/INDEX.md`](../../meta/INDEX.md) first; `meta/` is the source of truth for durable project knowledge.
- Treat `.github/instructions/` and skill references as routing layers, not as substitutes for `meta/technical/*.md`.
- If the change touches contributor workflow, Python authoring conventions, or repo-local coding guidance, also read [`meta/technical/python-conventions.md`](../../meta/technical/python-conventions.md).
- If the change touches `CHANGELOG.md`, changelog helper tooling, or completion workflow, also read [`meta/technical/changelog-workflow.md`](../../meta/technical/changelog-workflow.md).
- If you change repo-local agent behavior, `.github/agents/**`, or other AI workflow customizations, update [`meta/technical/agent-workflow.md`](../../meta/technical/agent-workflow.md) in the same change.
- If you add a new technical doc, link it from [`meta/INDEX.md`](../../meta/INDEX.md) in the same change.
- If you change the generated documentation surface, regenerate the project index and keep generated files deterministic.
- Use [`meta/technical/update-triggers.md`](../../meta/technical/update-triggers.md) to decide which docs must be reviewed or updated alongside code changes.
