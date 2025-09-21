# Signals

This document is about the signals that are send in the application and where they are send and listened to and to keep naming somewhat consistent.

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
- `r` (E: engine | L: camera)

- `wheel_up` (E: engine | L: camera)
- `wheel-down` (E: engine | L: camera)
- `mouse1` (E: engine | L: camera)
- `mouse3` (E: engine | L: camera)
- `escape` (E: engine | L: ui-part-load, L: ui-part-save, ui-part-pause)

### Debugging keys

These are used by the UI manager to control some debug actions these may disappear.

- `f2` (E: engine | L: manager-input) (debug: activate input system)
- `f3` (E: engine | L: manager-input) (debug: deactivate input system)
- `f7` (E: engine | L: manager-ui) (debug: run analysis)
- `f9` (E: engine | L: `tile<selected>`) (debug: trigger rerender on selected tile)
- `f10` (E: engine | L: `tile<selected>`) (debug: render bits on selected tile)
- `f11` (E: engine | L: `tile<selected>`) (debug: unrender bits on selected tile)

- `p` (E: engine | L: manager-ui)
- `l` (E: engine | L: manager-ui)
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
- `game.state.main_menu` (E: manager-ui | L: screen-game-ui)
- `game.state.request_load`(E: ui-part-load | L: manager-game)
- `game.state.reset_start` (E: manager-game | )
- `game.state.reset_finished` (E: manager-game | )
- `game.state.load_start` (E: manager-game | )
- `game.state.load_finished` (E: manager-game | )
- `game.state.save_start` (E: manager-game | )
- `game.state.save_finished` (E: manager-gamer | )

- `game.turn.request_end` (E:ui-player-turn-control | L:manager-turn)
- `game.turn.start_process` (E:manager-turn | L:manager-game, L:ui-player-turn-control)
- `game.turn.process_city` (E:manager-turn | L: city)
- `game.turn.end_process` (E:manager-turn | L:manager-game, L:ui-player-turn-control)

- `game.era.progressing` (E: manager-ages | L: manager-ui)
- `game.era.setting` (E: managers-ages | L: )

- `game.camera.request.center_on_tile` (E: action-search-map | L: system-camera)

- `game.gameplay.tiles.ownership_change` (E: manager-world | L: base-tile)
- `game.gameplay.unit.destroyed` (E: unit-base | L: screen-game-ui)

- `game.gameplay.unit.build_improvement_success` (E: action-build)
- `game.gameplay.unit.build_improvement_failure` (E: action-build)

- `game.gameplay.city.request_cancel_building_improvement_{tag}` (E:E ui-part-city | L: city)
- `game.gameplay.city.request_start_building_improvement_{tag}` (E: ui-part-city | L: city)
- `game.gameplay.city.starts_building_improvement` (E: city | L: ui-part-city)
- `game.gameplay.city.finish_building_improvement` (E: city | L: ui-part-city)
- `game.gameplay.city.canceled_production` (E: city | L: ui-part-city)
- `game.gameplay.city.border_growth` (E: city)

- `game.gameplay.city.request_start_building_unit` (E: ui-part-city | L: city)
- `game.gameplay.city.starts_building_unit` (E: ui-part-city | L: city)
- `game.gameplay.city.finishes_building_unit` (E: ui-part-city | L: city)

- `game.gameplay.city.population_grow` (E: city)
- `game.gameplay.city.population_starve` (E: city | L: manager-ui)
- `game.gameplay.city.requests_tile` (E: city | L: manager-world)
- `game.gameplay.city.gets_tile_ownership` (E: manager-world | L:city)

- `game.gameplay.research.request_start_research_session_player` (E: part-ui-research | L: player)
- `game.gameplay.research.player_queue_added_research` (E: managers-tech | L: )
- `game.gameplay.research.player_starts_research` (E: manager-player | L: manager-ui)
- `game.gameplay.research.player_cancels_research` (E: player | L: manager-ui)
- `game.gameplay.research.player_completed_research` (E: manager-tech | L: )

- `game.gameplay.civic.request_purchase` (E: part-ui-civic | L: )
- `game.gameplay.civic.player_purchased_civic` (E: part-ui-civic | L: )
- `game.gameplay.civic.player_tree_completed`  (E:  | L: )

### Units

- `unit.action.move.visiting_tile` (E: Tile | L: manager-ui)
- `unit.action.found_city.success` (E: action-found | )

## UI

- `ui.refresh.frame_insert` (E: * | L: manager-ui )

- `ui.update.user.tile_clicked"` (E: manager-game | L: manager-ui)
- `ui.update.user.unit_clicked` (E: manager-game | L: )
- `ui.update.user.city_clicked` (E: manager-ui | L: screen-game-ui)
- `ui.update.user.tile_hover` (E: manager-game | L: manager-ui)
- `ui.update.user.tile_unhover` (E: manager-game | L: manager-ui)
- `ui.update.user.enemy_city_clicked` (E: manager-ui | L: screen-game-ui)

- `ui.update.ui.unit_unselected` (E: manager-ui | L: screen-game-ui)

- `ui.request.update.borders` (L: manager-game | E: * )
- `ui.borders.updated` (E: system-border | L: manager-game)

- `ui.update.ui.show_research_ui` (E:ui-part-top-menu | L: ui-part-research)
- `ui.update.ui.hide_research_ui` (E:ui-part-top-menu, E:screen-game-ui | L: ui-part-research)

- `ui.update.ui.show_pause` (E: screen-game-ui | L: screen-pause-menu)
- `ui.update.ui.hide_pause` (E: screen-game-ui, E: manager-ui | L: screen-pause-menu)

- `ui.update.ui.show_save` (E: pause-menu-game-ui, E: main-menu-game-ui | L: ui-manager)
- `ui.update.ui.hide_save` (E: saveload-menu-game-ui | L: ui-manager)
- `ui.update.ui.show_load` (E: pause-menu-game-ui, E: main-menu-game-ui | L: ui-manager)
- `ui.update.ui.hide_load` (E: saveload-menu-game-ui | L: ui-manager)

- `ui.update.ui.show_player_info` (E: ui-player-list | L: manager-game )
- `ui.update.ui.hide_player_info` (E: ui-player-list | L: manager-game )

- `ui.update.ui.refresh_top_bar` (E: manager-ui | L: ui-part-top-bar)
- `ui.update.ui.refresh_player_turn_control` (E: manager-ui | L: ui-part-turn-control)
- `ui.update.ui.refresh_action_bar` (E: unit | L : manager-game-ui )
- `ui.update.ui.refresh_basic_elements` (E: * | L : game-ui)
- `ui.update.ui.refresh_combat_log` (E: * | L: player-combat-log-ui)

- `ui.update.ui.combat_log.add` (E: * | L: ui-player-combat-log )

- `ui.update.ui.messenger.refresh` (E: * | L: ui-messenger-renderer)

- `ui.update.ui.debug_ui_toggle` (E: ui-debug-actions | L: manager-ui)
- `ui.update.ui.resource_ui_change` (E: ui-debug-actions | L: manager-ui)
- `ui.update.ui.lense_change` (E: ui-debug-actions | L: manager-ui)

- `ui.request.save_game` (E: ui-part-save | L: manager-ui)
- `ui.request.open.popup` (E: actions-*, E:screen-game-ui | L: manager-ui)
- `ui.request.reroll` (E: ui-part-pause-menu | L: manager-ui)

- `ui.request.loading_screen` (E: game-config | L: manager-ui )
- `ui.loading.next_step` (E: * | L: screen-loading )

- `ui.request.action.stage` (E: debug | L: game-ui)

- `ui.notification.check` (E: * | L: manager-game)

## System

- `system.input.user.tile_clicked` (E: manager-input | L: manager-game)
- `system.input.user.unit_clicked` (E: manager-input | L: manager-game)
- `system.input.user.tile_hover` (E: manager-input | L: manager-game)
- `system.input.user.tile_unhover` (E: manager-input | L: manager-game)

- `system.input.raycaster_off` (L: manager-input)
- `system.input.raycaster_on` (L: manager-input)
- `system.input.raycaster_on_delay` (L: manager-input)

- `system.input.disable_zoom` (E: collision-mixin | L: camera)
- `system.input.enable_zoom` (E: collision-mixin | L: camera)

- `system.input.disable_control` (E: ui-part-save, E: ui-part-load | L: camera)
- `system.input.enable_control` (E: ui-part-save, E: ui-part-load | L: camera)

- `system.input.camera_lock` (E: ui-part-save, E: ui-part-load | L: camera)
- `system.input.camera_unlock` (E: ui-part-save, E: ui-part-load | L: camera)

- `system.game.start_load` (E:manager-ui, E:screen-game-config | L: manager-game)
- `system.game.player_game_over` (E: Lose | L: manager-game)
- `system.game.opponent_game_over` (E: Lose | L: manager-ui )

- `system.unit.destroyed` (E: unit-base)
