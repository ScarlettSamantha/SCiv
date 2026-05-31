from collections.abc import Iterable, Mapping, Set
from typing import TYPE_CHECKING

import numpy as np

from system.generators.dynamic_worlds.models import HexCoord, NamedRiver
from system.generators.dynamic_worlds.names import build_seeded_rng, generate_river_name
from system.subsystems.hexgen.edge import Edge
from system.subsystems.hexgen.enums import HexSide
from system.subsystems.hexgen.river import RiverSegment

if TYPE_CHECKING:
    from system.subsystems.hexgen.mapgen import MapGen
    from system.subsystems.hexgen.hex import Hex
    from gameplay.tile import Tile


def apply_dynamic_river_profile(mapgen: "MapGen", *, map_script: str, biome_style: str) -> dict[str, int]:
    base_source_count = len(mapgen.rivers_sources)
    major_river_count = sum(1 for river_source in mapgen.rivers_sources if river_source.size >= 8)
    scaled_river_count = max(1, major_river_count or base_source_count)
    tributary_factor = float(mapgen.params.get("tributary_factor", 0.0))
    connector_factor = float(mapgen.params.get("river_connector_factor", 0.0))
    distributary_factor = float(mapgen.params.get("river_distributary_factor", 0.0))

    target_tributaries = 0
    if tributary_factor > 0 and base_source_count > 0:
        target_tributaries = min(12, max(1, int(round(scaled_river_count * tributary_factor))))

    target_connectors = 0
    if connector_factor > 0 and base_source_count > 1:
        target_connectors = min(6, max(1, int(round(scaled_river_count * connector_factor))))

    target_distributaries = 0
    if distributary_factor > 0 and base_source_count > 0:
        target_distributaries = min(8, max(1, int(round(scaled_river_count * distributary_factor))))

    tributaries_added = _grow_tributaries(mapgen, target=target_tributaries)
    connectors_added = _grow_river_connectors(mapgen, target=target_connectors)
    distributaries_added = _grow_distributaries(mapgen, target=target_distributaries)
    valley_segments = _carve_river_valleys(
        mapgen,
        depth=float(mapgen.params.get("river_valley_depth", 0.0)),
        radius=max(1, int(mapgen.params.get("river_valley_radius", 1))),
    )

    return {
        "tributaries_added": tributaries_added,
        "connectors_added": connectors_added,
        "distributaries_added": distributaries_added,
        "valley_segments": valley_segments,
        "map_script": 1 if map_script else 0,
        "biome_style": 1 if biome_style else 0,
    }


def build_named_rivers(
    river_sources: Iterable["RiverSegment"],
    *,
    seed: int | None,
    visible_coords: Set[HexCoord] | None = None,
) -> list[NamedRiver]:
    rng = build_seeded_rng(seed, "rivers")
    used_names: set[str] = set()
    named_rivers: list[NamedRiver] = []

    grouped_sources: dict[str, list[RiverSegment]] = {}
    for river_source in river_sources:
        grouped_sources.setdefault(_river_network_id(river_source), []).append(river_source)

    ordered_groups = sorted(
        grouped_sources.items(),
        key=lambda item: max(current.size for current in item[1]),
        reverse=True,
    )

    for network_id, source_group in ordered_groups:
        ordered_sources = sorted(source_group, key=lambda current: current.size, reverse=True)
        coords: list[HexCoord] = []
        seen_coords: set[HexCoord] = set()

        for river_source in ordered_sources:
            current = river_source

            while current is not None:
                coord = (current.x, current.y)
                if (visible_coords is None or coord in visible_coords) and coord not in seen_coords:
                    coords.append(coord)
                    seen_coords.add(coord)
                current = current.next

        if not coords:
            continue

        existing_name = next(
            (
                current_name
                for river_source in ordered_sources
                for current_name in [getattr(river_source, "display_name", None)]
                if isinstance(current_name, str) and current_name
            ),
            None,
        )
        if existing_name is not None:
            river_name = existing_name
            used_names.add(river_name)
        else:
            river_name = generate_river_name(rng, used_names)

        for river_source in ordered_sources:
            _apply_chain_metadata(river_source, display_name=river_name)

        mouth: HexCoord | None = None
        for river_source in ordered_sources:
            tail = river_source
            while tail.next is not None:
                tail = tail.next

            mouth = _resolve_mouth_coord(tail, visible_coords, coords)
            if mouth is not None:
                break

        named_rivers.append(
            NamedRiver(
                id=network_id,
                name=river_name,
                length=len(coords),
                source=coords[0],
                mouth=mouth,
                tiles=tuple(coords),
            )
        )

    return named_rivers


def apply_river_names(tiles: Mapping[HexCoord, "Tile"], rivers: Iterable[NamedRiver]) -> None:
    assignments: dict[HexCoord, list[NamedRiver]] = {}

    for river in rivers:
        for coord in river.tiles:
            assignments.setdefault(coord, []).append(river)

    for coord, named_rivers in assignments.items():
        tile = tiles.get(coord)
        if tile is None:
            continue

        ordered_rivers = sorted(named_rivers, key=lambda current: current.length, reverse=True)
        river_names = [river.name for river in ordered_rivers]

        setattr(tile, "river_names", river_names)
        setattr(tile, "river_system_ids", [river.id for river in ordered_rivers])
        setattr(tile, "primary_river_name", river_names[0])
        setattr(tile, "river_count", len(river_names))


def _river_network_id(river_source: "RiverSegment") -> str:
    network_id = getattr(river_source, "network_id", None)
    if isinstance(network_id, str) and network_id:
        return network_id
    return river_source.id.hex


def _set_segment_metadata(
    segment: "RiverSegment",
    *,
    network_id: str | None = None,
    branch_kind: str | None = None,
    display_name: str | None = None,
) -> None:
    if network_id is not None:
        setattr(segment, "network_id", network_id)
    if branch_kind is not None:
        setattr(segment, "branch_kind", branch_kind)
    if display_name is not None:
        setattr(segment, "display_name", display_name)


def _apply_chain_metadata(
    river_source: "RiverSegment",
    *,
    network_id: str | None = None,
    branch_kind: str | None = None,
    display_name: str | None = None,
) -> None:
    current = river_source
    while current is not None:
        _set_segment_metadata(
            current,
            network_id=network_id,
            branch_kind=branch_kind,
            display_name=display_name,
        )
        current = current.next


def _chain_segments(river_source: "RiverSegment") -> list["RiverSegment"]:
    segments: list[RiverSegment] = []
    current = river_source
    while current is not None:
        segments.append(current)
        current = current.next
    return segments


def _chain_hexes(mapgen: "MapGen", river_source: "RiverSegment") -> list["Hex"]:
    chain_hexes: list[Hex] = []
    for segment in _chain_segments(river_source):
        hex_tile = mapgen.hex_grid.get(segment.x, segment.y)
        if hex_tile is not None:
            chain_hexes.append(hex_tile)
    return chain_hexes


def _river_hex_network_index(mapgen: "MapGen") -> dict[HexCoord, set[str]]:
    index: dict[HexCoord, set[str]] = {}

    for river_source in mapgen.rivers_sources:
        network_id = _river_network_id(river_source)
        current = river_source
        while current is not None:
            index.setdefault((current.x, current.y), set()).add(network_id)
            current = current.next

    return index


def _count_new_path_edges(path: list["Hex"]) -> int:
    new_edges = 0
    for current_hex, next_hex in zip(path, path[1:]):
        side = current_hex.get_side_to(next_hex)
        if side is None:
            return 0
        edge = current_hex.get_edge(side)
        if edge is None:
            return 0
        if not edge.is_river:
            new_edges += 1
    return new_edges


def _sample_indices(indices: list[int], *, max_points: int) -> list[int]:
    if len(indices) <= max_points:
        return indices

    if max_points <= 1:
        return [indices[len(indices) // 2]]

    step = (len(indices) - 1) / float(max_points - 1)
    selected: list[int] = []
    for offset in range(max_points):
        selected_index = indices[round(offset * step)]
        if selected_index not in selected:
            selected.append(selected_index)
    return selected


def _straight_line_hex_path(mapgen: "MapGen", *, start_hex: "Hex", goal_hex: "Hex") -> list["Hex"] | None:
    path: list[Hex] = []
    for coord in mapgen.straight_line_path((start_hex.x, start_hex.y), (goal_hex.x, goal_hex.y)):
        hex_tile = mapgen.hex_grid.get(*coord)
        if hex_tile is None:
            return None
        path.append(hex_tile)
    return path


def _path_is_viable(
    mapgen: "MapGen",
    *,
    path: list["Hex"],
    blocked_coords: set[HexCoord],
    allow_goal_water: bool = False,
) -> bool:
    if len(path) < 3:
        return False

    sealevel = float(mapgen.hex_grid.sealevel)
    goal_coord = (path[-1].x, path[-1].y)

    for hex_tile in path[1:]:
        coord = (hex_tile.x, hex_tile.y)
        if coord != goal_coord and coord in blocked_coords:
            return False

        if coord == goal_coord:
            if not hex_tile.is_land and not allow_goal_water:
                return False
            continue

        if not hex_tile.is_land:
            return False

        if float(hex_tile.altitude) > sealevel + 110.0:
            return False

    return _count_new_path_edges(path) >= 2


def _candidate_branch_path(
    mapgen: "MapGen",
    *,
    start_hex: "Hex",
    goal_hex: "Hex",
    blocked_coords: set[HexCoord],
    max_steps: int,
    allow_goal_water: bool = False,
) -> list["Hex"] | None:
    straight_path = _straight_line_hex_path(mapgen, start_hex=start_hex, goal_hex=goal_hex)
    if straight_path is not None and _path_is_viable(
        mapgen,
        path=straight_path,
        blocked_coords=blocked_coords,
        allow_goal_water=allow_goal_water,
    ):
        return straight_path

    return None


def _commit_branch_path(
    mapgen: "MapGen",
    *,
    source_hex: "Hex",
    path: list["Hex"],
    network_id: str | None,
    branch_kind: str,
) -> int:
    if len(path) < 3:
        return 0

    pair_specs: list[tuple["Hex", "Hex", HexSide, Edge, bool]] = []
    for current_hex, next_hex in zip(path, path[1:]):
        side = current_hex.get_side_to(next_hex)
        if side is None:
            return 0

        edge = current_hex.get_edge(side)
        if edge is None:
            return 0

        pair_specs.append((current_hex, next_hex, side, edge, bool(edge.is_river)))

    if any(preexisting for *_rest, preexisting in pair_specs[:-1]):
        return 0

    new_edges = sum(0 if preexisting else 1 for *_rest, preexisting in pair_specs)
    if new_edges < 2:
        return 0

    first_side = pair_specs[0][2]
    head = RiverSegment(mapgen.hex_grid, source_hex.x, source_hex.y, first_side, False)
    _set_segment_metadata(head, network_id=network_id, branch_kind=branch_kind)

    segments = [head]
    current_segment = head

    for index, (_current_hex, next_hex, side, edge, preexisting) in enumerate(pair_specs):
        current_segment.side = side
        edge.is_river = True

        if preexisting:
            break

        next_segment = RiverSegment(mapgen.hex_grid, next_hex.x, next_hex.y, side, False)
        _set_segment_metadata(next_segment, network_id=network_id, branch_kind=branch_kind)
        current_segment.next = next_segment
        segments.append(next_segment)

        if index == len(pair_specs) - 1:
            break

        current_segment = next_segment

    mapgen.rivers_sources.append(head)
    mapgen.rivers.extend(segments)
    return new_edges


def _resolve_mouth_coord(
    tail: "RiverSegment",
    visible_coords: Set[HexCoord] | None,
    coords: list[HexCoord],
) -> HexCoord | None:
    try:
        down_hex = tail.edge.down
    except Exception:
        return coords[-1] if coords else None

    mouth_coord = (down_hex.x, down_hex.y)
    if visible_coords is not None and mouth_coord not in visible_coords:
        return coords[-1] if coords else None
    return mouth_coord


def _grow_river_connectors(mapgen: "MapGen", *, target: int) -> int:
    if target <= 0 or len(mapgen.rivers_sources) < 2:
        return 0

    connector_radius = max(5, int(mapgen.params.get("river_connector_radius", 9)))
    sealevel = float(mapgen.hex_grid.sealevel)
    base_sources = [source for source in list(mapgen.rivers_sources) if source.size >= 7]
    network_sizes: dict[str, int] = {}
    for river_source in base_sources:
        network_id = _river_network_id(river_source)
        network_sizes[network_id] = max(network_sizes.get(network_id, 0), river_source.size)

    if len(network_sizes) < 2:
        return 0

    added = 0
    used_splits: set[HexCoord] = set()
    river_coords = {(segment.x, segment.y) for segment in mapgen.rivers}
    river_networks = _river_hex_network_index(mapgen)
    remaining_attempts = max(12, target * 8)

    for river_source in sorted(base_sources, key=lambda current: current.size, reverse=True):
        network_id = _river_network_id(river_source)
        chain_hexes = _chain_hexes(mapgen, river_source)
        if len(chain_hexes) < 7:
            continue

        candidate_indices = _sample_indices(
            list(range(max(2, len(chain_hexes) // 4), max(2, len(chain_hexes) - 2))),
            max_points=4,
        )
        for split_index in candidate_indices:
            split_hex = chain_hexes[split_index]
            split_coord = (split_hex.x, split_hex.y)
            if split_coord in used_splits:
                continue
            if not split_hex.is_land or float(split_hex.altitude) > sealevel + 95.0:
                continue

            best_score = float("-inf")
            best_path: list[Hex] | None = None

            ranked_targets: list[tuple[float, Hex]] = []
            for target_coord, target_networks in river_networks.items():
                if target_coord == split_coord:
                    continue
                if network_id in target_networks:
                    continue

                candidate_hex = mapgen.hex_grid.get(*target_coord)
                if candidate_hex is None or not candidate_hex.is_land:
                    continue

                direct_distance = mapgen.hex_distance(split_coord, target_coord)
                if direct_distance < 4 or direct_distance > connector_radius:
                    continue

                target_size = max(network_sizes.get(target_network, 1) for target_network in target_networks)
                cheap_score = (
                    float(target_size) * 0.45
                    + float(direct_distance) * 0.25
                    - float(candidate_hex.altitude) * 0.01
                    + float(getattr(candidate_hex, "distance", 0.0)) * 0.2
                )
                ranked_targets.append((cheap_score + mapgen.rng.random() * 0.1, candidate_hex))

            for _cheap_score, candidate_hex in sorted(ranked_targets, key=lambda item: item[0], reverse=True)[:6]:
                if remaining_attempts <= 0:
                    break
                remaining_attempts -= 1

                target_coord = (candidate_hex.x, candidate_hex.y)
                target_networks = river_networks.get(target_coord)
                if not target_networks:
                    continue

                direct_distance = mapgen.hex_distance(split_coord, target_coord)

                blocked_coords = set(river_coords)
                blocked_coords.discard(split_coord)
                blocked_coords.discard(target_coord)
                path = _candidate_branch_path(
                    mapgen,
                    start_hex=split_hex,
                    goal_hex=candidate_hex,
                    blocked_coords=blocked_coords,
                    max_steps=max(connector_radius + 2, direct_distance + 2),
                )
                if path is None:
                    continue

                target_size = max(network_sizes.get(target_network, 1) for target_network in target_networks)
                score = (
                    float(target_size) * 0.45
                    + float(direct_distance) * 0.25
                    - float(len(path)) * 0.35
                    - float(candidate_hex.altitude) * 0.01
                    + float(getattr(candidate_hex, "distance", 0.0)) * 0.2
                    + mapgen.rng.random() * 0.1
                )
                if score > best_score:
                    best_score = score
                    best_path = path

            if remaining_attempts <= 0:
                break

            if best_path is None:
                continue

            created = _commit_branch_path(
                mapgen,
                source_hex=split_hex,
                path=best_path,
                network_id=network_id,
                branch_kind="connector",
            )
            if created <= 0:
                continue

            added += 1
            used_splits.add(split_coord)
            river_coords = {(segment.x, segment.y) for segment in mapgen.rivers}
            river_networks = _river_hex_network_index(mapgen)
            break

        if added >= target or remaining_attempts <= 0:
            break

    return added


def _grow_distributaries(mapgen: "MapGen", *, target: int) -> int:
    if target <= 0 or not mapgen.rivers_sources:
        return 0

    distributary_radius = max(4, int(mapgen.params.get("river_distributary_radius", 6)))
    sealevel = float(mapgen.hex_grid.sealevel)
    base_sources = [source for source in list(mapgen.rivers_sources) if source.size >= 8]

    added = 0
    used_splits: set[HexCoord] = set()
    river_coords = {(segment.x, segment.y) for segment in mapgen.rivers}
    remaining_attempts = max(12, target * 8)

    for river_source in sorted(base_sources, key=lambda current: current.size, reverse=True):
        network_id = _river_network_id(river_source)
        chain_hexes = _chain_hexes(mapgen, river_source)
        if len(chain_hexes) < 8:
            continue

        candidate_indices = _sample_indices(
            list(range(max(2, len(chain_hexes) // 3), max(2, len(chain_hexes) - 3))),
            max_points=4,
        )
        for split_index in candidate_indices:
            split_hex = chain_hexes[split_index]
            split_coord = (split_hex.x, split_hex.y)
            if split_coord in used_splits:
                continue
            if not split_hex.is_land:
                continue
            if float(split_hex.altitude) > sealevel + 80.0:
                continue

            best_score = float("-inf")
            best_path: list[Hex] | None = None

            max_target_index = min(len(chain_hexes) - 1, split_index + distributary_radius + 4)
            target_indices = _sample_indices(list(range(split_index + 3, max_target_index + 1)), max_points=4)
            for target_index in target_indices:
                if remaining_attempts <= 0:
                    break
                remaining_attempts -= 1

                target_hex = chain_hexes[target_index]
                target_coord = (target_hex.x, target_hex.y)
                direct_distance = mapgen.hex_distance(split_coord, target_coord)
                if direct_distance < 3 or direct_distance > distributary_radius:
                    continue

                blocked_coords = set(river_coords)
                blocked_coords.discard(split_coord)
                blocked_coords.discard(target_coord)
                path = _candidate_branch_path(
                    mapgen,
                    start_hex=split_hex,
                    goal_hex=target_hex,
                    blocked_coords=blocked_coords,
                    max_steps=max(distributary_radius + 2, direct_distance + 2),
                )
                if path is None:
                    continue

                score = (
                    float(target_index - split_index) * 0.4
                    + float(direct_distance) * 0.15
                    - float(len(path)) * 0.4
                    - float(target_hex.altitude) * 0.01
                    + mapgen.rng.random() * 0.1
                )
                if score > best_score:
                    best_score = score
                    best_path = path

            if remaining_attempts <= 0:
                break

            if best_path is None:
                continue

            created = _commit_branch_path(
                mapgen,
                source_hex=split_hex,
                path=best_path,
                network_id=network_id,
                branch_kind="distributary",
            )
            if created <= 0:
                continue

            added += 1
            used_splits.add(split_coord)
            river_coords = {(segment.x, segment.y) for segment in mapgen.rivers}
            break

        if added >= target or remaining_attempts <= 0:
            break

    return added


def _grow_tributaries(mapgen: "MapGen", *, target: int) -> int:
    if target <= 0 or not mapgen.rivers_sources:
        return 0

    filled_alt = mapgen._priority_flood_filled_alt()  # pyright: ignore[reportPrivateUsage]
    flow_dir: dict["Hex", "Hex"] = mapgen._compute_flow_dir(filled_alt)  # pyright: ignore[reportPrivateUsage]
    acc: dict["Hex", float] = mapgen._flow_accumulation(flow_dir)  # pyright: ignore[reportPrivateUsage]

    river_coords = {(segment.x, segment.y) for segment in mapgen.rivers}
    source_coords = {(source.x, source.y) for source in mapgen.rivers_sources}
    candidate_scores: dict[HexCoord, float] = {}

    for river_source in sorted(mapgen.rivers_sources, key=lambda current: current.size, reverse=True):
        if river_source.size < 4:
            continue

        current = river_source
        while current is not None:
            current_hex = mapgen.hex_grid.get(current.x, current.y)
            if current_hex is None:
                break

            for candidate in current_hex.bubble(distance=2):
                coord = (candidate.x, candidate.y)
                local_distance = mapgen.hex_distance((current_hex.x, current_hex.y), coord)
                if local_distance < 2:
                    continue
                if coord in river_coords or coord in source_coords or not candidate.is_land:
                    continue
                if float(candidate.altitude) <= float(mapgen.hex_grid.sealevel) + 4.0:
                    continue
                if float(getattr(candidate, "distance", 0.0)) <= 1.0:
                    continue
                if any(edge is not None and getattr(edge, "is_river", False) for edge in candidate.edges):
                    continue

                score = (
                    float(acc.get(candidate, 1.0))
                    + float(candidate.altitude) * 0.02
                    + float(candidate.distance) * 0.4
                    + local_distance * 0.35
                )
                candidate_scores[coord] = max(score, candidate_scores.get(coord, float("-inf")))

            current = current.next

    spacing = max(2, int(mapgen.params.get("river_source_spacing", 6)) - 1)
    ordered_candidates = [
        mapgen.hex_grid.get(*coord)
        for coord, _ in sorted(candidate_scores.items(), key=lambda item: item[1], reverse=True)
    ]

    added = 0
    used_source_coords = set(source_coords)
    for candidate in ordered_candidates:
        if candidate is None:
            continue

        coord = (candidate.x, candidate.y)
        if any(mapgen.hex_distance(coord, other) < spacing for other in used_source_coords):
            continue

        created = _trace_tributary(mapgen, source_hex=candidate, flow_dir=flow_dir)
        if created >= 2:
            added += 1
            used_source_coords.add(coord)
            if added >= target:
                break

    return added


def _trace_tributary(mapgen: "MapGen", *, source_hex: "Hex", flow_dir: dict["Hex", "Hex"]) -> int:
    first_downstream = flow_dir.get(source_hex)
    if first_downstream is None:
        return 0

    first_side = source_hex.get_side_to(first_downstream)
    if first_side is None:
        return 0

    first_edge = source_hex.get_edge(first_side)
    if first_edge is None or first_edge.is_river:
        return 0

    head = RiverSegment(mapgen.hex_grid, source_hex.x, source_hex.y, first_side, True)
    current_hex = source_hex
    current_segment = head
    visited_chain = {source_hex}
    segments = [head]

    while True:
        downstream = flow_dir.get(current_hex)
        if downstream is None:
            break

        side_to_downstream = current_hex.get_side_to(downstream)
        if side_to_downstream is None:
            break

        edge = current_hex.get_edge(side_to_downstream)
        if edge is None:
            break

        if edge.is_river and current_hex is source_hex:
            return 0

        already_river = edge.is_river
        edge.is_river = True
        current_segment.side = side_to_downstream

        if already_river or downstream in visited_chain:
            break

        next_segment = RiverSegment(mapgen.hex_grid, downstream.x, downstream.y, side_to_downstream, False)
        current_segment.next = next_segment
        current_segment = next_segment
        segments.append(next_segment)
        current_hex = downstream
        visited_chain.add(downstream)

    if len(segments) < 2:
        return 0

    for segment in segments:
        _set_segment_metadata(segment, branch_kind="tributary")

    mapgen.rivers_sources.append(head)
    mapgen.rivers.extend(segments)
    return len(segments)


def _carve_river_valleys(mapgen: "MapGen", *, depth: float, radius: int) -> int:
    if depth <= 0 or not mapgen.rivers_sources:
        return 0

    processed = 0
    sealevel = float(mapgen.hex_grid.sealevel)
    processed_coords: set[HexCoord] = set()

    for river_source in mapgen.rivers_sources:
        current = river_source
        while current is not None:
            hex_tile = mapgen.hex_grid.get(current.x, current.y)
            coord = (current.x, current.y)
            if coord in processed_coords:
                current = current.next
                continue

            if hex_tile is not None and hex_tile.is_land:
                processed_coords.add(coord)
                hex_tile.altitude = np.float64(max(sealevel + 2.0, float(hex_tile.altitude) - depth))
                processed += 1

                for neighbor in hex_tile.bubble(distance=radius):
                    if neighbor is hex_tile or not neighbor.is_land:
                        continue

                    distance = mapgen.hex_distance((hex_tile.x, hex_tile.y), (neighbor.x, neighbor.y))
                    if distance > radius:
                        continue

                    falloff = (radius - distance + 1) / (radius + 1)
                    neighbor.altitude = np.float64(
                        max(sealevel + 1.5, float(neighbor.altitude) - depth * 0.35 * falloff)
                    )

            current = current.next

    return processed
