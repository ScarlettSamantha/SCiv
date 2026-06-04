from scripts.worldgen_viewer_support import format_hex_details, load_worldgen_payload


def test_load_worldgen_payload_exposes_territory_names_and_labels() -> None:
    dump = load_worldgen_payload(
        {
            "generator": {"name": "Test Generator", "seed": 11},
            "dimensions": {"requested": {"width": 2, "height": 1}, "raw_grid_size": 2},
            "summary": {"territory_count": 1},
            "raw": {
                "hexes": [
                    {
                        "coord": [0, 0],
                        "visible_in_runtime": True,
                        "altitude": 12.0,
                        "moisture": 4.5,
                        "temperature": 13.0,
                        "terrain": "flatgrass",
                        "biome": {"key": "grasslands", "title": "Grasslands"},
                        "territory_id": 1,
                        "is_land": True,
                        "is_water": False,
                        "is_inland": True,
                        "is_coast_land": False,
                        "is_coast_water": False,
                        "features": [],
                        "river_segments": [],
                    },
                    {
                        "coord": [1, 0],
                        "visible_in_runtime": True,
                        "altitude": 13.0,
                        "moisture": 4.2,
                        "temperature": 13.2,
                        "terrain": "flatgrass",
                        "biome": {"key": "grasslands", "title": "Grasslands"},
                        "territory_id": 1,
                        "territory_name": "Green March",
                        "is_land": True,
                        "is_water": False,
                        "is_inland": True,
                        "is_coast_land": False,
                        "is_coast_water": False,
                        "features": [],
                        "river_segments": [],
                    },
                ],
                "territories": [
                    {
                        "id": 1,
                        "name": "Green March",
                        "main": [0, 0],
                        "hexes": [[0, 0], [1, 0]],
                    }
                ],
                "named_regions": {},
                "rivers": [],
            },
        }
    )

    assert dump.territory_names_by_id == {1: "Green March"}
    assert dump.named_regions["territories"][0].name == "Green March"
    assert "Green March (ID 1)" in format_hex_details(dump, (0, 0))
