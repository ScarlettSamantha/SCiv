#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified SCiv project-index helper for generation, browsing, querying, and validation."""

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

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
    Path("changelog.py"),
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
    "CHANGELOG.md": "Project changelog maintained through the repo helper workflow.",
    "CREDITS": "Credits and attribution.",
    "Dockerfile": "Container build definition.",
    "LICENSE": "Project license text.",
    "Pipfile": "Alternative Python dependency manifest.",
    "README.md": "Project overview, status, and run instructions.",
    "SCIV.code-workspace": "VS Code workspace definition.",
    "assets": "Shared source assets such as models, textures, shaders, fonts, and icons.",
    "changelog.py": "Repository changelog helper and release metadata utility.",
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
    "CHANGELOG.md": "Project changelog maintained through the helper-driven gitmoji and release workflow.",
    ".github/agents/sciv-specialist.agent.md": "Custom SCiv-focused agent that reads repo docs first, makes surgical changes, and updates durable docs.",
    ".github/copilot-instructions.md": "Repo-level Copilot entrypoint that routes future sessions into Git-tracked docs.",
    ".github/instructions/README.md": "Overview of the SCiv dispatcher instruction layer.",
    ".github/instructions/managers.instructions.md": "Routes manager, startup, and turn-related work to the correct technical docs.",
    ".github/instructions/world-generation.instructions.md": "Routes world generation, hexgen, and generator-selection work to the correct technical docs.",
    ".github/instructions/entities-save.instructions.md": "Routes persistence and save/load work to the correct technical docs.",
    ".github/instructions/ui-bridge.instructions.md": "Routes Panda3D/Kivy bridge and UI flow work to the correct technical docs.",
    ".github/instructions/gameplay.instructions.md": "Routes gameplay changes to mechanics and rules docs.",
    ".github/instructions/docs-governance.instructions.md": "Routes documentation and generated-doc maintenance work to the source-of-truth docs.",
    ".github/instructions/python-conventions.instructions.md": "Routes Python 3.14, typing, and Pyright workflow changes to the canonical conventions docs.",
    ".github/skills/sciv-project-index/SKILL.md": "Skill for targeted lookup against the generated project index and routing data.",
    ".github/skills/sciv-orientation/SKILL.md": "Orientation skill for ambiguous or cross-cutting SCiv work.",
    ".github/skills/sciv-orientation/references/routing-matrix.md": "Task-to-doc routing matrix used by the orientation skill.",
    "meta/INDEX.md": "Primary documentation hub for humans and coding agents.",
    "meta/todo.md": "Project backlog and improvement list.",
    "meta/technical/agent-workflow.md": "Preferred workflow for SCiv-specialized coding agents and repo-local documentation discipline.",
    "meta/technical/architecture.md": "Subsystem overview and major runtime layers.",
    "meta/technical/actions.md": "One-shot runtime actions, targeting, and callback flow.",
    "meta/technical/changelog-workflow.md": "Canonical `CHANGELOG.md` maintenance workflow, gitmoji convention, and release/tag helper usage.",
    "meta/technical/city-production.md": "Food, production, border growth, and city-side turn processing.",
    "meta/technical/entities.md": "Entity lifecycle, persistence model, and save/load boundaries.",
    "meta/technical/effects.md": "Persistent modifiers, placement, timing, and effect load behavior.",
    "meta/technical/project-index-helper.md": "Unified project-index helper commands, generated artifacts, and human/AI lookup workflow.",
    "meta/technical/python-conventions.md": "Python 3.14 baseline, strong typing expectations, and Pyright-first authoring rules.",
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
        "description": "Generated human-readable project map rendered from the index helper.",
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
            "scripts/index.py",
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
            "meta/technical/project-index-helper.md",
            "meta/technical/agent-workflow.md",
            "meta/technical/update-triggers.md",
        ],
        "update_docs": [
            "meta/INDEX.md",
            "meta/technical/project-index-helper.md",
            "meta/technical/agent-workflow.md",
            "meta/technical/update-triggers.md",
            "meta/generated/project-index.json",
            "meta/generated/doc-routing.json",
        ],
    },
    {
        "id": "python-conventions-and-typing",
        "summary": "Python source, typing/tooling configuration, and repository Python authoring workflow.",
        "task_keywords": [
            "python",
            "typing",
            "pyright",
            "type checking",
            "python conventions",
            "future annotations",
        ],
        "file_globs": [
            "run.py",
            "sciv/**/*.py",
            "scripts/**/*.py",
            "pyproject.toml",
            "pyrightconfig.json",
        ],
        "dispatcher_instructions": [
            ".github/instructions/python-conventions.instructions.md",
        ],
        "read_first": [
            "meta/technical/python-conventions.md",
            "meta/technical/agent-workflow.md",
            "meta/technical/update-triggers.md",
        ],
        "update_docs": [
            "meta/technical/python-conventions.md",
            "meta/technical/agent-workflow.md",
            "meta/technical/update-triggers.md",
        ],
    },
    {
        "id": "changelog-and-contributor-workflow",
        "summary": "CHANGELOG maintenance, gitmoji/ticket entry conventions, release tagging, and contributor workflow completion rules.",
        "task_keywords": [
            "changelog",
            "gitmoji",
            "release notes",
            "release tag",
            "workflow",
            "contributor workflow",
            "changelog helper",
        ],
        "file_globs": [
            "CHANGELOG.md",
            "changelog.py",
            "makefile",
            "meta/technical/changelog-workflow.md",
        ],
        "dispatcher_instructions": [
            ".github/instructions/docs-governance.instructions.md",
        ],
        "read_first": [
            "meta/technical/changelog-workflow.md",
            "meta/technical/agent-workflow.md",
            "meta/technical/update-triggers.md",
        ],
        "update_docs": [
            "meta/technical/changelog-workflow.md",
            "meta/technical/agent-workflow.md",
            "meta/INDEX.md",
            "meta/technical/update-triggers.md",
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
    "changelog.py": 1,
    "sciv/__main__.py": 2,
    "sciv/game.py": 3,
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
    "scripts/index.py": 0,
    "scripts/generate_project_index.py": 1,
    "scripts/query_project_index.py": 2,
    "scripts/check_bad_imports.py": 3,
}

MODULE_SUMMARIES = {
    "run.py": "Root launcher that delegates to package bootstrap.",
    "changelog.py": "Repository changelog helper for entries, release preparation, and version sync.",
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
    "scripts/index.py": "Unified project-index helper for generation, browsing, querying, and freshness checks.",
    "scripts/generate_project_index.py": "Compatibility wrapper for the unified project-index helper's generate/check flow.",
    "scripts/query_project_index.py": "Compatibility wrapper for the unified project-index helper's query flow.",
    "scripts/check_bad_imports.py": "Guards staged Python changes against disallowed `sciv` imports.",
}

KIND_ORDER = {
    "doc": 0,
    "entry": 1,
    "route": 2,
    "area": 3,
    "module": 4,
    "artifact": 5,
    "top": 6,
}
KIND_CHOICES = ["all", *KIND_ORDER.keys()]
LIST_TARGET_KIND = {
    "docs": "doc",
    "entries": "entry",
    "routes": "route",
    "areas": "area",
    "modules": "module",
    "artifacts": "artifact",
    "top": "top",
}


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    """Help formatter with preserved examples and default values."""


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


@dataclass(frozen=True)
class IndexDataset:
    top_level: list[TopLevelItem]
    docs: list[DocumentationItem]
    modules: list[ModuleInfo]
    areas: list[AreaInfo]


@dataclass(frozen=True)
class GenerationOutputs:
    dataset: IndexDataset
    index: dict[str, Any]
    json_output: str
    routing_output: str
    markdown_output: str


@dataclass(frozen=True)
class FreshnessReport:
    missing_paths: list[Path]
    stale_paths: list[Path]

    @property
    def is_fresh(self) -> bool:
        return not self.missing_paths and not self.stale_paths

    def affected_paths(self) -> list[Path]:
        return [*self.missing_paths, *self.stale_paths]


@dataclass(frozen=True)
class RuntimeIndex:
    index: dict[str, Any]
    freshness: FreshnessReport


@dataclass(frozen=True)
class QueryOptions:
    refresh_if_stale: bool
    require_fresh: bool


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
    if not parts or len(parts) == 1:
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

    meta_root = REPO_ROOT / "meta"
    if meta_root.exists():
        for absolute_path in meta_root.rglob("*.md"):
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



def build_dataset() -> IndexDataset:
    modules = collect_modules()
    return IndexDataset(
        top_level=collect_top_level_items(),
        docs=collect_documentation_items(),
        modules=modules,
        areas=build_areas(modules),
    )



def build_index(dataset: IndexDataset) -> dict[str, Any]:
    return {
        "project": {
            "name": "SCiv",
            "root": ".",
            "documentation_root": "meta",
        },
        "entry_points": ENTRY_POINTS,
        "top_level": [asdict(item) for item in dataset.top_level],
        "documentation": [asdict(item) for item in dataset.docs],
        "generated_artifacts": GENERATED_ARTIFACTS,
        "doc_routing": DOC_ROUTING_RULES,
        "areas": [asdict(area) for area in dataset.areas],
    }



def render_routing_manifest() -> str:
    return json.dumps(
        {
            "skill": "sciv-orientation",
            "entrypoint": ".github/copilot-instructions.md",
            "instructions_root": ".github/instructions",
            "manifest": "meta/generated/doc-routing.json",
            "generator": "scripts/index.py",
            "rules": DOC_ROUTING_RULES,
        },
        indent=2,
        ensure_ascii=False,
    ) + "\n"



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



def render_structure(dataset: IndexDataset) -> str:
    module_count = sum(area.module_count for area in dataset.areas)
    doc_count = len(dataset.docs)

    lines: list[str] = [
        "# SCiv Project Structure",
        "",
        "> Generated by [`scripts/index.py`](../scripts/index.py). Do not hand-edit this file.",
        "> Start with the [Documentation Index](INDEX.md) for the curated reading order.",
        "",
        "## Snapshot",
        "",
        f"- Indexed Python modules: `{module_count}`",
        f"- Indexed documentation files: `{doc_count}`",
        f"- Runtime areas: `{len(dataset.areas)}`",
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
        for item in dataset.top_level
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
        for item in dataset.docs
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

    for area in dataset.areas:
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



def build_generation_outputs() -> GenerationOutputs:
    dataset = build_dataset()
    index = build_index(dataset)
    return GenerationOutputs(
        dataset=dataset,
        index=index,
        json_output=json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        routing_output=render_routing_manifest(),
        markdown_output=render_structure(dataset),
    )



def read_existing_output(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")



def freshness_report(outputs: GenerationOutputs) -> FreshnessReport:
    expected_by_path = {
        OUTPUT_JSON: outputs.json_output,
        OUTPUT_ROUTING_JSON: outputs.routing_output,
        OUTPUT_MARKDOWN: outputs.markdown_output,
    }
    missing_paths: list[Path] = []
    stale_paths: list[Path] = []

    for path, expected in expected_by_path.items():
        current = read_existing_output(path)
        if current is None:
            missing_paths.append(path)
        elif current != expected:
            stale_paths.append(path)

    return FreshnessReport(missing_paths=missing_paths, stale_paths=stale_paths)



def relative_paths(paths: Iterable[Path]) -> list[str]:
    return [path.relative_to(REPO_ROOT).as_posix() for path in paths]



def write_outputs(outputs: GenerationOutputs) -> list[Path]:
    written_paths: list[Path] = []
    content_by_path = {
        OUTPUT_JSON: outputs.json_output,
        OUTPUT_ROUTING_JSON: outputs.routing_output,
        OUTPUT_MARKDOWN: outputs.markdown_output,
    }

    for path, content in content_by_path.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written_paths.append(path)

    return written_paths



def format_generate_summary(outputs: GenerationOutputs, report: FreshnessReport, *, check: bool) -> list[str]:
    if check and report.is_fresh:
        return ["project index is up to date"]

    if check:
        lines = [
            "project index is stale",
            f"Run `python3 scripts/index.py generate` to refresh {', '.join(relative_paths(report.affected_paths()))}.",
        ]
        return lines

    written = relative_paths(write_outputs(outputs))
    return [f"wrote {path}" for path in written]



def run_generate(check: bool) -> int:
    outputs = build_generation_outputs()
    report = freshness_report(outputs)
    lines = format_generate_summary(outputs, report, check=check)
    for line in lines:
        print(line)
    return 0 if (not check or report.is_fresh) else 1



def normalize(value: Any) -> str:
    return " ".join(str(value).lower().split())



def preview(values: Iterable[Any], limit: int = 5) -> str:
    items = [str(value) for value in values]
    if not items:
        return "-"

    shown = ", ".join(items[:limit])
    remaining = len(items) - limit
    suffix = f" +{remaining} more" if remaining > 0 else ""
    return f"{shown}{suffix}"



def load_existing_index() -> dict[str, Any]:
    if not OUTPUT_JSON.exists():
        raise FileNotFoundError(OUTPUT_JSON)
    return json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))



def describe_freshness_issue(report: FreshnessReport) -> str:
    details: list[str] = []
    if report.missing_paths:
        details.append(f"missing: {', '.join(relative_paths(report.missing_paths))}")
    if report.stale_paths:
        details.append(f"stale: {', '.join(relative_paths(report.stale_paths))}")
    return "; ".join(details)



def resolve_runtime_index(options: QueryOptions) -> RuntimeIndex:
    outputs = build_generation_outputs()
    report = freshness_report(outputs)

    if report.missing_paths:
        if options.refresh_if_stale:
            write_outputs(outputs)
            report = FreshnessReport(missing_paths=[], stale_paths=[])
            return RuntimeIndex(index=outputs.index, freshness=report)

        missing = ", ".join(relative_paths(report.missing_paths))
        raise SystemExit(
            "Missing generated project-index artifacts: "
            f"{missing}. Run `python3 scripts/index.py generate` or rerun with `--refresh-if-stale`."
        )

    if report.stale_paths:
        if options.refresh_if_stale:
            write_outputs(outputs)
            report = FreshnessReport(missing_paths=[], stale_paths=[])
            return RuntimeIndex(index=outputs.index, freshness=report)

        if options.require_fresh:
            raise SystemExit(
                "Generated project-index artifacts are stale "
                f"({describe_freshness_issue(report)}). Run `python3 scripts/index.py generate` "
                "or rerun with `--refresh-if-stale`."
            )

        print(
            "warning: generated project-index artifacts are stale "
            f"({describe_freshness_issue(report)}); using the existing manifest. "
            "Run `python3 scripts/index.py generate` to refresh.",
            file=sys.stderr,
        )

    return RuntimeIndex(index=load_existing_index(), freshness=report)



def iter_index_items(index: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for item in index.get("documentation", []):
        yield {**item, "kind": "doc", "key": item["path"]}

    for item in index.get("entry_points", []):
        yield {**item, "kind": "entry", "key": item["path"]}

    for item in index.get("doc_routing", []):
        yield {**item, "kind": "route", "key": item["id"]}

    for item in index.get("generated_artifacts", []):
        yield {**item, "kind": "artifact", "key": item["path"]}

    for item in index.get("top_level", []):
        yield {**item, "kind": "top", "key": item["path"]}

    for area in index.get("areas", []):
        yield {**area, "kind": "area", "key": area["path"]}

        for module in area.get("modules", []):
            yield {**module, "kind": "module", "key": module["path"]}



def search_fields(item: dict[str, Any]) -> list[Any]:
    kind = item["kind"]

    if kind == "doc":
        return [item.get("path"), item.get("description"), item.get("category")]

    if kind == "entry":
        return [item.get("path"), item.get("primary_symbol"), item.get("purpose")]

    if kind == "route":
        return [
            item.get("id"),
            item.get("summary"),
            item.get("task_keywords", []),
            item.get("file_globs", []),
            item.get("read_first", []),
            item.get("dispatcher_instructions", []),
            item.get("update_docs", []),
        ]

    if kind == "artifact":
        return [item.get("path"), item.get("description")]

    if kind == "top":
        return [item.get("path"), item.get("kind"), item.get("description")]

    if kind == "area":
        return [
            item.get("path"),
            item.get("description"),
            item.get("module_count"),
            item.get("line_count"),
            [module.get("path") for module in item.get("key_modules", [])],
        ]

    return [
        item.get("path"),
        item.get("module"),
        item.get("summary"),
        item.get("area"),
        item.get("classes", []),
        item.get("functions", []),
    ]



def score_item(query: str, tokens: list[str], item: dict[str, Any]) -> int:
    normalized_query = normalize(query)
    score = 0

    for index, field in enumerate(search_fields(item)):
        field_text = normalize(field)
        if not field_text:
            continue

        weight = max(8, 50 - (index * 6))

        if field_text == normalized_query:
            score += weight + 120
        elif normalized_query in field_text:
            score += weight + 40

        field_parts = [part for part in re.split(r"[^a-z0-9]+", field_text) if part]

        for token in tokens:
            if token == field_text:
                score += weight + 20
            elif len(token) < 3 and token in field_parts:
                score += max(5, weight // max(1, len(tokens)))
            elif len(token) >= 3 and token in field_text:
                score += max(5, weight // max(1, len(tokens)))

    return score



def matches_kind(item_kind: str, requested_kind: str) -> bool:
    return requested_kind == "all" or item_kind == requested_kind



def search_index(index: dict[str, Any], query: str, requested_kind: str, limit: int) -> list[dict[str, Any]]:
    tokens = [token for token in normalize(query).split(" ") if token]
    results: list[tuple[int, dict[str, Any]]] = []

    for item in iter_index_items(index):
        if not matches_kind(item["kind"], requested_kind):
            continue

        score = score_item(query, tokens, item)
        if score > 0:
            results.append((score, item))

    results.sort(
        key=lambda pair: (
            -pair[0],
            KIND_ORDER.get(pair[1]["kind"], 999),
            str(pair[1].get("key", "")),
        )
    )

    return [{"score": score, **item} for score, item in results[:limit]]



def find_items(index: dict[str, Any], target: str, requested_kind: str) -> list[dict[str, Any]]:
    normalized_target = normalize(target)
    exact_matches: list[dict[str, Any]] = []
    partial_matches: list[dict[str, Any]] = []

    for item in iter_index_items(index):
        if not matches_kind(item["kind"], requested_kind):
            continue

        candidates = [item.get("key"), item.get("path"), item.get("id"), item.get("module")]
        normalized_candidates = [normalize(candidate) for candidate in candidates if candidate]

        if any(candidate == normalized_target for candidate in normalized_candidates):
            exact_matches.append(item)
            continue

        if any(normalized_target in candidate for candidate in normalized_candidates):
            partial_matches.append(item)

    matches = exact_matches if exact_matches else partial_matches
    return sorted(matches, key=lambda item: (KIND_ORDER.get(item["kind"], 999), str(item.get("key", ""))))



def resolve_kind_query(
    index: dict[str, Any],
    query: str,
    requested_kind: str,
    limit: int,
) -> tuple[str | None, list[dict[str, Any]]]:
    matches = find_items(index, query, requested_kind)
    if matches:
        return "show", matches

    results = search_index(index, query, requested_kind, limit)
    if results:
        return "search", results

    return None, []



def format_item(item: dict[str, Any]) -> str:
    lines = [f"[{item['kind']}] {item['key']}"]
    kind = item["kind"]

    if kind == "doc":
        lines.append(f"  Category: {item.get('category', '-')}")
        lines.append(f"  Purpose: {item.get('description', '-')}")
    elif kind == "entry":
        lines.append(f"  Symbol: {item.get('primary_symbol', '-')}")
        lines.append(f"  Purpose: {item.get('purpose', '-')}")
    elif kind == "route":
        lines.append(f"  Summary: {item.get('summary', '-')}")
        lines.append(f"  Keywords: {preview(item.get('task_keywords', []))}")
        lines.append(f"  Files: {preview(item.get('file_globs', []))}")
        lines.append(f"  Dispatchers: {preview(item.get('dispatcher_instructions', []))}")
        lines.append(f"  Read first: {preview(item.get('read_first', []))}")
        lines.append(f"  Update docs: {preview(item.get('update_docs', []))}")
    elif kind == "artifact":
        lines.append(f"  Purpose: {item.get('description', '-')}")
    elif kind == "top":
        lines.append(f"  Kind: {item.get('kind', '-')}")
        lines.append(f"  Role: {item.get('description', '-')}")
    elif kind == "area":
        lines.append(f"  Description: {item.get('description', '-')}")
        lines.append(f"  Modules: {item.get('module_count', '-')}")
        lines.append(f"  Indexed lines: {item.get('line_count', '-')}")
        lines.append(
            f"  Key modules: {preview([module.get('path') for module in item.get('key_modules', []) if module.get('path')])}"
        )
    elif kind == "module":
        lines.append(f"  Module: {item.get('module', '-')}")
        lines.append(f"  Area: {item.get('area', '-')}")
        lines.append(f"  Summary: {item.get('summary', '-')}")
        lines.append(f"  Classes: {preview(item.get('classes', []))}")
        lines.append(f"  Functions: {preview(item.get('functions', []))}")
        if item.get("parse_error"):
            lines.append(f"  Parse error: {item['parse_error']}")

    if "score" in item:
        lines.append(f"  Score: {item['score']}")

    return "\n".join(lines)



def list_items(index: dict[str, Any], target: str, query: str | None, limit: int) -> list[dict[str, Any]]:
    kind = LIST_TARGET_KIND[target]
    if query:
        return search_index(index, query, kind, limit)

    items = [item for item in iter_index_items(index) if item["kind"] == kind]
    items.sort(key=lambda item: str(item.get("key", "")))
    return items[:limit]



def build_stats(index: dict[str, Any], freshness: FreshnessReport) -> dict[str, Any]:
    modules = [item for item in iter_index_items(index) if item["kind"] == "module"]
    docs = index.get("documentation", [])
    routes = index.get("doc_routing", [])
    areas = index.get("areas", [])
    parse_errors = [
        {
            "path": module["path"],
            "parse_error": module["parse_error"],
        }
        for module in modules
        if module.get("parse_error")
    ]

    return {
        "project": index.get("project", {}),
        "counts": {
            "top_level": len(index.get("top_level", [])),
            "documentation": len(docs),
            "generated_artifacts": len(index.get("generated_artifacts", [])),
            "entry_points": len(index.get("entry_points", [])),
            "routes": len(routes),
            "areas": len(areas),
            "modules": len(modules),
            "parse_errors": len(parse_errors),
        },
        "freshness": {
            "is_fresh": freshness.is_fresh,
            "missing": relative_paths(freshness.missing_paths),
            "stale": relative_paths(freshness.stale_paths),
        },
        "areas": [
            {
                "path": area["path"],
                "module_count": area["module_count"],
                "line_count": area["line_count"],
            }
            for area in areas
        ],
        "parse_errors": parse_errors,
    }



def format_stats(stats: dict[str, Any]) -> str:
    counts = stats["counts"]
    freshness = stats["freshness"]
    lines = [
        f"Project: {stats['project'].get('name', 'SCiv')}",
        "",
        "Counts:",
        f"  Top-level items: {counts['top_level']}",
        f"  Documentation files: {counts['documentation']}",
        f"  Generated artifacts: {counts['generated_artifacts']}",
        f"  Entry points: {counts['entry_points']}",
        f"  Routing rules: {counts['routes']}",
        f"  Areas: {counts['areas']}",
        f"  Modules: {counts['modules']}",
        f"  Parse errors: {counts['parse_errors']}",
        "",
        f"Freshness: {'fresh' if freshness['is_fresh'] else 'stale'}",
    ]

    if freshness["missing"]:
        lines.append(f"  Missing: {', '.join(freshness['missing'])}")
    if freshness["stale"]:
        lines.append(f"  Stale: {', '.join(freshness['stale'])}")

    if stats["parse_errors"]:
        lines.extend(
            [
                "",
                "Parse errors:",
                *[f"  - {item['path']}: {item['parse_error']}" for item in stats["parse_errors"]],
            ]
        )

    return "\n".join(lines)



def build_doctor_report(outputs: GenerationOutputs, freshness: FreshnessReport) -> dict[str, Any]:
    stats: dict[str, Any] = build_stats(outputs.index, freshness)
    advice: list[str] = []
    if freshness.is_fresh:
        advice.append("Generated project-index artifacts are current.")
    else:
        advice.append("Run `python3 scripts/index.py generate` to refresh stale or missing artifacts.")
        advice.append("Use `--refresh-if-stale` with read-only commands when you want the helper to repair them first.")

    return {
        "freshness": stats["freshness"],
        "counts": stats["counts"],
        "parse_errors": stats["parse_errors"],
        "advice": advice,
    }



def format_doctor_report(report: dict[str, Any]) -> str:
    freshness = report["freshness"]
    counts = report["counts"]
    lines = [
        f"Doctor status: {'healthy' if freshness['is_fresh'] else 'needs attention'}",
        "",
        f"Modules indexed: {counts['modules']}",
        f"Docs indexed: {counts['documentation']}",
        f"Routes indexed: {counts['routes']}",
        f"Parse errors: {counts['parse_errors']}",
    ]

    if freshness["missing"]:
        lines.append(f"Missing artifacts: {', '.join(freshness['missing'])}")
    if freshness["stale"]:
        lines.append(f"Stale artifacts: {', '.join(freshness['stale'])}")

    if report["parse_errors"]:
        lines.extend(
            [
                "",
                "Parse errors:",
                *[f"  - {item['path']}: {item['parse_error']}" for item in report['parse_errors']],
            ]
        )

    lines.extend(["", "Advice:", *[f"  - {item}" for item in report["advice"]]])
    return "\n".join(lines)



def print_results(results: list[dict[str, Any]], *, as_json: bool, header: str | None = None) -> None:
    if as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    if header:
        print(f"{header}\n")
    print("\n\n".join(format_item(item) for item in results))



def add_freshness_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--refresh-if-stale",
        action="store_true",
        help="Regenerate the generated project-index artifacts before reading them if they are missing or stale.",
    )
    parser.add_argument(
        "--require-fresh",
        action="store_true",
        help="Fail instead of reading stale generated artifacts.",
    )



def query_options_from_args(args: argparse.Namespace) -> QueryOptions:
    return QueryOptions(
        refresh_if_stale=bool(getattr(args, "refresh_if_stale", False)),
        require_fresh=bool(getattr(args, "require_fresh", False)),
    )



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified SCiv project-index helper for generation, browsing, querying, and validation.",
        epilog=(
            "Examples:\n"
            "  python3 scripts/index.py generate\n"
            "  python3 scripts/index.py check\n"
            "  python3 scripts/index.py search \"ui runtime\"\n"
            "  python3 scripts/index.py route docs-and-routing\n"
            "  python3 scripts/index.py list modules --query world --limit 10\n"
            "  python3 scripts/index.py stats --json\n"
            "  python3 scripts/index.py doctor"
        ),
        formatter_class=HelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate or refresh the project-index artifacts.",
        description="Generate SCiv's project-index JSON, doc-routing JSON, and structure markdown artifacts.",
        formatter_class=HelpFormatter,
    )
    generate_parser.add_argument(
        "--check",
        action="store_true",
        help="Fail instead of writing when the generated artifacts are stale.",
    )

    subparsers.add_parser(
        "check",
        help="Check whether the generated project-index artifacts are current.",
        description="Alias for `generate --check` with CI-friendly output and exit codes.",
        formatter_class=HelpFormatter,
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Search docs, routes, areas, entry points, and modules.",
        formatter_class=HelpFormatter,
    )
    search_parser.add_argument("query", help="Text to search for across indexed content.")
    search_parser.add_argument("--kind", choices=KIND_CHOICES, default="all", help="Restrict matches to a single item kind.")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum number of matches to print.")
    search_parser.add_argument("--json", action="store_true", help="Print results as JSON.")
    add_freshness_arguments(search_parser)

    show_parser = subparsers.add_parser(
        "show",
        help="Show one or more matching indexed items by path, route id, or module name.",
        formatter_class=HelpFormatter,
    )
    show_parser.add_argument("target", help="Exact or partial path/id/module name to inspect.")
    show_parser.add_argument("--kind", choices=KIND_CHOICES, default="all", help="Restrict lookup to a single item kind.")
    show_parser.add_argument("--json", action="store_true", help="Print results as JSON.")
    add_freshness_arguments(show_parser)

    for kind_name in ("route", "area"):
        kind_parser = subparsers.add_parser(
            kind_name,
            help=f"Search or inspect {kind_name} items quickly.",
            formatter_class=HelpFormatter,
        )
        kind_parser.add_argument("query", help=f"Exact id/path or fuzzy text to resolve against {kind_name} items.")
        kind_parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Maximum number of search matches to print when no direct match is found.",
        )
        kind_parser.add_argument("--json", action="store_true", help="Print results as JSON.")
        add_freshness_arguments(kind_parser)

    list_parser = subparsers.add_parser(
        "list",
        help="Browse one slice of the generated inventory.",
        description="List docs, routes, areas, modules, entry points, artifacts, or top-level items.",
        formatter_class=HelpFormatter,
    )
    list_parser.add_argument("target", choices=sorted(LIST_TARGET_KIND), help="Which indexed slice to browse.")
    list_parser.add_argument("--query", help="Optional fuzzy filter for the chosen slice.")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum number of items to print.")
    list_parser.add_argument("--json", action="store_true", help="Print results as JSON.")
    add_freshness_arguments(list_parser)

    stats_parser = subparsers.add_parser(
        "stats",
        help="Show inventory counts and freshness summary.",
        formatter_class=HelpFormatter,
    )
    stats_parser.add_argument("--json", action="store_true", help="Print stats as JSON.")
    add_freshness_arguments(stats_parser)

    doctor_parser = subparsers.add_parser(
        "doctor",
        aliases=["validate"],
        help="Diagnose stale artifacts and index-health issues.",
        formatter_class=HelpFormatter,
    )
    doctor_parser.add_argument("--json", action="store_true", help="Print the health report as JSON.")
    doctor_parser.add_argument(
        "--refresh-if-stale",
        action="store_true",
        help="Refresh stale or missing generated artifacts before reporting health.",
    )

    return parser



def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "generate":
        return run_generate(check=args.check)

    if args.command == "check":
        return run_generate(check=True)

    if args.command in {"search", "show", "route", "area", "list", "stats"}:
        runtime = resolve_runtime_index(query_options_from_args(args))
        index = runtime.index

        if args.command == "search":
            limit = max(1, args.limit)
            results = search_index(index, args.query, args.kind, limit)
            if not results:
                print(f"No matches found for {args.query!r}.", file=sys.stderr)
                return 1
            print_results(results, as_json=args.json, header=f"Top {len(results)} matches for {args.query!r}:")
            return 0

        if args.command == "show":
            matches = find_items(index, args.target, args.kind)
            if not matches:
                print(f"No items found for {args.target!r}.", file=sys.stderr)
                return 1
            print_results(matches, as_json=args.json, header=f"Found {len(matches)} match(es) for {args.target!r}:")
            return 0

        if args.command in {"route", "area"}:
            limit = max(1, args.limit)
            mode, results = resolve_kind_query(index, args.query, args.command, limit)
            if not results:
                print(f"No {args.command} items found for {args.query!r}.", file=sys.stderr)
                return 1
            header = (
                f"Found {len(results)} {args.command} match(es) for {args.query!r}:"
                if mode == "show"
                else f"Top {len(results)} {args.command} matches for {args.query!r}:"
            )
            print_results(results, as_json=args.json, header=header)
            return 0

        if args.command == "list":
            limit = max(1, args.limit)
            results = list_items(index, args.target, args.query, limit)
            if not results:
                query_text = f" for query {args.query!r}" if args.query else ""
                print(f"No {args.target} items found{query_text}.", file=sys.stderr)
                return 1
            header = (
                f"Top {len(results)} {args.target} matches for {args.query!r}:"
                if args.query
                else f"Showing {len(results)} {args.target} item(s):"
            )
            print_results(results, as_json=args.json, header=header)
            return 0

        stats = build_stats(index, runtime.freshness)
        if args.json:
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print(format_stats(stats))
        return 0

    outputs = build_generation_outputs()
    report = freshness_report(outputs)
    if args.refresh_if_stale and not report.is_fresh:
        write_outputs(outputs)
        report = FreshnessReport(missing_paths=[], stale_paths=[])

    doctor_report = build_doctor_report(outputs, report)
    if args.json:
        print(json.dumps(doctor_report, indent=2, ensure_ascii=False))
    else:
        print(format_doctor_report(doctor_report))
    return 0 if report.is_fresh else 1


if __name__ == "__main__":
    raise SystemExit(main())
