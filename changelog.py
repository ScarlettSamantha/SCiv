#!/usr/bin/env python3

import argparse
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parent
CHANGELOG_PATH: Final[Path] = REPO_ROOT / "CHANGELOG.md"
PYPROJECT_PATH: Final[Path] = REPO_ROOT / "pyproject.toml"
VERSION_PATH: Final[Path] = REPO_ROOT / "sciv" / "version.py"
DEFAULT_SECTION: Final[str] = "Unreleased"
DEFAULT_CATEGORY: Final[str] = "Changed"
DEFAULT_TAG_PREFIX: Final[str] = "v"

HELP_EPILOG: Final[str] = """Examples:
  python changelog.py unreleased
  python changelog.py add --category UI --message \"Polished minimap controls\"
  python changelog.py add --category Mechanics --ticket 142 --message \"Balanced ranged targeting\"
  python changelog.py categories
  python changelog.py gitmojis
  python changelog.py release --version 0.2.0
  python changelog.py tag --version 0.2.0 --dry-run
  python changelog.py version-show
  python changelog.py version-set --version 0.2.0.dev1 --version-name \"Proof of Concept\"
  python changelog.py status
"""

GITMOJI_BY_NAME: Final[dict[str, str]] = {
    "ai": "🤖",
    "ambulance": "🚑️",
    "apple": "🍎",
    "arrow_down": "⬇️",
    "arrow_up": "⬆️",
    "art": "🎨",
    "bookmark": "🔖",
    "boom": "💥",
    "bug": "🐛",
    "checkered_flag": "🏁",
    "children_crossing": "🚸",
    "construction_worker": "👷",
    "egg": "🥚",
    "engine": "⚙️",
    "fire": "🔥",
    "game_content": "📦️",
    "game_engine": "⚙️",
    "game_mechanics": "🎮",
    "gear": "⚙️",
    "green_apple": "🍏",
    "green_heart": "💚",
    "lipstick": "💄",
    "lock": "🔒️",
    "mag": "🔍️",
    "mechanics": "🎮",
    "memo": "📝",
    "package": "📦️",
    "penguin": "🐧",
    "rocket": "🚀",
    "robot": "🤖",
    "sparkles": "✨",
    "speech_balloon": "💬",
    "tooling": "👷",
    "ui": "💄",
    "video_game": "🎮",
    "wrench": "🔧",
    "zap": "⚡️",
}


@dataclass(frozen=True)
class CategoryPreset:
    name: str
    gitmoji: str
    description: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class VersionInfo:
    major: int
    minor: int
    patch: int
    stage: str
    revision: int
    version_name: str

    @property
    def version(self) -> str:
        return build_version_string(self.major, self.minor, self.patch, self.stage, self.revision)


CATEGORY_PRESETS: Final[tuple[CategoryPreset, ...]] = (
    CategoryPreset("Added", "sparkles", "New features or notable additions."),
    CategoryPreset("Changed", "wrench", "Behavior or workflow changes that are not pure fixes."),
    CategoryPreset("Fixed", "bug", "Bug fixes and regressions."),
    CategoryPreset("AI", "robot", "AI systems, behavior, or tooling changes.", ("bot", "ml")),
    CategoryPreset("UI", "lipstick", "HUD, menus, layout, visuals, and interaction polish.", ("ux", "interface")),
    CategoryPreset("Engine", "gear", "Runtime engine, rendering, performance, and platform integration.", ("game engine", "runtime")),
    CategoryPreset("Mechanics", "video_game", "Rules, balance, systems, and gameplay behavior.", ("gameplay", "balance", "rules")),
    CategoryPreset("Content", "package", "Game data, assets, authored content, and content packs.", ("game content", "assets", "data")),
    CategoryPreset("Docs", "memo", "Documentation and contributor guidance."),
    CategoryPreset("Tooling", "construction_worker", "Scripts, automation, validation, and repo tooling.", ("tools",)),
)
CANONICAL_CATEGORIES: Final[tuple[str, ...]] = tuple(preset.name for preset in CATEGORY_PRESETS)
CATEGORY_PRESET_BY_NAME: Final[dict[str, CategoryPreset]] = {preset.name: preset for preset in CATEGORY_PRESETS}
CATEGORY_LOOKUP: dict[str, str] = {}
for _preset in CATEGORY_PRESETS:
    CATEGORY_LOOKUP[_preset.name.strip().lower().replace("-", "_").replace(" ", "_")] = _preset.name
    for _alias in _preset.aliases:
        CATEGORY_LOOKUP[_alias.strip().lower().replace("-", "_").replace(" ", "_")] = _preset.name

VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:(?:\.(?P<dev_stage>dev)(?P<dev_revision>\d+))|(?:(?P<stage>a|b|rc)(?P<revision>\d+)))?$"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SCiv changelog and version helper.",
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="command")

    add_parser = subparsers.add_parser(
        "add",
        help="Add a changelog entry.",
        description="Insert a changelog entry into a section/category, applying category emoji defaults when possible.",
    )
    add_parser.add_argument("--section", default=DEFAULT_SECTION, help="Second-level section heading to use.")
    add_parser.add_argument("--category", default=DEFAULT_CATEGORY, help="Category heading to use, such as UI or Mechanics.")
    add_parser.add_argument("--message", required=True, help="Entry text to insert.")
    add_parser.add_argument(
        "--emoji",
        help="Prefix the entry with a literal emoji or a :gitmoji: shortcode such as :sparkles:.",
    )
    add_parser.add_argument(
        "--gitmoji",
        help="Prefix the entry with a named gitmoji such as sparkles, robot, gear, video_game, or memo.",
    )
    add_parser.add_argument(
        "--ticket",
        "--issue",
        dest="ticket",
        help="Append an issue or ticket reference as [#123] or [SCIV-123].",
    )
    add_common_file_argument(add_parser)
    add_parser.add_argument("--dry-run", action="store_true", help="Print the updated changelog without writing it.")

    ensure_parser = subparsers.add_parser(
        "ensure",
        help="Ensure canonical headings exist.",
        description="Create the canonical changelog structure and category headings if they are missing.",
    )
    add_common_file_argument(ensure_parser)
    ensure_parser.add_argument("--dry-run", action="store_true", help="Print the normalized changelog without writing it.")

    unreleased_parser = subparsers.add_parser(
        "unreleased",
        help="Show current unreleased changes.",
        description="Print the current Unreleased section, optionally hiding empty categories.",
    )
    add_common_file_argument(unreleased_parser)
    unreleased_parser.add_argument(
        "--all-categories",
        action="store_true",
        help="Show empty canonical categories too instead of only populated categories.",
    )

    show_parser = subparsers.add_parser(
        "show",
        help="Show a changelog section.",
        description="Print a requested changelog section such as Unreleased or a released version heading.",
    )
    show_parser.add_argument("--section", default=DEFAULT_SECTION, help="Section heading to print.")
    add_common_file_argument(show_parser)
    show_parser.add_argument(
        "--all-categories",
        action="store_true",
        help="Show empty canonical categories too when printing section contents.",
    )

    categories_parser = subparsers.add_parser(
        "categories",
        help="List supported changelog categories.",
        description="Show built-in changelog categories, their default emoji, and their intended use.",
    )
    categories_parser.add_argument(
        "--plain",
        action="store_true",
        help="Print a compact plain-text list instead of a formatted table.",
    )

    gitmoji_parser = subparsers.add_parser(
        "gitmojis",
        help="List known gitmoji aliases.",
        description="Show the built-in gitmoji aliases recognized by the changelog helper.",
    )
    gitmoji_parser.add_argument(
        "--plain",
        action="store_true",
        help="Print a compact plain-text list instead of a formatted table.",
    )

    release_parser = subparsers.add_parser(
        "release",
        help="Cut a release section.",
        description="Move populated Unreleased entries into a dated release section.",
    )
    release_parser.add_argument("--version", required=True, help="Release version such as 0.2.0 or 0.2.0rc1.")
    release_parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Release date in ISO format (YYYY-MM-DD). Defaults to today.",
    )
    add_common_file_argument(release_parser)
    release_parser.add_argument("--dry-run", action="store_true", help="Print the released changelog without writing it.")

    tag_parser = subparsers.add_parser(
        "tag",
        help="Preview or create an annotated git tag.",
        description="Preview or create an annotated git tag for an existing changelog release section.",
    )
    tag_parser.add_argument("--version", required=True, help="Release version such as 0.2.0 or 0.2.0rc1.")
    tag_parser.add_argument(
        "--tag-prefix",
        default=DEFAULT_TAG_PREFIX,
        help="Prefix for generated git tags when --tag-name is not provided.",
    )
    tag_parser.add_argument("--tag-name", help="Override the full git tag name instead of deriving it from the version.")
    tag_parser.add_argument(
        "--tag-message",
        help="Annotated git tag message. Defaults to 'Release <version>'.",
    )
    add_common_file_argument(tag_parser)
    tag_parser.add_argument("--dry-run", action="store_true", help="Print the resolved tag name and message.")

    version_show_parser = subparsers.add_parser(
        "version-show",
        help="Show version state.",
        description="Print the current version values from sciv/version.py and pyproject.toml and report whether they match.",
    )
    version_show_parser.add_argument(
        "--plain",
        action="store_true",
        help="Print a compact plain-text output instead of a table.",
    )

    version_set_parser = subparsers.add_parser(
        "version-set",
        help="Set version files.",
        description="Update sciv/version.py and pyproject.toml to a consistent version string.",
    )
    version_set_parser.add_argument("--version", required=True, help="PEP 440 version such as 0.2.0, 0.2.0rc1, or 0.2.0.dev1.")
    version_set_parser.add_argument(
        "--version-name",
        help="Optional display name/codename for sciv/version.py. Defaults to the current version name.",
    )
    version_set_parser.add_argument("--dry-run", action="store_true", help="Print the target version changes without writing them.")

    status_parser = subparsers.add_parser(
        "status",
        help="Show changelog and version status.",
        description="Print a compact summary of version consistency and current unreleased categories.",
    )
    add_common_file_argument(status_parser)

    return parser


def add_common_file_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--file", type=Path, default=CHANGELOG_PATH, help="Override the changelog file path.")


def normalize_name_token(value: str) -> str:
    return value.strip().strip(":").strip().lower().replace("-", "_").replace(" ", "_")


def normalize_message(message: str) -> str:
    normalized: str = " ".join(message.strip().split())
    if not normalized:
        raise ValueError("message must not be empty")
    return normalized


def normalize_category(category: str) -> str:
    normalized_category: str = normalize_message(category)
    lookup_key: str = normalize_name_token(normalized_category)
    if lookup_key in CATEGORY_LOOKUP:
        return CATEGORY_LOOKUP[lookup_key]

    if lookup_key == "ui":
        return "UI"
    if lookup_key == "ai":
        return "AI"

    words: list[str] = [word for word in normalized_category.replace("_", " ").split(" ") if word]
    if not words:
        raise ValueError("category must not be empty")
    return " ".join(word.upper() if word.upper() in {"AI", "UI"} else word.capitalize() for word in words)


def default_gitmoji_name_for_category(category: str) -> str | None:
    preset: CategoryPreset | None = CATEGORY_PRESET_BY_NAME.get(normalize_category(category))
    if preset is None:
        return None
    return preset.gitmoji


def resolve_gitmoji(*, emoji: str | None, gitmoji: str | None, category: str | None = None) -> str:
    if emoji and gitmoji:
        raise ValueError("use either --emoji or --gitmoji, not both")

    raw_value: str | None = gitmoji if gitmoji is not None else emoji
    if raw_value is None and category is not None:
        default_name: str | None = default_gitmoji_name_for_category(category)
        if default_name is not None:
            raw_value = default_name

    if raw_value is None:
        return ""

    stripped_value: str = raw_value.strip()
    if not stripped_value:
        raise ValueError("gitmoji/emoji value must not be empty")

    normalized_name: str = normalize_name_token(stripped_value)
    if normalized_name in GITMOJI_BY_NAME:
        return GITMOJI_BY_NAME[normalized_name]

    if gitmoji is not None:
        available_names: str = ", ".join(sorted(GITMOJI_BY_NAME))
        raise ValueError(f"unknown gitmoji '{gitmoji}'. Try one of: {available_names}")

    return stripped_value


def normalize_ticket(ticket: str | None) -> str:
    if ticket is None:
        return ""

    normalized: str = " ".join(ticket.strip().split())
    if not normalized:
        raise ValueError("ticket/issue reference must not be empty")

    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1].strip()

    if normalized.isdigit():
        normalized = f"#{normalized}"

    return f"[{normalized}]"


def heading(level: int, title: str) -> str:
    return f"{'#' * level} {title.strip()}"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str, *, dry_run: bool) -> None:
    if dry_run:
        print(content, end="")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_top_heading(lines: list[str]) -> list[str]:
    trimmed: list[str] = lines[:]
    while trimmed and trimmed[0].strip() == "":
        trimmed.pop(0)

    expected_heading: str = heading(1, "Changelog")
    if trimmed and trimmed[0].strip() == expected_heading:
        return trimmed

    if not trimmed:
        return [expected_heading, ""]

    return [expected_heading, "", *trimmed]


def find_heading_index(lines: list[str], level: int, title: str) -> int | None:
    expected: str = heading(level, title)
    for index, line in enumerate(lines):
        if line.strip() == expected:
            return index
    return None


def next_heading_index(lines: list[str], start_index: int, levels: tuple[int, ...]) -> int:
    prefixes: tuple[str, ...] = tuple("#" * level + " " for level in levels)
    search_index: int = start_index + 1
    while search_index < len(lines):
        stripped: str = lines[search_index].strip()
        if stripped.startswith(prefixes):
            return search_index
        search_index += 1
    return len(lines)


def ensure_blank_line_before_end(lines: list[str]) -> list[str]:
    result: list[str] = lines[:]
    while result and result[-1].strip() == "":
        result.pop()
    result.append("")
    return result


def ensure_section(lines: list[str], section: str) -> list[str]:
    existing_index: int | None = find_heading_index(lines, 2, section)
    if existing_index is not None:
        return lines

    result: list[str] = ensure_blank_line_before_end(lines)
    result.extend([heading(2, section), ""])
    return result


def ensure_category(lines: list[str], section: str, category: str) -> list[str]:
    normalized_category: str = normalize_category(category)
    section_index: int | None = find_heading_index(lines, 2, section)
    if section_index is None:
        raise ValueError(f"section '{section}' was expected to exist")

    section_end: int = next_heading_index(lines, section_index, (2,))
    for index in range(section_index + 1, section_end):
        if lines[index].strip() == heading(3, normalized_category):
            return lines

    result: list[str] = lines[:]
    insert_at: int = section_end
    while insert_at > section_index + 1 and result[insert_at - 1].strip() == "":
        insert_at -= 1
    result[insert_at:insert_at] = ["", heading(3, normalized_category), ""]
    return result


def ensure_canonical_structure(content: str, *, section: str = DEFAULT_SECTION) -> str:
    lines: list[str] = content.splitlines()
    lines = ensure_top_heading(lines)
    lines = ensure_section(lines, section)

    if section == DEFAULT_SECTION:
        for category in CANONICAL_CATEGORIES:
            lines = ensure_category(lines, section, category)
        lines = reorder_section(lines, section=section, include_empty_categories=True)

    return "\n".join(ensure_blank_line_before_end(lines)) + "\n"


def strip_leading_blank_lines(lines: list[str]) -> list[str]:
    result: list[str] = lines[:]
    while result and result[0].strip() == "":
        result.pop(0)
    return result


def strip_trailing_blank_lines(lines: list[str]) -> list[str]:
    result: list[str] = lines[:]
    while result and result[-1].strip() == "":
        result.pop()
    return result


def section_bounds(lines: list[str], level: int, title: str) -> tuple[int, int] | None:
    start_index: int | None = find_heading_index(lines, level, title)
    if start_index is None:
        return None
    end_index: int = next_heading_index(lines, start_index, (level,))
    return (start_index, end_index)


def collect_category_entries(lines: list[str], *, section: str) -> list[tuple[str, list[str]]]:
    bounds: tuple[int, int] | None = section_bounds(lines, 2, section)
    if bounds is None:
        raise ValueError(f"section '{section}' was expected to exist")

    section_start: int
    section_end: int
    section_start, section_end = bounds
    collected: list[tuple[str, list[str]]] = []
    current_name: str | None = None
    current_entries: list[str] = []

    for index in range(section_start + 1, section_end):
        stripped_line: str = lines[index].strip()
        if stripped_line.startswith("### "):
            if current_name is not None:
                collected.append((current_name, current_entries[:]))
            current_name = normalize_category(stripped_line[4:].strip())
            current_entries = []
            continue

        if current_name is None or stripped_line == "":
            continue

        current_entries.append(lines[index])

    if current_name is not None:
        collected.append((current_name, current_entries[:]))

    return collected


def render_section(section: str, categories: list[tuple[str, list[str]]], *, include_empty_categories: bool) -> list[str]:
    rendered: list[str] = [heading(2, section), ""]
    for category, entries in categories:
        if not include_empty_categories and not entries:
            continue
        rendered.append(heading(3, normalize_category(category)))
        rendered.append("")
        if entries:
            rendered.extend(entries)
            rendered.append("")
    return rendered


def reorder_section(lines: list[str], *, section: str, include_empty_categories: bool) -> list[str]:
    bounds: tuple[int, int] | None = section_bounds(lines, 2, section)
    if bounds is None:
        raise ValueError(f"section '{section}' was expected to exist")

    start_index: int
    end_index: int
    start_index, end_index = bounds
    existing_entries: list[tuple[str, list[str]]] = collect_category_entries(lines, section=section)
    entry_map: dict[str, list[str]] = {category: entries for category, entries in existing_entries}

    ordered_entries: list[tuple[str, list[str]]] = []
    if section == DEFAULT_SECTION:
        for category in CANONICAL_CATEGORIES:
            ordered_entries.append((category, entry_map.pop(category, [])))

    for category, _entries in existing_entries:
        if category in entry_map:
            ordered_entries.append((category, entry_map.pop(category)))

    prefix: list[str] = strip_trailing_blank_lines(lines[:start_index])
    suffix: list[str] = strip_leading_blank_lines(lines[end_index:])
    rebuilt_section: list[str] = render_section(section, ordered_entries, include_empty_categories=include_empty_categories)
    return [*prefix, "", *rebuilt_section, *suffix]


def release_heading(version: str, release_date: str) -> str:
    normalized_version: str = normalize_message(version)
    normalized_date: str = date.fromisoformat(release_date).isoformat()
    return f"{normalized_version} - {normalized_date}"


def release_section_exists(lines: list[str], version: str) -> bool:
    expected_prefix: str = f"## {normalize_message(version)}"
    for line in lines:
        stripped_line: str = line.strip()
        if stripped_line == expected_prefix or stripped_line.startswith(f"{expected_prefix} - "):
            return True
    return False


def insert_entry(content: str, *, section: str, category: str, message: str) -> str:
    normalized_section: str = normalize_message(section)
    normalized_category: str = normalize_category(category)
    normalized_content: str = ensure_canonical_structure(content, section=normalized_section)
    lines: list[str] = normalized_content.splitlines()
    lines = ensure_category(lines, normalized_section, normalized_category)

    section_index: int | None = find_heading_index(lines, 2, normalized_section)
    category_index: int | None = find_heading_index(lines, 3, normalized_category)
    if section_index is None or category_index is None:
        raise ValueError("failed to build requested changelog section/category")

    category_end: int = next_heading_index(lines, category_index, (2, 3))
    entry_line: str = f"- {normalize_message(message)}"

    for scan_index in range(category_index + 1, category_end):
        if lines[scan_index].strip() == entry_line:
            return "\n".join(ensure_blank_line_before_end(lines)) + "\n"

    insert_at: int = category_end
    while insert_at > category_index + 1 and lines[insert_at - 1].strip() == "":
        insert_at -= 1

    insertion: list[str] = ["", entry_line, ""] if insert_at == category_index + 1 else [entry_line]
    lines[insert_at:insert_at] = insertion
    return "\n".join(ensure_blank_line_before_end(lines)) + "\n"


def format_entry_message(message: str, *, emoji: str | None, gitmoji: str | None, ticket: str | None, category: str) -> str:
    parts: list[str] = []
    resolved_gitmoji: str = resolve_gitmoji(emoji=emoji, gitmoji=gitmoji, category=category)
    if resolved_gitmoji:
        parts.append(resolved_gitmoji)
    parts.append(normalize_message(message))

    ticket_suffix: str = normalize_ticket(ticket)
    if ticket_suffix:
        parts.append(ticket_suffix)

    return " ".join(parts)


def release_entries(content: str, *, version: str, release_date: str) -> str:
    normalized_content: str = ensure_canonical_structure(content, section=DEFAULT_SECTION)
    lines: list[str] = normalized_content.splitlines()

    if release_section_exists(lines, version):
        raise ValueError(f"release section for version '{version}' already exists")

    unreleased_entries: list[tuple[str, list[str]]] = collect_category_entries(lines, section=DEFAULT_SECTION)
    populated_entries: list[tuple[str, list[str]]] = [(category, entries) for category, entries in unreleased_entries if entries]
    if not populated_entries:
        raise ValueError("Unreleased has no entries to release")

    unreleased_bounds: tuple[int, int] | None = section_bounds(lines, 2, DEFAULT_SECTION)
    if unreleased_bounds is None:
        raise ValueError("Unreleased section was expected to exist")

    unreleased_start: int
    unreleased_end: int
    unreleased_start, unreleased_end = unreleased_bounds

    prefix: list[str] = strip_trailing_blank_lines(lines[:unreleased_start])
    suffix: list[str] = strip_leading_blank_lines(lines[unreleased_end:])
    empty_unreleased: list[tuple[str, list[str]]] = [(category, []) for category in CANONICAL_CATEGORIES]
    combined: list[str] = [
        *prefix,
        "",
        *render_section(DEFAULT_SECTION, empty_unreleased, include_empty_categories=True),
        *render_section(release_heading(version, release_date), populated_entries, include_empty_categories=False),
        *suffix,
    ]
    return "\n".join(ensure_blank_line_before_end(combined)) + "\n"


def extract_section_text(content: str, *, section: str, include_empty_categories: bool) -> str:
    lines: list[str] = content.splitlines()
    bounds: tuple[int, int] | None = section_bounds(lines, 2, normalize_message(section))
    if bounds is None:
        raise ValueError(f"section '{section}' does not exist")

    categories: list[tuple[str, list[str]]] = collect_category_entries(lines, section=normalize_message(section))
    rendered: list[str] = render_section(normalize_message(section), categories, include_empty_categories=include_empty_categories)
    return "\n".join(ensure_blank_line_before_end(rendered)) + "\n"


def ensure_release_exists(path: Path, *, version: str) -> None:
    lines: list[str] = read_text(path).splitlines()
    if not release_section_exists(lines, version):
        raise ValueError(f"release section for version '{version}' does not exist in {path}")


def resolve_tag_name(*, version: str, tag_prefix: str, tag_name: str | None) -> str:
    if tag_name is not None and tag_name.strip():
        return tag_name.strip()
    return f"{tag_prefix.strip()}{normalize_message(version)}"


def release_tag_message(version: str, explicit_message: str | None) -> str:
    if explicit_message is None or not explicit_message.strip():
        return f"Release {normalize_message(version)}"
    return normalize_message(explicit_message)


def git_tag_exists(tag_name: str) -> bool:
    completed_process = subprocess.run(
        ["git", "tag", "--list", tag_name],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed_process.stdout.strip() != ""


def create_git_tag(*, version: str, tag_prefix: str, tag_name: str | None, tag_message: str | None, dry_run: bool) -> None:
    resolved_tag_name: str = resolve_tag_name(version=version, tag_prefix=tag_prefix, tag_name=tag_name)
    resolved_tag_message: str = release_tag_message(version, tag_message)

    if dry_run:
        print(f"tag: {resolved_tag_name}")
        print(f"message: {resolved_tag_message}")
        return

    if git_tag_exists(resolved_tag_name):
        raise ValueError(f"git tag '{resolved_tag_name}' already exists")

    subprocess.run(["git", "tag", "-a", resolved_tag_name, "-m", resolved_tag_message], cwd=REPO_ROOT, check=True)
    print(f"created annotated git tag {resolved_tag_name}")


def parse_version_string(version: str, *, version_name: str) -> VersionInfo:
    normalized_version: str = normalize_message(version)
    match: re.Match[str] | None = VERSION_PATTERN.fullmatch(normalized_version)
    if match is None:
        raise ValueError("version must look like 0.2.0, 0.2.0rc1, or 0.2.0.dev1")

    stage: str = match.group("dev_stage") or match.group("stage") or ""
    revision_text: str | None = match.group("dev_revision") or match.group("revision")
    revision: int = int(revision_text) if revision_text is not None else 0
    return VersionInfo(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        stage=stage,
        revision=revision,
        version_name=version_name,
    )


def build_version_string(major: int, minor: int, patch: int, stage: str, revision: int) -> str:
    base: str = f"{major}.{minor}.{patch}"
    if not stage:
        return base
    if stage == "dev":
        return f"{base}.dev{revision}"
    return f"{base}{stage}{revision}"


def extract_string_assignment(content: str, name: str) -> str | None:
    pattern: re.Pattern[str] = re.compile(rf'^{re.escape(name)}\s*:?[^=]*=\s*"([^"]*)"', re.MULTILINE)
    match: re.Match[str] | None = pattern.search(content)
    return match.group(1) if match is not None else None


def extract_int_assignment(content: str, name: str) -> int | None:
    pattern: re.Pattern[str] = re.compile(rf"^{re.escape(name)}\s*:?[^=]*=\s*(\d+)", re.MULTILINE)
    match: re.Match[str] | None = pattern.search(content)
    return int(match.group(1)) if match is not None else None


def extract_bool_assignment(content: str, name: str) -> bool | None:
    pattern: re.Pattern[str] = re.compile(rf"^{re.escape(name)}\s*:?[^=]*=\s*(True|False)", re.MULTILINE)
    match: re.Match[str] | None = pattern.search(content)
    if match is None:
        return None
    return match.group(1) == "True"


def load_version_info(path: Path = VERSION_PATH) -> VersionInfo:
    content: str = read_text(path)
    major: int | None = extract_int_assignment(content, "__major__")
    minor: int | None = extract_int_assignment(content, "__minor__")
    patch: int | None = extract_int_assignment(content, "__patch__")
    revision: int = extract_int_assignment(content, "__revision__") or 0
    version_name: str = extract_string_assignment(content, "__version_name__") or "SCiv"
    stage: str | None = extract_string_assignment(content, "__stage__")

    if stage is None:
        isdev: bool | None = extract_bool_assignment(content, "__isdev__")
        stage = "dev" if isdev else ""

    if major is None or minor is None or patch is None:
        literal_version: str | None = extract_string_assignment(content, "__version__")
        if literal_version is None:
            raise ValueError(f"failed to parse version information from {path}")
        return parse_version_string(literal_version, version_name=version_name)

    return VersionInfo(
        major=major,
        minor=minor,
        patch=patch,
        stage=stage,
        revision=revision,
        version_name=version_name,
    )


def render_version_py(version_info: VersionInfo) -> str:
    stage_literal: str = version_info.stage
    isdev_literal: str = "True" if version_info.stage == "dev" else "False"
    return f'''from importlib.metadata import PackageNotFoundError, version

try:
    import pkg_resources
except ImportError:
    pkg_resources = None  # type: ignore

__major__: int = {version_info.major}
__minor__: int = {version_info.minor}
__patch__: int = {version_info.patch}
__stage__: str = "{stage_literal}"
__revision__: int = {version_info.revision}
__isdev__: bool = {isdev_literal}

if __stage__ == "dev":
    __pre_release__: str = ".dev"
    __build__: str = str(__revision__)
elif __stage__:
    __pre_release__ = __stage__
    __build__ = str(__revision__)
else:
    __pre_release__ = ""
    __build__ = ""

__version__: str = f"{{__major__}}.{{__minor__}}.{{__patch__}}{{__pre_release__}}{{__build__}}"
__version_name__: str = "{version_info.version_name}"


def get_package_version(package_name: str) -> str:
    try:
        return version(package_name)
    except PackageNotFoundError:
        if pkg_resources:
            try:
                return pkg_resources.get_distribution(package_name).version
            except pkg_resources.DistributionNotFound:
                return "unknown"
        return "unknown"


__panda3d_version__ = get_package_version("panda3d")
__kivy_version__ = get_package_version("kivy")
'''


def find_section_range(lines: list[str], section_header: str) -> tuple[int, int]:
    start_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == section_header:
            start_index = index
            break
    if start_index is None:
        raise ValueError(f"section {section_header} was not found")

    end_index: int = len(lines)
    for index in range(start_index + 1, len(lines)):
        if lines[index].startswith("[") and lines[index].endswith("]"):
            end_index = index
            break
    return (start_index, end_index)


def upsert_toml_setting(content: str, *, section_header: str, key: str, rendered_value: str) -> str:
    lines: list[str] = content.splitlines()
    start_index: int
    end_index: int
    start_index, end_index = find_section_range(lines, section_header)

    for index in range(start_index + 1, end_index):
        if lines[index].startswith(f"{key} ="):
            lines[index] = f"{key} = {rendered_value}"
            return "\n".join(lines) + "\n"

    insert_at: int = start_index + 1
    while insert_at < end_index and lines[insert_at].strip() == "":
        insert_at += 1
    lines.insert(insert_at, f"{key} = {rendered_value}")
    return "\n".join(lines) + "\n"


def load_pyproject_versions(path: Path = PYPROJECT_PATH) -> dict[str, str | None]:
    content: str = read_text(path)
    briefcase_version: str | None = extract_section_value(content, "[tool.briefcase]", "version")
    poetry_version: str | None = extract_section_value(content, "[tool.poetry]", "version")
    version_variables: str | None = extract_section_value(content, "[tool.semantic_release]", "version_variables")
    return {
        "tool.briefcase.version": briefcase_version,
        "tool.poetry.version": poetry_version,
        "tool.semantic_release.version_variables": version_variables,
    }


def extract_section_value(content: str, section_header: str, key: str) -> str | None:
    lines: list[str] = content.splitlines()
    try:
        start_index, end_index = find_section_range(lines, section_header)
    except ValueError:
        return None

    for index in range(start_index + 1, end_index):
        stripped: str = lines[index].strip()
        if stripped.startswith(f"{key} ="):
            return stripped.split("=", 1)[1].strip()
    return None


def update_pyproject_versions(content: str, *, version: str) -> str:
    updated: str = upsert_toml_setting(content, section_header="[tool.briefcase]", key="version", rendered_value=f'"{version}"')
    updated = upsert_toml_setting(updated, section_header="[tool.poetry]", key="version", rendered_value=f'"{version}"')
    updated = upsert_toml_setting(
        updated,
        section_header="[tool.semantic_release]",
        key="version_variables",
        rendered_value='["sciv/version.py:__version__"]',
    )
    return updated


def render_text_table(headers: list[str], rows: list[list[str]]) -> str:
    widths: list[int] = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def format_row(row: list[str]) -> str:
        return " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))

    separator: str = "-+-".join("-" * width for width in widths)
    output_lines: list[str] = [format_row(headers), separator]
    output_lines.extend(format_row(row) for row in rows)
    return "\n".join(output_lines)


def render_categories(*, plain: bool) -> str:
    rows: list[list[str]] = [
        [preset.name, GITMOJI_BY_NAME[preset.gitmoji], preset.gitmoji, preset.description]
        for preset in CATEGORY_PRESETS
    ]
    if plain:
        return "\n".join(f"{row[0]}: {row[1]} ({row[2]}) - {row[3]}" for row in rows) + "\n"
    return render_text_table(["Category", "Emoji", "Default gitmoji", "Purpose"], rows) + "\n"


def render_gitmojis(*, plain: bool) -> str:
    rows: list[list[str]] = [[name, emoji] for name, emoji in sorted(GITMOJI_BY_NAME.items())]
    if plain:
        return "\n".join(f"{name}: {emoji}" for name, emoji in rows) + "\n"
    return render_text_table(["Alias", "Emoji"], rows) + "\n"


def render_version_status(*, plain: bool) -> str:
    version_info: VersionInfo = load_version_info()
    pyproject_versions: dict[str, str | None] = load_pyproject_versions()
    briefcase_version: str = strip_quotes(pyproject_versions["tool.briefcase.version"])
    poetry_version: str = strip_quotes(pyproject_versions["tool.poetry.version"])
    version_variables: str = pyproject_versions["tool.semantic_release.version_variables"] or "<missing>"
    synchronized: bool = briefcase_version == version_info.version == poetry_version

    rows: list[list[str]] = [
        ["sciv/version.py", version_info.version],
        ["pyproject tool.briefcase", briefcase_version],
        ["pyproject tool.poetry", poetry_version],
        ["semantic_release version_variables", version_variables],
        ["in sync", "yes" if synchronized else "no"],
    ]
    if plain:
        return "\n".join(f"{label}: {value}" for label, value in rows) + "\n"
    return render_text_table(["Source", "Value"], rows) + "\n"


def strip_quotes(value: str | None) -> str:
    if value is None:
        return "<missing>"
    stripped: str = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] == '"':
        return stripped[1:-1]
    return stripped


def summarize_unreleased(content: str) -> str:
    normalized: str = ensure_canonical_structure(content, section=DEFAULT_SECTION)
    entries: list[tuple[str, list[str]]] = collect_category_entries(normalized.splitlines(), section=DEFAULT_SECTION)
    populated: list[list[str]] = []
    for category, category_entries in entries:
        if not category_entries:
            continue
        emoji: str = resolve_gitmoji(emoji=None, gitmoji=default_gitmoji_name_for_category(category), category=category)
        populated.append([category, emoji or "", str(len(category_entries))])

    if not populated:
        return "No unreleased changes.\n"
    return render_text_table(["Category", "Emoji", "Entries"], populated) + "\n"


def sync_version_files(version: str, *, version_name: str | None, dry_run: bool) -> None:
    current_info: VersionInfo = load_version_info()
    resolved_name: str = normalize_message(version_name) if version_name else current_info.version_name
    target_info: VersionInfo = parse_version_string(version, version_name=resolved_name)

    version_output: str = render_version_py(target_info)
    pyproject_output: str = update_pyproject_versions(read_text(PYPROJECT_PATH), version=target_info.version)

    if dry_run:
        print(f"sciv/version.py -> {target_info.version} ({resolved_name})")
        print(f"pyproject.toml [tool.briefcase].version -> {target_info.version}")
        print(f"pyproject.toml [tool.poetry].version -> {target_info.version}")
        print("pyproject.toml [tool.semantic_release].version_variables -> [\"sciv/version.py:__version__\"]")
        return

    VERSION_PATH.write_text(version_output, encoding="utf-8")
    PYPROJECT_PATH.write_text(pyproject_output, encoding="utf-8")
    print(f"updated version files to {target_info.version}")


def openciv_changelog(*_args: object, **_kwargs: object) -> str:
    return read_text(CHANGELOG_PATH)


def main() -> int:
    parser: argparse.ArgumentParser = build_parser()
    args: argparse.Namespace = parser.parse_args()

    if args.command == "categories":
        print(render_categories(plain=bool(args.plain)), end="")
        return 0

    if args.command == "gitmojis":
        print(render_gitmojis(plain=bool(args.plain)), end="")
        return 0

    if args.command == "version-show":
        print(render_version_status(plain=bool(args.plain)), end="")
        return 0

    if args.command == "version-set":
        sync_version_files(str(args.version), version_name=getattr(args, "version_name", None), dry_run=bool(args.dry_run))
        return 0

    if args.command == "status":
        file_path: Path = args.file.resolve()
        content: str = read_text(file_path)
        print("Versions")
        print(render_version_status(plain=False), end="")
        print()
        print("Unreleased")
        print(summarize_unreleased(content), end="")
        return 0

    file_path = args.file.resolve()
    current_content: str = read_text(file_path)

    if args.command == "ensure":
        updated_content: str = ensure_canonical_structure(current_content)
        write_text(file_path, updated_content, dry_run=bool(args.dry_run))
        return 0

    if args.command == "unreleased":
        print(extract_section_text(current_content, section=DEFAULT_SECTION, include_empty_categories=bool(args.all_categories)), end="")
        return 0

    if args.command == "show":
        print(
            extract_section_text(
                current_content,
                section=str(args.section),
                include_empty_categories=bool(args.all_categories),
            ),
            end="",
        )
        return 0

    if args.command == "add":
        normalized_category: str = normalize_category(str(args.category))
        updated_content = insert_entry(
            current_content,
            section=str(args.section).strip() or DEFAULT_SECTION,
            category=normalized_category,
            message=format_entry_message(
                str(args.message),
                emoji=getattr(args, "emoji", None),
                gitmoji=getattr(args, "gitmoji", None),
                ticket=getattr(args, "ticket", None),
                category=normalized_category,
            ),
        )
        write_text(file_path, updated_content, dry_run=bool(args.dry_run))
        return 0

    if args.command == "release":
        updated_content = release_entries(current_content, version=str(args.version), release_date=str(args.date))
        write_text(file_path, updated_content, dry_run=bool(args.dry_run))
        if not args.dry_run:
            print(f"released {normalize_message(str(args.version))} in {file_path}")
        return 0

    if args.command == "tag":
        ensure_release_exists(file_path, version=str(args.version))
        create_git_tag(
            version=str(args.version),
            tag_prefix=str(args.tag_prefix),
            tag_name=getattr(args, "tag_name", None),
            tag_message=getattr(args, "tag_message", None),
            dry_run=bool(args.dry_run),
        )
        return 0

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
