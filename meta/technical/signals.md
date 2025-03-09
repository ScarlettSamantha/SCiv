# Signals

This document is about the signals that are send in the application and where they are send and listend to and to keep naming somewhat consistent.

## Keys

These are all used by the camera system and are used for mainly controlling the camera.

- `arrow-up` (E: engine | L: camera)
- `arrow-down` (E: engine | L: camera)
- `arrow-left` (E: engine | L: camera)
- `arrow-right` (E: engine | L: camera)
- `w` (E: engine | L: camera)
- `s` (E: engine | L: camera)
- `d` (E: engine | L: camera)
- `q` (E: engine | L: camera)
- `e` (E: engine | L: camera)
- `wheel_up` (E: engine | L: camera)
- `wheel-down` (E: engine | L: camera)
- `r` (E: engine | L: camera)
- `mouse1` (E: engine | L: camera)
- `mouse3` (E: engine | L: camera)

### Debugging keys

These are used by the UI manager to controll some debug actions these may disapear.

- `f7` (E: engine | L: manager-ui)
- `p` (E: engine | L: manager-ui)
- `l` (E: engine | L: manager-ui)
- `n` (E: engine | L: manager-ui)
- `m` (E: engine | L: manager-ui)
- `b` (E: engine | L: manager-ui)
- `z` (E: engine | L: manager-ui)
- `x` (E: engine | L: manager-ui)
- `c` (E: engine | L: manager-ui)

## Game

- `game.requests.end_turn` (manager-game)
- `game.input.user.escape_pressed` (E: manager-input | L:manager-game, L:manager-ui)
- `game.input.user.quit_game` (E: ui-main-menu, E: ui-pause-menu | L: manager-game)
- `game.input.user.wireframe_toggle` (E:NONE | L: manager-game)
- `game.state.true_game_start` (E: manager-game | L: manager-ui)
- `game.turn.request_end` (E:ui-player-turn-control | L:manager-turn)
- `game.turn.start_process` (E:manager-turn | L:manager-game, L:ui-player-turn-controll)
- `game.turn.end_process` (E:manager-turn | L:manager-game, L:ui-player-turn-controll)

### Units

- `unit.action.move.visiting_tile` (E: BaseTile | L: manager-ui)

## UI

- `ui.update.user.tile_clicked"` (E: manager-game | L: manager-ui, L: screen-game-ui)
- `ui.update.user.unit_clicked` (E: manager-game | L: screen-game-ui)
- `ui.update.ui.debug_ui_toggle` (E: ui-debug-actions | L: manager-ui)
- `ui.update.ui.resource_ui_change` (E: ui-debug-actions | L: manager-ui)
- `ui.update.ui.lense_change` (E: ui-debug-actions | L: manager-ui)
- `ui.request.open.popup` (E: actions-* | L: manager-ui)

## Sytem

- `system.input.user.tile_clicked` (E: manager-input | L: manager-game)
- `system.input.user.unit_clicked` (E: manager-input | L: manager-game)
- `system.game.start_load` (E:manager-ui, E:screen-game-config | L: manager-game)
