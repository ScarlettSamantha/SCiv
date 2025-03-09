import weakref
from logging import Logger
from typing import TYPE_CHECKING

from direct.showbase.MessengerGlobal import messenger

from managers.entity import EntityManager, EntityType
from mixins.singleton import Singleton
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.units.unit_base import UnitBaseClass  # Prevent circular import
    from main import Openciv


class Turn(Singleton):
    PREPARE_FOR_GAME = -1
    GAME_BEGIN = 0

    turn: int = PREPARE_FOR_GAME

    def __init__(self, base: "Openciv"):
        self.base: "Openciv" = base
        self.active = False
        self.logger: Logger = self.base.logger.engine.getChild("manager.turn")

    def __setup__(self, base, *args, **kwargs):
        self.base: "Openciv" = base
        self.logger: Logger = self.base.logger.engine.getChild("manager.turn")
        return super().__setup__(*args, **kwargs)

    def register(self):
        pass

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
        pass

    def process(self):
        self.logger.info(f"Processing turn {self.turn}, sending start_process signal.")
        messenger.send("game.turn.start_process", [self.turn])

        def world():
            self.logger.info("Processing world turn changes.")

        def players():
            self.logger.info("Processing player turn changes.")

        def units():
            self.logger.info("Processing unit turn changes.")

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

            self.logger.info("Restoring all movement points for all units.")
            restore_all_movement_points()

        world()
        players()
        units()

        self.turn += 1
        self.logger.info(f"Turn {self.turn} processed, sending end_process signal.")
        messenger.send("game.turn.end_process", [self.turn])
