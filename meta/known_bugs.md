# Known Bugs

## UI

- [X] Units can teleport to random tiles
- [x] Units dont respect not climbing over mountains (without tech)
- [ ] Issues with the dropdowns
- [ ] Cant keep selection of unit properly internally when a tile is clicked.
- [ ] Window drifts up and right very slightly over time (meaby because of writeback system?)

### Things that seem like bugs

- [ ] UI buttons not updating with keyboard shortcuts for it.

## Gameplay

- [X] Found actions is broken

### Units

- [X] Water seems to be having some impact on path finding that it should not, I think it has to do with the heuristics from A* in the repository (@after-fixed: had to do with what tile was set.)
- [X] Tile standing on was also counted for movement.
- [ ] Units can spawn on mountains (meaby see: data.tiles.base_tile.BaseTile.is_spawnable_upon last check with mountains)

## Map/World

- [X] When generating it will sometimes with smaller maps get stuck on generating aquafers I think I know why this is, it might have to do that its trying to spawn many aquafers but cant find a place for them all and gets stuck infinitly. (@after-fixed: Refactored it into a sum instead of a flat hardcoded parametered random_int)
