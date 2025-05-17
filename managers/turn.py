import weakref
from datetime import datetime
from enum import Enum
from logging import Logger
from typing import TYPE_CHECKING, Any

from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger

from managers.entity import EntityManager, EntityType
from managers.player import PlayerManager
from mixins.singleton import Singleton
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.player import Player
    from gameplay.unit import Unit  # Prevent circular import
    from main import SCIV


class TurnStage(Enum):
    NO_TURN_CHANGE = -1
    TURN_CHANGE_BEGIN = 0
    TURN_WORLD = 1
    TURN_PLAYERS = 2
    TURN_PLAYERS_CITIES = 3
    TURN_PLAYERS_UNITS = 4
    TURN_UNITS = 5
    TURN_CHANGE_END = 6


class Turn(Singleton, DirectObject):
    PREPARE_FOR_GAME = -1
    GAME_BEGIN = 0

    turn: int = PREPARE_FOR_GAME

    def __init__(self, base: "SCIV"):
        self.base: "SCIV" = base
        self.active = False
        self.logger: Logger = self.base.logger.engine.getChild("manager.turn")
        self.turn_stage: TurnStage = TurnStage.NO_TURN_CHANGE
        super().__init__()
        self.register()

    def __setup__(self, base: "SCIV", *args: Any, **kwargs: Any):
        self.base: "SCIV" = base
        self.logger: Logger = self.base.get_child_logger("manager.turn")
        self.register()
        return super().__setup__(*args, **kwargs)

    def register(self):
        self.accept("game.requests.end_turn", self.end_turn)

    def reset(self):
        self.turn = self.PREPARE_FOR_GAME
        self.active = False

    def de_activate(self):
        self.active = False

    def activate(self):
        self.active = True
        self.turn = self.GAME_BEGIN

    def end_turn(self):
        self.process()

    def get_turn(self) -> int:
        return self.turn

    def set_turn(self, turn_num: int):
        self.turn = turn_num

    def process(self):
        self.logger.info(f"Processing turn {self.turn}, sending start_process signal.")
        messenger.send("game.turn.start_process", [self.turn])

        timings: dict[str, float] = {}

        def world():
            from managers.world import World

            _start = datetime.now()
            self.logger.info("Processing world turn changes.")
            self.turn_stage = TurnStage.TURN_WORLD
            World.get_singleton_instance().on_turn_end(self.turn)
            timings["world"] = (datetime.now() - _start).total_seconds()
            self.logger.debug(f"Turn {self.turn} processing for world took: {timings['world']:.4f} seconds.")

        def players():
            _start = datetime.now()
            self.logger.info("Processing player turn changes.")

            def cities(player: "Player"):
                self.logger.info("Processing player city turn changes.")
                self.turn_stage = TurnStage.TURN_PLAYERS_CITIES
                for city in player.cities:
                    city: "City" = city
                    self.logger.info(f"Processing city {city.name} turn changes.")
                    city.on_turn_end(self.turn)

            nature_player: Player = PlayerManager.get_nature()
            self.logger.info("Processing nature player turn changes.")
            nature_player.on_turn_end(self.turn)

            barbarians: Player = PlayerManager.get_barbarian()
            self.logger.info("Processing barbarian player turn changes.")
            barbarians.on_turn_end(self.turn)

            for player in PlayerManager.all().values():
                player: "Player" = player
                self.logger.info(f"Processing player {player.name} turn changes.")
                player.on_turn_end(self.turn)
                cities(player)

            timings["players"] = (datetime.now() - _start).total_seconds()
            self.logger.debug(f"Turn {self.turn} processing for players took: {timings['players']:.4f} seconds.")

        def units():
            _start = datetime.now()
            self.logger.info("Processing unit turn changes.")
            self.turn_stage = TurnStage.TURN_UNITS

            def restore_all_movement_points():
                entity_manager: EntityManager = EntityManager.get_singleton_instance()
                for _, entity in entity_manager.get_all_refs(EntityType.UNIT).items():
                    entity: weakref.ReferenceType["BaseEntity"] = entity
                    entity_instance: "Unit | None" = entity()  # type: ignore

                    if entity_instance is not None:
                        entity_instance.restore_movement_points()
                    else:
                        self.logger.warning(f"Unit entity {entity} was None, skipping.")

                    if entity_instance is not None:
                        entity_instance.effects.on_turn_end(self.turn)

            self.logger.info("Restoring all movement points for all units.")
            restore_all_movement_points()
            timings["units"] = (datetime.now() - _start).total_seconds()
            self.logger.debug(f"Turn {self.turn} processing for units took: {timings['units']:.4f} seconds.")

        # Run stages
        world()
        players()
        units()

        self.turn += 1
        self.turn_stage = TurnStage.NO_TURN_CHANGE

        # Dump a single timing line for the turn
        timing_line = f"Turn {self.turn} timings: " + ", ".join(f"{k}: {v:.4f}s" for k, v in timings.items())
        self.logger.info(timing_line)
        # You can also send it via messenger if you want
        messenger.send("game.turn.timings", [self.turn, timings])

        self.logger.info(f"Turn {self.turn} processed, sending end_process signal.")
        messenger.send("game.turn.end_process", [self.turn])
