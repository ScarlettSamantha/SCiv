# Python Conventions

> Back to [Documentation Index](../INDEX.md)
>
> Related: [Agent Workflow](agent-workflow.md) | [Update Triggers](update-triggers.md) | [Changelog Workflow](changelog-workflow.md)

This page is the source of truth for day-to-day Python authoring conventions in SCiv.

The goal is not to chase style for style's sake. The goal is to keep SCiv's Python code predictable for contributors, friendly to Pyright strict mode, and aligned with the Python version the repository actually targets.

## Version target

SCiv targets **Python 3.14** as the official repository baseline.

That means new code should assume modern Python syntax and standard-library behavior available in Python 3.14.

### Practical consequences

- prefer native unions such as `Player | None` over `Optional[Player]` when it improves readability
- prefer built-in generics such as `list[str]`, `dict[str, int]`, and `tuple[float, float]`
- prefer modern standard-library helpers available on the 3.14 baseline instead of compatibility shims for older versions
- do not add compatibility code for Python 3.13 or earlier unless the repository explicitly reintroduces that support later

## `from __future__ import annotations`

Do **not** add `from __future__ import annotations` to new SCiv Python modules.

Python 3.14 already provides the typing syntax and runtime behavior SCiv expects, so the future import is unnecessary noise in normal repository code.

### Exceptions

If a future import is kept in an older module for a narrowly justified runtime reason, leave a short comment explaining why it still exists. Otherwise, prefer removing it when touching the file safely.

## Typing policy

SCiv uses **Pyright in strict mode** as the canonical type-checking workflow.

The repository configuration lives in:

- [`pyrightconfig.json`](../../pyrightconfig.json)
- [`pyproject.toml`](../../pyproject.toml)

### Required default

Write Python as if another contributor will read the types before they read the implementation.

That means:

- annotate function and method parameters
- annotate return types
- annotate instance attributes that carry state across methods
- annotate module-level variables whose types are part of the module contract
- annotate non-trivial local variables, especially when they:
  - hold containers
  - change shape across branches
  - are initialized with `None`
  - are reused across multiple logical steps
  - would otherwise force the reader or Pyright to guess

### Prefer explicit, precise types

Prefer:

- `list[Tile]` over bare `list`
- `dict[str, Player]` over `dict`
- `Tile | None` over `Any`
- `Sequence[str]` or `Iterable[str]` when the code only needs read-only iteration
- `Literal[...]`, `TypeAlias`, `Protocol`, `TypeVar`, and `Self` when they make a contract clearer

Avoid:

- bare `Any` unless unavoidable for external or dynamic integrations
- broad `object` when a narrower protocol or union expresses the contract better
- type comments when a normal annotation works
- silently relying on inference for long-lived or cross-branch values

## Local variable guidance

SCiv should be **strongly typed**, not merely “function-typed.”

In practice, that means contributors should type variables instead of assuming inference is always good enough.

A good rule of thumb:

- if a variable survives more than a couple of lines, annotate it when its type is not obvious
- if a variable is a container, annotate the element type explicitly
- if a variable starts as `None`, annotate the final intended union explicitly
- if a variable exists to cross an ownership or subsystem boundary, annotate it explicitly

Tiny one-line temporaries with an obvious scalar type do not need ceremony, but the default bias should be toward clear typing.

## Readability and spacing

SCiv should prefer readable code over maximally dense code.

Use whitespace intentionally so related lines stay grouped and different logical phases are easy to scan.

It is fine if code is a little less dense when that spacing makes the structure clearer and more visually pleasant.

When organizing code:

- group related statements together
- use blank lines to separate distinct steps such as setup, validation, transformation, side effects, and return paths when those steps are meaningfully different
- avoid cramming unrelated operations into one dense block just to save vertical space
- keep spacing consistent so a function is easy to scan top to bottom

## Structure and modularity

Prefer splitting code into smaller reusable chunks such as helper functions, modules, classes, components, or focused elements when that makes the code easier to understand and reuse.

It is usually better to keep concerns separated into different files when that separation is practical and useful.

The goal is not fragmentation for its own sake. The goal is better cohesion, easier review, less token churn when editing, and clearer boundaries between responsibilities.

When organizing code:

- prefer small focused units over large multipurpose blocks
- extract reusable behavior when the same responsibility would otherwise be repeated or tangled together
- keep files focused on a clear responsibility when practical
- split code into separate files when it improves clarity, reuse, maintenance, or targeted editing
- avoid needless indirection or tiny abstractions that make the flow harder to follow

## Comment guidance

SCiv should prefer code that reads clearly without commentary.

Do not add comments by default.

Use a comment only when the logic would still be hard to understand from well-named code alone, most commonly for genuinely non-obvious math, coordinate transforms, or similar constraints.

When a comment is justified:

- keep it short
- explain the non-obvious reason or constraint
- do not narrate line-by-line behavior the code already shows
- prefer one precise note over a block of commentary so the code stays clean

## Scope guidance

Prefer small, focused changes over big sweeping ones.

When touching code:

- solve the requested problem with the smallest coherent diff
- keep changes easy to review, reason about, and validate
- avoid opportunistic rewrites or broad refactors unless they are required to complete the task safely

## Validation workflow

Use Pyright as the first-line type check.

Repository shortcuts:

- `make pyright-full` — run the full configured Pyright pass
- `make pyright-diff` — run the diff-scoped Pyright check used by local verification

Type-related changes should also keep normal syntax validation healthy for touched files.

## When touching legacy code

SCiv contains older dynamic code and a few legacy typing shortcuts.

When you touch those areas:

- do not rewrite whole files just to modernize typing
- improve the touched surface if it is safe and local
- remove unnecessary future-annotations imports when you are already editing the file and the change is low-risk
- leave a narrow comment or follow-up note when a typing cleanup is desirable but outside scope

## Related workflow rules

- If a task changes repo-local workflow or coding conventions, also update [Agent Workflow](agent-workflow.md), [Update Triggers](update-triggers.md), and the relevant `.github/**` routing layer.
- If a task is user-visible, contributor-visible, or workflow-visible, add a note to [`CHANGELOG.md`](../../CHANGELOG.md) using the helper documented in [Changelog Workflow](changelog-workflow.md).
