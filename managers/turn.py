import weakref
from datetime import datetime
from enum import Enum
from logging import Logger
from typing import TYPE_CHECKING

from direct.showbase.MessengerGlobal import messenger

from gameplay.improvement import Player
from managers.entity import EntityManager, EntityType
from managers.player import PlayerManager
from mixins.singleton import Singleton
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.units.unit_base import UnitBaseClass  # Prevent circular import
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


class Turn(Singleton):
    PREPARE_FOR_GAME = -1
    GAME_BEGIN = 0

    turn: int = PREPARE_FOR_GAME

    def __init__(self, base: "SCIV"):
        self.base: "SCIV" = base
        self.active = False
        self.logger: Logger = self.base.logger.engine.getChild("manager.turn")
        self.turn_stage: TurnStage = TurnStage.NO_TURN_CHANGE

    def __setup__(self, base, *args, **kwargs):
        self.base: "SCIV" = base
        self.logger: Logger = self.base.logger.engine.getChild("manager.turn")
        return super().__setup__(*args, **kwargs)

    def register(self):
        pass

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

        def world():
            from managers.world import World

            _timer_world = datetime.now()
            self.logger.info("Processing world turn changes.")
            self.turn_stage = TurnStage.TURN_WORLD
            World.get_instance().on_turn_end(self.turn)  # World manager will forward the signal to all tiles
            self.logger.debug(
                f"Turn {self.turn} processing for world took: {round((datetime.now() - _timer_world).total_seconds() * 1000, 4)} miliseconds."
            )

        def players():
            self.logger.info("Processing player turn changes.")
            _timer_players = datetime.now()

            def cities(player: Player):
                self.logger.info("Processing player city turn changes.")
                self.turn_stage = TurnStage.TURN_PLAYERS_CITIES
                for city in player.cities:
                    city: "City" = city  # this is a type hint
                    self.logger.info(f"Processing city {city.name} turn changes.")
                    city.on_turn_end(self.turn)

            for player in PlayerManager.all().values():
                player: "Player" = player
                self.logger.info(f"Processing player {player.name} turn changes.")
                player.on_turn_end(self.turn)
                cities(player)

            self.logger.debug(
                f"Turn {self.turn} processing for players took: {round((datetime.now() - _timer_players).total_seconds() * 1000, 4)} miliseconds."
            )

        def units():
            self.logger.info("Processing unit turn changes.")
            _timer_units = datetime.now()
            self.turn_stage = TurnStage.TURN_UNITS

            def restore_all_movement_points():
                entity_manager: EntityManager = EntityManager.get_instance()
                for _, entity in entity_manager.get_all_refs(EntityType.UNIT).items():
                    entity: weakref.ReferenceType["BaseEntity"] = entity

                    if entity is None:
                        self.logger.warning(f"Entity {entity} was None, skipping.")
                        continue

                    entity_instance: "UnitBaseClass | None" = entity()  # type: ignore

                    if entity_instance is not None:
                        entity_instance.restore_movement_points()
                    else:
                        self.logger.warning(f"Unit entity {entity} was None, skipping.")

                    if entity_instance is not None:
                        entity_instance.effects.on_turn_end(self.turn)

            self.logger.info("Restoring all movement points for all units.")
            restore_all_movement_points()
            self.logger.debug(
                f"Turn {self.turn} processing for units took: {round((datetime.now() - _timer_units).total_seconds() * 1000, 4)} miliseconds."
            )

        world()
        players()
        units()

        self.turn += 1
        self.turn_stage = TurnStage.NO_TURN_CHANGE
        self.logger.info(f"Turn {self.turn} processed, sending end_process signal.")
        messenger.send("game.turn.end_process", [self.turn])
