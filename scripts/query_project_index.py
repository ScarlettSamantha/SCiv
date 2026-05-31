#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Query SCiv's generated project index for targeted lookup of docs, routes, areas, entry points, and modules."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = REPO_ROOT / "meta" / "generated" / "project-index.json"

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


def load_index() -> dict[str, Any]:
	if not INDEX_PATH.exists():
		raise SystemExit(
			f"Missing generated index: {INDEX_PATH}. Run `python3 scripts/generate_project_index.py` first."
		)

	return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


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
		lines.append(f"  Read first: {preview(item.get('read_first', []))}")
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

	if "score" in item:
		lines.append(f"  Score: {item['score']}")

	return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Query SCiv's generated project index.")
	subparsers = parser.add_subparsers(dest="command", required=True)

	search_parser = subparsers.add_parser("search", help="Search the generated project index.")
	search_parser.add_argument("query", help="Text to search for across docs, routes, areas, entry points, and modules.")
	search_parser.add_argument("--kind", choices=KIND_CHOICES, default="all", help="Restrict matches to a single item kind.")
	search_parser.add_argument("--limit", type=int, default=10, help="Maximum number of matches to print.")
	search_parser.add_argument("--json", action="store_true", help="Print results as JSON.")

	show_parser = subparsers.add_parser("show", help="Show a matching item by path, route id, or module name.")
	show_parser.add_argument("target", help="Exact or partial path/id/module name to inspect.")
	show_parser.add_argument("--kind", choices=KIND_CHOICES, default="all", help="Restrict lookup to a single item kind.")
	show_parser.add_argument("--json", action="store_true", help="Print results as JSON.")

	for kind_name in ("route", "area"):
		kind_parser = subparsers.add_parser(kind_name, help=f"Search or inspect {kind_name} items quickly.")
		kind_parser.add_argument(
			"query",
			help=f"Exact id/path or fuzzy text to resolve against {kind_name} items.",
		)
		kind_parser.add_argument(
			"--limit",
			type=int,
			default=5,
			help="Maximum number of search matches to print when no direct match is found.",
		)
		kind_parser.add_argument("--json", action="store_true", help="Print results as JSON.")

	return parser


def main() -> int:
	parser = build_parser()
	args = parser.parse_args()

	index = load_index()

	if args.command == "search":
		limit = max(1, args.limit)
		results = search_index(index, args.query, args.kind, limit)

		if not results:
			print(f"No matches found for {args.query!r}.", file=sys.stderr)
			return 1

		if args.json:
			print(json.dumps(results, indent=2, ensure_ascii=False))
		else:
			print(f"Top {len(results)} matches for {args.query!r}:\n")
			print("\n\n".join(format_item(item) for item in results))
		return 0

	if args.command in {"route", "area"}:
		limit = max(1, args.limit)
		mode, results = resolve_kind_query(index, args.query, args.command, limit)

		if not results:
			print(f"No {args.command} items found for {args.query!r}.", file=sys.stderr)
			return 1

		if args.json:
			print(json.dumps(results, indent=2, ensure_ascii=False))
		else:
			if mode == "show":
				print(f"Found {len(results)} {args.command} match(es) for {args.query!r}:\n")
			else:
				print(f"Top {len(results)} {args.command} matches for {args.query!r}:\n")
			print("\n\n".join(format_item(item) for item in results))
		return 0

	matches = find_items(index, args.target, args.kind)

	if not matches:
		print(f"No items found for {args.target!r}.", file=sys.stderr)
		return 1

	if args.json:
		print(json.dumps(matches, indent=2, ensure_ascii=False))
	else:
		print(f"Found {len(matches)} match(es) for {args.target!r}:\n")
		print("\n\n".join(format_item(item) for item in matches))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
