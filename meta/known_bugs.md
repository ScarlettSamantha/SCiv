# Known Bugs

## UI

- [X] Units can teleport to random tiles
- [x] Units don't respect not climbing over mountains (without tech)
- [x] Issues with the dropdowns
- [x] Cant keep selection of unit properly internally when a tile is clicked.
- [x] Window drifts up and right very slightly over time (maybe because of write-back system?)
- [X] Unit action bar does not clear properly.

### Things that seem like bugs

- [ ] UI buttons not updating with keyboard shortcuts for it.

## Gameplay

- [ ] When citizens reach zero it will not disappear yes. This has not been implemented together with a failure condition in general.
- [X] Found actions is broken

### Units

- [X] Water seems to be having some impact on path finding that it should not, I think it has to do with the heuristics from A* in the repository (@after-fixed: had to do with what tile was set.)
- [X] Tile standing on was also counted for movement.
- [X] Units can spawn on mountains (maybe see: data.tiles.base_tile.BaseTile.is_spawnable_upon last check with mountains)

## Map/World

- [X] When generating it will sometimes with smaller maps get stuck on generating aquifers I think I know why this is, it might have to do that its trying to spawn many aquifers but cant find a place for them all and gets stuck infinity. (@after-fixed: Refactored it into a sum instead of a flat hardcoded parameterized random_int)
