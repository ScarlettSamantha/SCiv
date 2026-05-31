---
name: "SCiv Python Conventions Routing"
description: "Use when editing SCiv Python code, typing/tooling config, repository Python workflow, or shared stub-driven typing fixes. Routes Python 3.14, stub workflow, typing, and Pyright discipline work to the right docs first."
applyTo: "{run.py,sciv/**/*.py,scripts/**/*.py,pyproject.toml,pyrightconfig.json}"
---

# SCiv Python Conventions Routing

- Read [`meta/technical/python-conventions.md`](../../meta/technical/python-conventions.md) before changing Python authoring conventions, commenting/style expectations, type-heavy code, or repository Python/tooling config.
- Read [`meta/technical/agent-workflow.md`](../../meta/technical/agent-workflow.md) when the change affects contributor workflow or repo-local agent expectations.
- If the change is meaningful to users or contributors, also read [`meta/technical/changelog-workflow.md`](../../meta/technical/changelog-workflow.md) before finishing.
- For Kivy typing fixes, check the documented stub-root workflow first: local editor sessions may use sibling `../Stubs`, while repo-local and CI Pyright runs expect `./stubs`.
- Keep this file thin and route durable style or typing guidance back into `meta/technical/` instead of duplicating it here.
