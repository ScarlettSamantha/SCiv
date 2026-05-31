#!/usr/bin/env python3
"""Generate raw SCiv worldgen debug exports without launching the full game runtime."""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from worldgen_generation_support import (
    generate_random_seed,
    generate_world_payload,
    get_config_manager,
    list_offline_generators,
    resolve_offline_generator,
    write_world_payload,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        default="Dynamic Worlds",
        help="Generator name. Supported values: CivLike, Dynamic Worlds.",
    )
    parser.add_argument("--width", type=int, default=50, help="Requested runtime map width.")
    parser.add_argument("--height", type=int, default=50, help="Requested runtime map height.")
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of worlds to export. Defaults to the saved offline batch count setting.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Base seed to use. When count > 1, later worlds increment this seed by one.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional export directory. Relative paths resolve from the repository root.",
    )
    parser.add_argument(
        "--option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Generator setup option override. Repeat for multiple options.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose raw hexgen debug output while generating the worlds.",
    )
    parser.add_argument(
        "--list-generators",
        action="store_true",
        help="List the supported offline export generators and exit.",
    )
    return parser.parse_args()


def parse_option_pairs(raw_options: list[str]) -> dict[str, str]:
    options: dict[str, str] = {}
    for entry in raw_options:
        if "=" not in entry:
            raise ValueError(f"Invalid --option value '{entry}'. Expected KEY=VALUE.")
        key, value = entry.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid --option value '{entry}'. The key cannot be empty.")
        options[key] = value
    return options


def resolve_batch_count(config: Any, requested_count: int | None) -> int:
    if requested_count is not None:
        return max(1, requested_count)
    return config.get_world_generation_export_batch_count()


def main() -> int:
    args = parse_args()
    config = get_config_manager()

    if args.list_generators:
        for spec in list_offline_generators():
            print(f"{spec.name}: {spec.description}")
        return 0

    generator_spec = resolve_offline_generator(str(args.generator))
    raw_options = parse_option_pairs(list(args.option))
    sanitized_options = generator_spec.sanitize_options(raw_options)

    count = resolve_batch_count(config, args.count)
    output_dir = args.output_dir or config.get_world_generation_export_dir()
    batch_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    generator_slug = generator_spec.name.lower().replace(" ", "_")

    manifest_entries: list[dict[str, Any]] = []
    batch_dir = output_dir
    if count > 1:
        batch_dir = str(Path(output_dir) / f"offline_{generator_slug}_{batch_timestamp}")

    for index in range(count):
        seed = args.seed + index if args.seed is not None else generate_random_seed()
        payload = generate_world_payload(
            generator_spec,
            width=max(1, args.width),
            height=max(1, args.height),
            seed=seed,
            options=sanitized_options,
            debug=args.debug,
            source="offline",
            extra_meta={
                "offline_helper": {
                    "count": count,
                    "batch_index": index + 1,
                    "batch_timestamp": batch_timestamp,
                }
            },
        )

        file_path = write_world_payload(
            payload,
            export_dir=batch_dir,
            file_stem=f"world_{index + 1:03d}_seed_{seed}",
        )

        summary = payload.get("summary", {})
        manifest_entries.append(
            {
                "file": str(file_path),
                "seed": seed,
                "generator": generator_spec.name,
                "setup_options": sanitized_options,
                "summary": summary,
            }
        )

        print(
            f"[{index + 1}/{count}] Wrote {file_path} "
            f"(land={summary.get('hexes', {}).get('land')}, water={summary.get('hexes', {}).get('water')})"
        )

    if count > 1:
        manifest_payload = {
            "generated_at": datetime.now().isoformat(),
            "generator": generator_spec.name,
            "requested_size": [max(1, args.width), max(1, args.height)],
            "count": count,
            "setup_options": sanitized_options,
            "worlds": manifest_entries,
        }
        manifest_path = write_world_payload(
            manifest_payload,
            export_dir=batch_dir,
            file_stem="batch_manifest",
        )
        print(f"Batch manifest: {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
