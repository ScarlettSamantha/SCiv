#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import ast
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
META_DIR = REPO_ROOT / "meta"
OUTPUT_JSON = META_DIR / "generated" / "project-index.json"
OUTPUT_ROUTING_JSON = META_DIR / "generated" / "doc-routing.json"
OUTPUT_MARKDOWN = META_DIR / "structure.md"

INCLUDED_HIDDEN_ROOTS = {
    ".github",
    ".gitlab-ci.yml",
    ".markdownlnt.json",
    ".pre-commit-config.yaml",
    ".vscode",
}

SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "stubs",
}

SKIP_PATHS = {
    Path("meta/generated"),
}

ROOT_PYTHON_FILES = (
    Path("run.py"),
)

SCAN_PYTHON_ROOTS = (
    Path("sciv"),
    Path("scripts"),
)

AREA_ORDER = [
    "root",
    "sciv",
    "sciv/managers",
    "sciv/gameplay",
    "sciv/system",
    "sciv/menus",
    "sciv/helpers",
    "sciv/mixins",
    "sciv/exceptions",
    "sciv/world",
    "sciv/i18n",
    "scripts",
]

TOP_LEVEL_DESCRIPTIONS = {
    ".github": "Repository-level automation and Copilot instructions.",
    ".gitlab-ci.yml": "GitLab CI verification and packaging pipeline.",
    ".markdownlnt.json": "Markdown lint configuration.",
    ".pre-commit-config.yaml": "Pre-commit hook configuration.",
    ".vscode": "VS Code workspace settings and tasks.",
    "CHANGELOG.md": "Generated release changelog.",
    "CREDITS": "Credits and attribution.",
    "Dockerfile": "Container build definition.",
    "LICENSE": "Project license text.",
    "Pipfile": "Alternative Python dependency manifest.",
    "README.md": "Project overview, status, and run instructions.",
    "SCIV.code-workspace": "VS Code workspace definition.",
    "assets": "Shared source assets such as models, textures, shaders, fonts, and icons.",
    "docker-compose.yml": "Container orchestration for local workflows.",
    "known_bugs.md": "Known issues and current rough edges.",
    "makefile": "Common local verification and build shortcuts.",
    "meta": "Project documentation, generated indexes, and technical notes.",
    "mypy.ini": "Mypy configuration.",
    "pyproject.toml": "Python tooling, packaging, lint, and release configuration.",
    "pyrightconfig.json": "Pyright type-checking configuration.",
    "requirements.txt": "Python runtime dependency list.",
    "run.py": "Root launcher that delegates into the package bootstrap.",
    "sciv": "Main application package.",
    "scripts": "Repository maintenance and utility scripts.",
    "typings": "Additional typing support and third-party type information.",
}

AREA_DESCRIPTIONS = {
    "root": "Root-level Python entrypoints and thin wrappers.",
    "sciv": "Core package bootstrap, application host, configuration, and top-level resources.",
    "sciv/managers": "Singleton-backed orchestration for game flow, UI, entities, players, and turns.",
    "sciv/gameplay": "Domain model for players, tiles, cities, units, rules, effects, and other mechanics.",
    "sciv/system": "Engine-facing systems such as rendering, save/load helpers, generators, and effects.",
    "sciv/menus": "Kivy application and screen/widget layers.",
    "sciv/helpers": "Stateless utilities and runtime helper functions.",
    "sciv/mixins": "Reusable patterns such as the singleton and inspection helpers.",
    "sciv/exceptions": "Domain-specific exception types.",
    "sciv/world": "World-adjacent package resources.",
    "sciv/i18n": "Internationalization resources and language data.",
    "scripts": "Developer utilities and repository automation scripts.",
}

DOC_DESCRIPTIONS = {
    "README.md": "Project overview and how to run the game.",
    "known_bugs.md": "Known issues and currently tracked rough edges.",
    "CHANGELOG.md": "Generated release history.",
    ".github/agents/sciv-specialist.agent.md": "Custom SCiv-focused agent that reads repo docs first, makes surgical changes, and updates durable docs.",
    ".github/copilot-instructions.md": "Repo-level Copilot entrypoint that routes future sessions into Git-tracked docs.",
    ".github/instructions/README.md": "Overview of the SCiv dispatcher instruction layer.",
    ".github/instructions/managers.instructions.md": "Routes manager, startup, and turn-related work to the correct technical docs.",
    ".github/instructions/world-generation.instructions.md": "Routes world generation, hexgen, and generator-selection work to the correct technical docs.",
    ".github/instructions/entities-save.instructions.md": "Routes persistence and save/load work to the correct technical docs.",
    ".github/instructions/ui-bridge.instructions.md": "Routes Panda3D/Kivy bridge and UI flow work to the correct technical docs.",
    ".github/instructions/gameplay.instructions.md": "Routes gameplay changes to mechanics and rules docs.",
    ".github/instructions/docs-governance.instructions.md": "Routes documentation and generated-doc maintenance work to the source-of-truth docs.",
    ".github/skills/sciv-project-index/SKILL.md": "Skill for targeted lookup against the generated project index and routing data.",
    ".github/skills/sciv-orientation/SKILL.md": "Orientation skill for ambiguous or cross-cutting SCiv work.",
    ".github/skills/sciv-orientation/references/routing-matrix.md": "Task-to-doc routing matrix used by the orientation skill.",
    "meta/INDEX.md": "Primary documentation hub for humans and coding agents.",
    "meta/todo.md": "Project backlog and improvement list.",
    "meta/technical/agent-workflow.md": "Preferred workflow for SCiv-specialized coding agents and repo-local documentation discipline.",
    "meta/technical/architecture.md": "Subsystem overview and major runtime layers.",
    "meta/technical/actions.md": "One-shot runtime actions, targeting, and callback flow.",
    "meta/technical/city-production.md": "Food, production, border growth, and city-side turn processing.",
    "meta/technical/entities.md": "Entity lifecycle, persistence model, and save/load boundaries.",
    "meta/technical/effects.md": "Persistent modifiers, placement, timing, and effect load behavior.",
    "meta/technical/rules.md": "Game rule registry and configurable rule values.",
    "meta/technical/signals.md": "Curated signal catalog.",
    "meta/technical/startup.md": "Boot path from launcher to live UI.",
    "meta/technical/ui-runtime.md": "Kivy screen runtime, screen contracts, overlays, and input-lock policy.",
    "meta/technical/world-generation.md": "New-game generation flow, generator ownership, and the hexgen pipeline.",
    "meta/technical/state.md": "Shared non-entity runtime state and when to use it.",
    "meta/technical/turns.md": "Turn stages and per-turn processing pipeline.",
    "meta/technical/update-triggers.md": "Maps guarded code areas to the docs that should be reviewed or updated with them.",
    "meta/technical/workings.md": "High-level mechanics overview and hub for focused gameplay docs.",
}

GENERATED_ARTIFACTS = [
    {
        "path": "meta/structure.md",
        "description": "Generated human-readable project map rendered from the index generator.",
    },
    {
        "path": "meta/generated/project-index.json",
        "description": "Generated machine-readable manifest of indexed code and docs.",
    },
    {
        "path": "meta/generated/doc-routing.json",
        "description": "Generated machine-readable routing manifest for subsystem-to-doc guidance.",
    },
]

DOC_ROUTING_RULES = [
    {
        "id": "startup-and-runtime-core",
        "summary": "Startup, bootstrap, loading-screen handoff, and manager initialization order.",
        "task_keywords": [
            "startup",
            "bootstrap",
            "loading screen",
            "manager init",
            "OpenCiv",
            "system.main.ready",
        ],
        "file_globs": [
            "run.py",
            "sciv/__main__.py",
            "sciv/game.py",
            "sciv/managers/**",
        ],
        "dispatcher_instructions": [
            ".github/instructions/managers.instructions.md",
            ".github/instructions/ui-bridge.instructions.md",
        ],
        "read_first": [
            "meta/technical/startup.md",
            "meta/technical/architecture.md",
            "meta/technical/update-triggers.md",
        ],
        "update_docs": [
            "meta/technical/startup.md",
            "meta/technical/architecture.md",
            "meta/technical/update-triggers.md",
        ],
    },
    {
        "id": "world-generation-and-generator-selection",
        "summary": "World generation, generator selection, hexgen terrain creation, resource allocation, and starting-unit placement.",
        "task_keywords": [
            "world generation",
            "generator",
            "map generation",
            "hexgen",
            "heightmap",
            "geoform",
            "river",
            "territory",
            "resource allocation",
            "starting units",
        ],
        "file_globs": [
            "sciv/system/generators/**",
            "sciv/system/subsystems/hexgen/**",
            "sciv/system/game_settings.py",
            "sciv/managers/world.py",
            "sciv/managers/game.py",
            "sciv/gameplay/repositories/generators.py",
        ],
        "dispatcher_instructions": [
            ".github/instructions/world-generation.instructions.md",
            ".github/instructions/managers.instructions.md",
        ],
        "read_first": [
            "meta/technical/world-generation.md",
            "meta/technical/startup.md",
            "meta/technical/architecture.md",
            "meta/technical/update-triggers.md",
        ],
        "update_docs": [
            "meta/technical/world-generation.md",
            "meta/technical/startup.md",
            "meta/technical/architecture.md",
            "meta/technical/update-triggers.md",
        ],
    },
    {
        "id": "turns-and-signals",
        "summary": "Turn pipeline, turn stages, end-turn flow, and turn-related messenger behavior.",
        "task_keywords": [
            "turn",
            "end turn",
            "turn stage",
            "game.turn",
            "signals",
        ],
        "file_globs": [
            "sciv/managers/turn.py",
            "sciv/managers/game.py",
            "sciv/gameplay/**",
        ],
        "dispatcher_instructions": [
            ".github/instructions/managers.instructions.md",
            ".github/instructions/gameplay.instructions.md",
        ],
        "read_first": [
            "meta/technical/turns.md",
            "meta/technical/signals.md",
            "meta/technical/update-triggers.md",
        ],
        "update_docs": [
            "meta/technical/turns.md",
            "meta/technical/signals.md",
            "meta/technical/update-triggers.md",
        ],
    },
    {
        "id": "entities-and-save-load",
        "summary": "Entity lifecycle, entity registration, serialization, save/load, and state boundaries.",
        "task_keywords": [
            "entity",
            "serialization",
            "save",
            "load",
            "state manager",
            "weakref",
        ],
        "file_globs": [
            "sciv/system/entity.py",
            "sciv/system/save_file.py",
            "sciv/managers/entity.py",
            "sciv/managers/state.py",
        ],
        "dispatcher_instructions": [
            ".github/instructions/entities-save.instructions.md",
        ],
        "read_first": [
            "meta/technical/entities.md",
            "meta/technical/state.md",
            "meta/technical/update-triggers.md",
        ],
        "update_docs": [
            "meta/technical/entities.md",
            "meta/technical/state.md",
            "meta/technical/update-triggers.md",
        ],
    },
    {
        "id": "input-picking-and-camera-locks",
        "summary": "World picking, input raycaster activation, camera zoom locks, and input/UI collision gating.",
        "task_keywords": [
            "input",
            "raycaster",
            "picker",
            "picking",
            "collision",
            "zoom lock",
            "camera lock",
        ],
        "file_globs": [
            "sciv/managers/input.py",
            "sciv/system/camera.py",
            "sciv/helpers/input.py",
            "sciv/menus/kivy/mixins/collidable.py",
        ],
        "dispatcher_instructions": [
            ".github/instructions/managers.instructions.md",
            ".github/instructions/ui-bridge.instructions.md",
        ],
        "read_first": [
            "meta/technical/architecture.md",
            "meta/technical/signals.md",
            "meta/technical/update-triggers.md",
        ],
        "update_docs": [
            "meta/technical/architecture.md",
            "meta/technical/signals.md",
            "meta/technical/update-triggers.md",
        ],
    },
    {
        "id": "ui-bridge-and-screens",
        "summary": "Panda3D/Kivy bridge, UI manager, screen flow, and UI-facing signals.",
        "task_keywords": [
            "ui",
            "kivy",
            "screen",
            "bridge",
            "menu",
            "ui runtime",
            "pause menu",
            "save load",
            "panda3d_kivy",
        ],
        "file_globs": [
            "sciv/menus/**",
            "sciv/managers/game.py",
            "sciv/managers/ui.py",
            "sciv/game.py",
        ],
        "dispatcher_instructions": [
            ".github/instructions/ui-bridge.instructions.md",
            ".github/instructions/managers.instructions.md",
        ],
        "read_first": [
            "meta/technical/startup.md",
            "meta/technical/architecture.md",
            "meta/technical/ui-runtime.md",
            "meta/technical/signals.md",
            "meta/technical/update-triggers.md",
        ],
        "update_docs": [
            "meta/technical/startup.md",
            "meta/technical/architecture.md",
            "meta/technical/ui-runtime.md",
            "meta/technical/signals.md",
            "meta/technical/update-triggers.md",
        ],
    },
    {
        "id": "gameplay-rules-and-mechanics",
        "summary": "Gameplay rules, effects, mechanics, and domain-level behavior changes.",
        "task_keywords": [
            "gameplay",
            "rule",
            "effect",
            "unit",
            "city",
            "tile",
            "civic",
            "tech",
        ],
        "file_globs": [
            "sciv/gameplay/**",
        ],
        "dispatcher_instructions": [
            ".github/instructions/gameplay.instructions.md",
        ],
        "read_first": [
            "meta/technical/workings.md",
            "meta/technical/effects.md",
            "meta/technical/actions.md",
            "meta/technical/city-production.md",
            "meta/technical/rules.md",
            "meta/technical/turns.md",
            "meta/technical/entities.md",
            "meta/technical/update-triggers.md",
        ],
        "update_docs": [
            "meta/technical/workings.md",
            "meta/technical/effects.md",
            "meta/technical/actions.md",
            "meta/technical/city-production.md",
            "meta/technical/rules.md",
            "meta/technical/turns.md",
            "meta/technical/entities.md",
            "meta/technical/update-triggers.md",
        ],
    },
    {
        "id": "docs-and-routing",
        "summary": "Documentation, generated indexes, routing rules, repo instructions, custom agents, and docs freshness checks.",
        "task_keywords": [
            "docs",
            "documentation",
            "index",
            "routing",
            "agent",
            "custom agent",
            "workflow",
            "instruction",
            "skill",
            "project index",
            "index helper",
            "generated docs",
        ],
        "file_globs": [
            "meta/**",
            ".github/**",
            "scripts/generate_project_index.py",
            "scripts/query_project_index.py",
            ".gitlab-ci.yml",
            "makefile",
        ],
        "dispatcher_instructions": [
            ".github/instructions/docs-governance.instructions.md",
        ],
        "read_first": [
            "meta/INDEX.md",
            "meta/structure.md",
            "meta/generated/project-index.json",
            "meta/technical/agent-workflow.md",
            "meta/technical/update-triggers.md",
        ],
        "update_docs": [
            "meta/INDEX.md",
            "meta/technical/agent-workflow.md",
            "meta/technical/update-triggers.md",
            "meta/generated/project-index.json",
            "meta/generated/doc-routing.json",
        ],
    },
]

ENTRY_POINTS = [
    {
        "path": "run.py",
        "primary_symbol": "bootstrap()",
        "purpose": "Root launcher that imports and executes package bootstrap.",
    },
    {
        "path": "sciv/__main__.py",
        "primary_symbol": "bootstrap()",
        "purpose": "Package bootstrap that switches into the package directory and starts OpenCiv.",
    },
    {
        "path": "sciv/game.py",
        "primary_symbol": "OpenCiv",
        "purpose": "Main application host that bootstraps Panda3D, Kivy, managers, and assets.",
    },
    {
        "path": "sciv/managers/game.py",
        "primary_symbol": "Game",
        "purpose": "Coordinates game start/load/reset, world generation, and active session state.",
    },
    {
        "path": "sciv/managers/turn.py",
        "primary_symbol": "Turn",
        "purpose": "Owns the turn loop, stage tracking, and turn-related signals.",
    },
]

MODULE_PRIORITY = {
    "run.py": 0,
    "sciv/__main__.py": 1,
    "sciv/game.py": 2,
    "sciv/managers/game.py": 0,
    "sciv/managers/world.py": 1,
    "sciv/managers/entity.py": 2,
    "sciv/managers/turn.py": 3,
    "sciv/managers/ui.py": 4,
    "sciv/managers/input.py": 5,
    "sciv/managers/player.py": 6,
    "sciv/managers/tech.py": 7,
    "sciv/managers/civics.py": 8,
    "sciv/managers/ages.py": 9,
    "sciv/gameplay/player.py": 0,
    "sciv/gameplay/tile.py": 1,
    "sciv/gameplay/unit.py": 2,
    "sciv/gameplay/city.py": 3,
    "sciv/gameplay/rules.py": 4,
    "sciv/gameplay/effect.py": 5,
    "sciv/gameplay/vision.py": 6,
    "sciv/gameplay/diplomacy.py": 7,
    "sciv/gameplay/yields.py": 8,
    "sciv/gameplay/tech.py": 9,
    "sciv/gameplay/civic.py": 10,
    "sciv/gameplay/civilization.py": 11,
    "sciv/system/entity.py": 0,
    "sciv/system/save_file.py": 1,
    "sciv/system/effects.py": 2,
    "sciv/system/actions.py": 3,
    "sciv/system/generators/basic.py": 4,
    "sciv/system/tile_renderer.py": 5,
    "sciv/system/unit_renderer.py": 6,
    "sciv/system/camera.py": 7,
    "sciv/system/atlas.py": 8,
    "sciv/menus/kivy/core.py": 0,
    "sciv/menus/screens/game_ui.py": 1,
    "sciv/mixins/singleton.py": 0,
    "scripts/generate_project_index.py": 0,
    "scripts/check_bad_imports.py": 1,
}

MODULE_SUMMARIES = {
    "run.py": "Root launcher that delegates to package bootstrap.",
    "sciv/__main__.py": "Package bootstrap entrypoint for starting OpenCiv.",
    "sciv/game.py": "Main ShowBase host that wires Panda3D, Kivy, managers, logging, and assets together.",
    "sciv/managers/game.py": "Top-level game coordinator for start, load, reset, and active session state.",
    "sciv/managers/world.py": "Owns world dimensions, tile lookup, tile ownership changes, and world turn work.",
    "sciv/managers/entity.py": "Persistent entity registry and serializer/save-load coordination.",
    "sciv/managers/turn.py": "Turn pipeline owner with turn stages, timings, and turn signals.",
    "sciv/managers/ui.py": "Bridge between runtime events and the Kivy screen layer.",
    "sciv/managers/input.py": "User input parsing and dispatch into gameplay/UI actions.",
    "sciv/managers/player.py": "Player registry and player-related helper accessors.",
    "sciv/managers/tech.py": "Research progression and tech state management.",
    "sciv/managers/civics.py": "Civic tree and civic progression management.",
    "sciv/managers/ages.py": "Age progression and age-related events.",
    "sciv/gameplay/player.py": "Primary player domain object with empire-level state and behavior.",
    "sciv/gameplay/tile.py": "Tile domain object used for world grid state and tile-local mechanics.",
    "sciv/gameplay/unit.py": "Unit domain object for movement, combat, and unit-level turn behavior.",
    "sciv/gameplay/city.py": "City domain object for production, growth, borders, and city-local state.",
    "sciv/gameplay/rules.py": "Rule interface and active SCiv rule implementation.",
    "sciv/gameplay/effect.py": "Gameplay effect objects that modify mechanics over time or in reaction to events.",
    "sciv/gameplay/vision.py": "Visibility and fog-of-war related player state.",
    "sciv/gameplay/diplomacy.py": "Diplomatic relationships and related gameplay concepts.",
    "sciv/gameplay/yields.py": "Yield calculations and value containers used across tiles, cities, and players.",
    "sciv/gameplay/tech.py": "Technology domain object and related research state.",
    "sciv/gameplay/civic.py": "Civic domain object and civic progression state.",
    "sciv/gameplay/civilization.py": "Civilization identity and civilization-level data.",
    "sciv/system/entity.py": "Base entity behavior, serialization hooks, and shared entity identity.",
    "sciv/system/save_file.py": "Save-file abstractions and on-disk persistence helpers.",
    "sciv/system/effects.py": "Effect container/orchestration layer used by gameplay entities.",
    "sciv/system/actions.py": "Stateless action execution helpers for one-shot gameplay actions.",
    "sciv/system/generators/basic.py": "Default world generator implementation.",
    "sciv/system/tile_renderer.py": "Tile rendering system for pushing world state into the scene.",
    "sciv/system/unit_renderer.py": "Unit rendering and placement support.",
    "sciv/system/camera.py": "Civ-style camera behavior and camera controls.",
    "sciv/system/atlas.py": "Generated atlas support for icons and related assets.",
    "sciv/menus/kivy/core.py": "Kivy app host and screen registration for the in-game UI.",
    "sciv/menus/screens/game_ui.py": "Primary in-game screen layer.",
    "sciv/mixins/singleton.py": "Thread-safe singleton implementation used by managers and shared services.",
    "scripts/generate_project_index.py": "Generates the repo-native documentation index for humans and AI tooling.",
    "scripts/query_project_index.py": "Queries the generated project index for targeted lookup of docs, routes, areas, entry points, and modules.",
    "scripts/check_bad_imports.py": "Guards staged Python changes against disallowed `sciv` imports.",
}


@dataclass(frozen=True)
class TopLevelItem:
    path: str
    kind: str
    description: str


@dataclass(frozen=True)
class DocumentationItem:
    path: str
    category: str
    description: str


@dataclass(frozen=True)
class ModuleInfo:
    path: str
    module: str
    area: str
    summary: str
    classes: list[str]
    functions: list[str]
    imports: list[str]
    line_count: int
    parse_error: str | None = None


@dataclass(frozen=True)
class AreaInfo:
    path: str
    description: str
    module_count: int
    line_count: int
    key_modules: list[ModuleInfo]
    modules: list[ModuleInfo]


def is_skipped(relative_path: Path) -> bool:
    if any(part in SKIP_DIR_NAMES for part in relative_path.parts):
        return True
    return any(relative_path == skip or skip in relative_path.parents for skip in SKIP_PATHS)


def repo_relative(path: Path) -> Path:
    return path.relative_to(REPO_ROOT)


def category_for_doc(relative_path: Path) -> str:
    as_posix = relative_path.as_posix()
    if as_posix == "meta/INDEX.md":
        return "start"
    if as_posix.startswith(".github/"):
        return "automation"
    if as_posix.startswith("meta/technical/"):
        return "technical"
    if as_posix.startswith("meta/"):
        return "project"
    return "root"


def category_rank(category: str) -> int:
    ordered = ["start", "root", "project", "technical", "automation"]
    try:
        return ordered.index(category)
    except ValueError:
        return len(ordered)


def area_for_path(relative_path: Path) -> str:
    parts = list(relative_path.parts)
    if not parts:
        return "root"

    if len(parts) == 1:
        return "root"

    if parts[0] == "sciv" and len(parts) > 1:
        second = parts[1]
        if second in {"managers", "gameplay", "system", "menus", "helpers", "mixins", "exceptions", "world", "i18n"}:
            return f"sciv/{second}"
        return "sciv"

    if parts[0] == "scripts":
        return "scripts"

    return parts[0]


def area_rank(area: str) -> tuple[int, str]:
    try:
        return AREA_ORDER.index(area), area
    except ValueError:
        return len(AREA_ORDER), area


def module_name_for(relative_path: Path) -> str:
    if relative_path.name == "__init__.py":
        return ".".join(relative_path.parent.parts)
    return ".".join(relative_path.with_suffix("").parts)


def doc_summary(text: str | None) -> str | None:
    if text is None:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    first_line = stripped.splitlines()[0].strip()
    return first_line if first_line.endswith(".") else f"{first_line}."


def fallback_module_summary(relative_path: Path) -> str:
    as_posix = relative_path.as_posix()
    if as_posix in MODULE_SUMMARIES:
        return MODULE_SUMMARIES[as_posix]

    if relative_path.name == "__init__.py":
        return f"Package module for {relative_path.parent.as_posix()}."

    stem = relative_path.stem.strip("_").replace("_", " ").strip()
    if not stem:
        stem = relative_path.stem.replace("_", " ").strip()

    area = area_for_path(relative_path)
    if area == "sciv/managers":
        return f"Manager module for {stem}."
    if area == "sciv/gameplay":
        return f"Gameplay module for {stem}."
    if area == "sciv/system":
        return f"System module for {stem}."
    if area == "sciv/menus":
        return f"UI module for {stem}."
    if area == "sciv/helpers":
        return f"Helper module for {stem}."
    if area == "sciv/mixins":
        return f"Mixin or shared pattern module for {stem}."
    if area == "scripts":
        return f"Repository utility script for {stem}."
    return f"Python module for {stem}."


def iter_python_paths() -> Iterable[Path]:
    for relative_path in ROOT_PYTHON_FILES:
        absolute_path = REPO_ROOT / relative_path
        if absolute_path.exists() and not is_skipped(relative_path):
            yield relative_path

    for root in SCAN_PYTHON_ROOTS:
        absolute_root = REPO_ROOT / root
        if not absolute_root.exists():
            continue

        for absolute_path in sorted(absolute_root.rglob("*.py")):
            relative_path = repo_relative(absolute_path)
            if is_skipped(relative_path):
                continue
            yield relative_path


def parse_python_module(relative_path: Path) -> ModuleInfo:
    absolute_path = REPO_ROOT / relative_path
    source = absolute_path.read_text(encoding="utf-8")
    line_count = len(source.splitlines())

    try:
        tree = ast.parse(source, filename=relative_path.as_posix(), type_comments=True)
    except SyntaxError as exc:
        return ModuleInfo(
            path=relative_path.as_posix(),
            module=module_name_for(relative_path),
            area=area_for_path(relative_path),
            summary=fallback_module_summary(relative_path),
            classes=[],
            functions=[],
            imports=[],
            line_count=line_count,
            parse_error=f"{exc.msg} (line {exc.lineno}, column {exc.offset})",
        )

    classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    functions = [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names if alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = f"{'.' * node.level}{node.module or ''}"
            if module:
                imports.add(module)

    summary = doc_summary(ast.get_docstring(tree)) or fallback_module_summary(relative_path)

    return ModuleInfo(
        path=relative_path.as_posix(),
        module=module_name_for(relative_path),
        area=area_for_path(relative_path),
        summary=summary,
        classes=sorted(classes),
        functions=sorted(functions),
        imports=sorted(imports),
        line_count=line_count,
    )


def collect_top_level_items() -> list[TopLevelItem]:
    items: list[TopLevelItem] = []

    for absolute_path in sorted(REPO_ROOT.iterdir()):
        name = absolute_path.name
        if name.startswith(".") and name not in INCLUDED_HIDDEN_ROOTS:
            continue

        description = TOP_LEVEL_DESCRIPTIONS.get(name)
        if description is None:
            description = "Project directory." if absolute_path.is_dir() else "Project file."

        items.append(
            TopLevelItem(
                path=name,
                kind="directory" if absolute_path.is_dir() else "file",
                description=description,
            )
        )

    return items


def collect_documentation_items() -> list[DocumentationItem]:
    candidates: set[Path] = set()

    for relative_path in (Path("README.md"), Path("known_bugs.md"), Path("CHANGELOG.md")):
        if (REPO_ROOT / relative_path).exists():
            candidates.add(relative_path)

    github_root = REPO_ROOT / ".github"
    if github_root.exists():
        for absolute_path in github_root.rglob("*.md"):
            relative_path = repo_relative(absolute_path)
            if is_skipped(relative_path):
                continue
            candidates.add(relative_path)

    for root in (Path("meta"),):
        absolute_root = REPO_ROOT / root
        if not absolute_root.exists():
            continue

        for absolute_path in absolute_root.rglob("*.md"):
            relative_path = repo_relative(absolute_path)
            if is_skipped(relative_path) or relative_path == Path("meta/structure.md"):
                continue
            candidates.add(relative_path)

    items = [
        DocumentationItem(
            path=relative_path.as_posix(),
            category=category_for_doc(relative_path),
            description=DOC_DESCRIPTIONS.get(relative_path.as_posix(), "Repository documentation."),
        )
        for relative_path in candidates
    ]

    return sorted(items, key=lambda item: (category_rank(item.category), item.path))


def collect_modules() -> list[ModuleInfo]:
    return [parse_python_module(relative_path) for relative_path in iter_python_paths()]


def select_key_modules(modules: list[ModuleInfo], limit: int = 12) -> list[ModuleInfo]:
    ordered = sorted(modules, key=lambda module: (MODULE_PRIORITY.get(module.path, 999), module.path))
    return ordered[: min(limit, len(ordered))]


def build_areas(modules: list[ModuleInfo]) -> list[AreaInfo]:
    grouped: dict[str, list[ModuleInfo]] = {}
    for module in modules:
        grouped.setdefault(module.area, []).append(module)

    areas: list[AreaInfo] = []
    for area_name, area_modules in grouped.items():
        ordered_modules = sorted(area_modules, key=lambda module: module.path)
        areas.append(
            AreaInfo(
                path=area_name,
                description=AREA_DESCRIPTIONS.get(area_name, "Indexed Python area."),
                module_count=len(ordered_modules),
                line_count=sum(module.line_count for module in ordered_modules),
                key_modules=select_key_modules(ordered_modules),
                modules=ordered_modules,
            )
        )

    return sorted(areas, key=lambda area: area_rank(area.path))


def link_from_structure(path: str) -> str:
    relative_link = Path(os.path.relpath(REPO_ROOT / path, OUTPUT_MARKDOWN.parent)).as_posix()
    return f"[{path}]({relative_link})"


def escape_markdown(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def summarize_names(names: list[str], label: str, limit: int = 4) -> str:
    if not names:
        return ""

    shown = ", ".join(f"`{name}`" for name in names[:limit])
    remaining = len(names) - limit
    suffix = f" +{remaining} more" if remaining > 0 else ""
    return f"{label}: {shown}{suffix}"


def format_symbols(module: ModuleInfo) -> str:
    parts = [
        summarize_names(module.classes, "classes"),
        summarize_names(module.functions, "functions"),
    ]
    formatted = "; ".join(part for part in parts if part)
    return formatted if formatted else "-"


def render_table(rows: list[list[str]], headers: list[str]) -> list[str]:
    table = [
        f"| {' | '.join(headers)} |",
        f"| {' | '.join('---' for _ in headers)} |",
    ]
    for row in rows:
        table.append(f"| {' | '.join(row)} |")
    return table


def render_structure(top_level: list[TopLevelItem], docs: list[DocumentationItem], areas: list[AreaInfo]) -> str:
    module_count = sum(area.module_count for area in areas)
    doc_count = len(docs)

    lines: list[str] = [
        "# SCiv Project Structure",
        "",
        "> Generated by [`scripts/generate_project_index.py`](../scripts/generate_project_index.py). Do not hand-edit this file.",
        "> Start with the [Documentation Index](INDEX.md) for the curated reading order.",
        "",
        "## Snapshot",
        "",
        f"- Indexed Python modules: `{module_count}`",
        f"- Indexed documentation files: `{doc_count}`",
        f"- Runtime areas: `{len(areas)}`",
        "- Machine-readable manifest: [`meta/generated/project-index.json`](generated/project-index.json)",
        "",
        "## Entry points",
        "",
    ]

    entry_rows = [
        [
            link_from_structure(entry["path"]),
            f"`{entry['primary_symbol']}`",
            escape_markdown(entry["purpose"]),
        ]
        for entry in ENTRY_POINTS
    ]
    lines.extend(render_table(entry_rows, ["Path", "Primary symbol", "Purpose"]))

    lines.extend(
        [
            "",
            "## Top-level workspace map",
            "",
        ]
    )

    top_rows = [
        [link_from_structure(item.path), item.kind, escape_markdown(item.description)]
        for item in top_level
    ]
    lines.extend(render_table(top_rows, ["Path", "Kind", "Role"]))

    lines.extend(
        [
            "",
            "## Documentation map",
            "",
        ]
    )

    doc_rows = [
        [link_from_structure(item.path), item.category, escape_markdown(item.description)]
        for item in docs
    ]
    lines.extend(render_table(doc_rows, ["Path", "Category", "Purpose"]))

    lines.extend(
        [
            "",
            "## Generated artifacts",
            "",
        ]
    )

    generated_rows = [
        [link_from_structure(item["path"]), escape_markdown(item["description"])]
        for item in GENERATED_ARTIFACTS
    ]
    lines.extend(render_table(generated_rows, ["Path", "Purpose"]))

    lines.extend(
        [
            "",
            "## Indexed runtime areas",
            "",
            "The sections below show representative modules for each indexed Python area. Use `meta/generated/project-index.json` when you need the full module list.",
        ]
    )

    for area in areas:
        lines.extend(
            [
                "",
                f"### `{area.path}`",
                "",
                area.description,
                "",
                f"- Modules indexed: `{area.module_count}`",
                f"- Indexed lines: `{area.line_count}`",
                "",
            ]
        )

        module_rows = [
            [
                link_from_structure(module.path),
                format_symbols(module),
                escape_markdown(module.summary),
            ]
            for module in area.key_modules
        ]
        lines.extend(render_table(module_rows, ["Representative module", "Top-level symbols", "Summary"]))

    lines.append("")
    return "\n".join(lines)


def write_or_check(path: Path, content: str, check: bool) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return True

    if check:
        print(f"stale generated file: {path.relative_to(REPO_ROOT).as_posix()}")
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def build_index() -> dict[str, Any]:
    top_level = collect_top_level_items()
    docs = collect_documentation_items()
    modules = collect_modules()
    areas = build_areas(modules)

    return {
        "project": {
            "name": "SCiv",
            "root": ".",
            "documentation_root": "meta",
        },
        "entry_points": ENTRY_POINTS,
        "top_level": [asdict(item) for item in top_level],
        "documentation": [asdict(item) for item in docs],
        "generated_artifacts": GENERATED_ARTIFACTS,
        "doc_routing": DOC_ROUTING_RULES,
        "areas": [asdict(area) for area in areas],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the SCiv project index and structure docs.")
    parser.add_argument("--check", action="store_true", help="Fail if generated files are out of date.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    index = build_index()
    routing_output = json.dumps(
        {
            "skill": "sciv-orientation",
            "entrypoint": ".github/copilot-instructions.md",
            "instructions_root": ".github/instructions",
            "manifest": "meta/generated/doc-routing.json",
            "rules": DOC_ROUTING_RULES,
        },
        indent=2,
        ensure_ascii=False,
    ) + "\n"

    top_level = [TopLevelItem(**item) for item in index["top_level"]]
    docs = [DocumentationItem(**item) for item in index["documentation"]]
    areas: list[AreaInfo] = []
    for raw_area in index["areas"]:
        key_modules = [ModuleInfo(**module) for module in raw_area["key_modules"]]
        modules = [ModuleInfo(**module) for module in raw_area["modules"]]
        areas.append(
            AreaInfo(
                path=raw_area["path"],
                description=raw_area["description"],
                module_count=raw_area["module_count"],
                line_count=raw_area["line_count"],
                key_modules=key_modules,
                modules=modules,
            )
        )

    json_output = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    markdown_output = render_structure(top_level, docs, areas)

    json_ok = write_or_check(OUTPUT_JSON, json_output, check=args.check)
    routing_ok = write_or_check(OUTPUT_ROUTING_JSON, routing_output, check=args.check)
    markdown_ok = write_or_check(OUTPUT_MARKDOWN, markdown_output, check=args.check)

    if args.check:
        if json_ok and routing_ok and markdown_ok:
            print("project index is up to date")
            return 0

        print("project index is stale; run `python scripts/generate_project_index.py`")
        return 1

    print(f"wrote {OUTPUT_JSON.relative_to(REPO_ROOT).as_posix()}")
    print(f"wrote {OUTPUT_ROUTING_JSON.relative_to(REPO_ROOT).as_posix()}")
    print(f"wrote {OUTPUT_MARKDOWN.relative_to(REPO_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())