import random
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type

from direct.showbase.MessengerGlobal import messenger
import numpy as np
from panda3d.core import (
    BitMask32,
    ColorBlendAttrib,
    GeomNode,
    LVector3,
    LVecBase3f,
    LineSegs,
    CardMaker,
    NodePath,
    PythonTask,
    Shader,
    Texture,
    TextureStage,
    TransparencyAttrib,
)


from direct.showbase import MessengerGlobal
from direct.task import Task
from gameplay.condition import Conditions
from gameplay.floating_text import spawn_damage_text
from gameplay.repositories.tile import TileRepository
from gameplay.resources.core.basic.production import Production
from helpers.colors import Tuple4f
from game import Cache
from managers.combat import T_TARGET, Combat, CombatOutcome, CombatResults
from managers.combat_log import CombatLog
from managers.entity import uuid4
from managers.i18n import T_TranslationOrStrOrNone
from managers.player import PlayerManager
from managers.unit import UnitManager
from sciv.helpers.windows import WindowsHelper
from system.actions import Action
from system.effects import Effects
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.improvement import BasicBaseResource
    from gameplay.player import Player
    from gameplay.promotion import PromotionTree
    from gameplay.tile import Tile


class CantMoveReason(Enum):
    USER_INPUT_ERROR = -3  # This is when the user input is invalid, e.g. trying to move to a non-tile target.
    SAME_TILE = -2  # This is a special case where the unit is already on the tile
    COULD_MOVE = -1  # This is more of a ok unit could move.
    NO_MOVES = 0  # This is when the unit has no moves left
    NO_PATH = 1  # This is when the unit has no path to the target
    NO_TARGET = 2  # This is when the unit has no target this is a bug.
    IMMOBILE = 3  # This is when the unit is immobile and cannot move.
    IMPASSABLE = 4  # This is only when the target tile is impassable as otherwise routing would have caught it. and trigger NO_PATH
    NO_OWNER = 5  # This is when the unit has no owner
    OTHER_OWNER = 6  # This is when the target tile is owned by another player this can integrate with the other owner in some way.
    NO_UNIT = 7  # This is when the unit has no unit to move this is a bug.
    UNIT_TRAPPED_MIDWAY = 8  # This is when the unit is trapped midway through the path as the tiles have an on_visit check which can be used to trap the unit this can be used to do partial logic.
    OTHER_UNIT_ON_TILE = 9  # This might have to integrate with the other owner in some way ether being it attacking or being attacked or just not being able to move.


class Unit(BaseEntity, ABC):
    _model: Optional[str] = None

    buildable: bool = False
    build_conditions: Conditions = Conditions()
    name: T_TranslationOrStrOrNone
    description: T_TranslationOrStrOrNone
    icon: str | Path | None
    promotion_tree: Type["PromotionTree"]
    model: Optional[NodePath] = None
    model_size: float = 1.0

    can_spawn_on_land: bool = True
    can_spawn_on_water: bool = False
    max_health: float = 10.0

    def __init__(self, tile: "Tile", player: "Player", key: Optional[str] = None, *args: Any, **kwargs: Any):
        from gameplay.city import Yields  # to avoid circular import

        BaseEntity.__init__(self, tile=tile, owner=player, *args, **kwargs)

        self.key: str = key if key else uuid4().hex
        self.tag = self.generate_unit_tag()

        self.model_rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Default rotation of the model
        self.model_position_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.collides: bool = True
        self.actions: List[Action] = []

        self.pos_y: float = 0.0
        self.pos_x: float = 0.0
        self.pos_z: float = 0.0

        self.max_moves: int = 2
        self.moves_left: int | float = 2.0

        self.model: Optional[NodePath] = None
        self.selection_radius: float = 1.0
        self.selection_enabled: bool = True
        self.selection_circle: Optional[NodePath] = None
        self.rotation_task: Optional[PythonTask] = None
        self.unit_icons: Optional[NodePath] = None
        self.unit_icons_z_offset: float = 0.3
        self.unit_icons_scale: float = 0.5

        self.can_cross_water: bool = self.can_spawn_on_water
        self.can_cross_land: bool = self.can_spawn_on_land
        self.can_fly: bool = False

        self.can_move: bool = True
        self.can_attack: bool = True
        self.can_heal: bool = True
        self.can_pillage: bool = True
        self.can_build: bool = False

        self.is_being_build: bool = False

        self.resource_needed: Type["BasicBaseResource"] = Production
        self.amount_resource_needed: Yields = Yields(production=10)

        self.effects: Effects = Effects(self)

        self.build_charges: int = 0
        self.build_charges_left: int = 0

        self._logger = None

        self.model_cache: Optional[NodePath] = None

        self.selection_shader = Shader.load(
            Shader.SL_GLSL,
            vertex=self.base.base_path / "assets/shaders/unit_selection.vert.glsl",
            fragment=self.base.base_path / "assets/shaders/unit_selection.frag.glsl",
        )

        self.register_actions()
        if self.is_registered is False:
            self.register()

    @abstractmethod
    def register_actions(self):
        if self.can_move:
            from gameplay.actions.unit.move import WalkAction

            self.add_action(WalkAction(self))

        if self.can_attack:
            if self.attack_power_mele > 0:
                from gameplay.actions.unit.attack_mele import AttackAction

                self.add_action(AttackAction(self))

    @property
    def logger(self):
        if self._logger is None:
            self._logger = Cache.get_showbase_instance().logger.get_singleton_instance().gameplay.getChild("unit")
        return self._logger

    def get_pos(self) -> Tuple[float, float, float]:
        return (self.pos_x, self.pos_y, self.pos_z)

    def load_model(self) -> NodePath | None:
        from system.tile_render import NET_NODE_TAG_ID_FIELD, NET_TYPE_FIELD, NET_TYPE

        if self.model is not None:
            return self.model

        if self._model is None:
            raise ValueError(f"Unit {self.key} has no model assigned.")

        pos = self.get_tile().calculate_z_pos_on_altitude()

        model_path: str = str(self.base.base_path / self._model)
        if WindowsHelper.is_windows():
            model_path = WindowsHelper.win32_to_unix_path(model_path)

        self.model = self.base.loader.loadModel(model_path)

        if self.model is None:
            raise ValueError(f"Unit {self.key} model could not be loaded.")

        self.model.reparent_to(self.base.render)
        self.model.setName(f"unit_{self.key}")

        self.model.flatten_medium()

        self.model.setHpr(LVector3(*self.model_rotation))
        self.model.setPos(*pos)
        self.model.setScale(self.model_size)
        self.model.setCollideMask(BitMask32.bit(1))
        self.model.setTag(NET_NODE_TAG_ID_FIELD, self.tag)
        self.model.setTag(NET_TYPE_FIELD, NET_TYPE.UNIT.value)

        if self.icon is not None:
            texture = Cache.get_icon_atlas().get_panda3d_texture_by_virtual_path(str(self.icon))
            if texture is None:
                raise ValueError(f"Icon texture for unit {self.key} not found at path: {self.icon}")

            cm = CardMaker("marker_quad")
            cm.set_frame(-0.5, 0.5, -0.5, 0.5)
            self.unit_icons = self.model.attachNewNode(cm.generate())

            bounds = self.model.getTightBounds() if self.model else None
            height = bounds[1].z - bounds[0].z if bounds else 0
            self.unit_icons.setPos(0, 0, height + self.unit_icons_z_offset)  # type: ignore

            ts = TextureStage("icon")

            texture.setFormat(Texture.F_srgb_alpha)
            self.unit_icons.setScale(self.unit_icons_scale)  # Scale the texture
            self.unit_icons.set_texture(ts, texture)  # type: ignore
            self.unit_icons.setTransparency(1)  # type: ignore

            self.unit_icons.setAttrib(  # type: ignore
                ColorBlendAttrib.make(  # type: ignore
                    ColorBlendAttrib.MAdd,
                    ColorBlendAttrib.OIncomingAlpha,
                    ColorBlendAttrib.OOneMinusIncomingAlpha,
                )
            )

            self.unit_icons.set_depth_write(True)  # type: ignore
            self.unit_icons.set_depth_test(True)  # type: ignore
            self.unit_icons.setTwoSided(True)  # type: ignore

            self.unit_icons.set_bin("transparent", 90)  # type: ignore

            self.unit_icons.set_shader(  # type: ignore
                Shader.load(  # type: ignore
                    Shader.SL_GLSL,
                    self.base.base_path / "assets/shaders/unit_icon.vert",
                    self.base.base_path / "assets/shaders/unit_icon.frag",
                )
            )
            self.unit_icons.set_shader_input("billboard_position", pos)  # type: ignore
            self.unit_icons.set_shader_input("size", LVecBase3f(0.2, 0.2, 0))  # type: ignore
            self.unit_icons.set_shader_input("iconTex", texture)  # type: ignore

            self.healthbar_np = self.unit_icons.attachNewNode("healthbar")
            self.healthbar_np.setPos(0, 0, 0.75)
            self.healthbar_np.setScale(1.25, 1, 1.5)

            cm = CardMaker("healthbar_quad")
            cm.setFrame(-0.625, 0.625, -0.1125, 0.1125)
            bar_np = self.healthbar_np.attachNewNode(cm.generate())

            bar_np.setTransparency(TransparencyAttrib.MAlpha)
            bar_np.setAttrib(
                ColorBlendAttrib.make(
                    ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOneMinusIncomingAlpha
                )
            )
            bar_np.setBin("fixed", 50)
            bar_np.setDepthTest(False)
            bar_np.setDepthWrite(False)
            bar_np.setTransparency(TransparencyAttrib.MAlways, 1)  #     type: ignore

            self.healthbar_shader = Shader.load(
                Shader.SL_GLSL,
                self.base.base_path / "assets/shaders/unit_healthbar.vert.glsl",
                self.base.base_path / "assets/shaders/unit_healthbar.frag.glsl",
            )
            bar_np.setShader(self.healthbar_shader)
            bar_np.setShaderInput("health_ratio", 1.0)  # type: ignore
            bar_np.setShaderInput("border", 0.025)  # 2% border thickness # type: ignore
            bar_np.setShaderInput("color", self.get_owner().color)  # green color # type: ignore
            # 5) store quad for updates
            self._healthbar_quad = bar_np

        return self.model

    def _create_selection_circle(
        self,
        num_segments: int = 64,
        dash_length: int = 2,
        color: Optional[Tuple4f] = None,
        line_thickness: float = 4.0,
    ) -> NodePath:
        if not self.model:
            raise ValueError(f"No model loaded for unit {self.key}.")

        color = self.get_owner().get_color()
        segs = LineSegs()

        segs.setThickness(line_thickness)
        segs.setColor(color)
        num_segments = num_segments if num_segments > 0 else 64

        radius = self.selection_radius
        angle_step = 360.0 / num_segments
        dash_length = dash_length if dash_length > 0 else 2

        for i in range(num_segments):
            if (i // dash_length) % 2 == 0:
                angle1 = np.radians(i * angle_step)
                angle2 = np.radians((i + 1) * angle_step)
                segs.moveTo(radius * np.cos(angle1), radius * np.sin(angle1), 0.0)
                segs.drawTo(radius * np.cos(angle2), radius * np.sin(angle2), 0.0)

        node = segs.create()
        circle_np = NodePath(GeomNode(f"sel-circle-{id(self)}"))
        circle_np.node().addGeomsFrom(node)
        circle_np.setHpr(90, 0, 0)

        circle_np.setPos(0, 0, 0 + 0.1)  # type: ignore

        if self.selection_shader:
            circle_np.setShader(self.selection_shader)
            circle_np.setShaderInput("dashLength", dash_length)  # type: ignore
            circle_np.setShaderInput("dashFreq", 18.0)  # type: ignore
            circle_np.setShaderInput("pulseSpeed", 2.0)  # type: ignore
            circle_np.setShaderInput("borderWidth", 0.05)  # type: ignore
            circle_np.setShaderInput("radius", 1)  # type: ignore
            circle_np.setShaderInput("time", 0.0)  # type: ignore
            circle_np.setShaderInput("color", color)  # type: ignore

        circle_np.hide()
        circle_np.reparentTo(self.model)
        return circle_np

    def _rotate_indicator_task(self, task: Task.Task) -> Task.Task:
        if self.selection_enabled and self.selection_circle:
            self.selection_circle.setH(task.time * 60.0)
        return Task.cont  # type: ignore

    def on_load(self):
        self.base = Cache.get_showbase_instance()
        self._logger = Cache.get_showbase_instance().logger.get_singleton_instance().gameplay.getChild("unit")
        self.effects = Effects(self)
        self.actions = []
        self.model = None
        self.model_cache = None
        self.health_left: float = self.max_health
        self.moves_left = self.max_moves
        self.register_actions()
        self.register()
        UnitManager.get_singleton_instance().add_unit(self)

        self.spawn(ignore_constraints=True)

    def __getstate__(self) -> Dict[str, Any]:
        state = super().__getstate__()
        state.pop("base", None)
        state.pop("_logger", None)
        state.pop("model", None)
        state.pop("model_cache", None)
        state.pop("effects", None)
        state.pop("actions", None)
        state.pop("renderer", None)
        state["resource_needed"] = self.resource_needed.__name__ if self.resource_needed else None
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        from gameplay.resources.core.basic.production import Production

        self.base = Cache.get_showbase_instance()
        self._logger = Cache.get_showbase_instance().logger.get_singleton_instance().gameplay.getChild("unit")
        self.model = None
        self.model_cache = None
        self.effects = Effects(self)
        self.actions = []
        self.resource_needed = Production
        self.tile = state.get("tile")  # type: ignore
        self.tag = str(state.get("tag"))
        for key, value in state.items():
            setattr(self, key, value)

    def register(self) -> None:
        from managers.entity import EntityManager, EntityType

        self.is_registered = True

        entity_manager: EntityManager = EntityManager.get_singleton_instance()

        entity_manager.register(entity=self, type=EntityType.UNIT, key=self.tag)

        if self.owner is not None:
            self.owner.units.add_unit(entity_manager.get(EntityType.UNIT, str(self.tag)))  # type: ignore

        UnitManager.get_singleton_instance().add_unit(self)

    def set_pos(self, pos: Tuple[float, float, float]) -> None:
        self.pos_x, self.pos_y, self.pos_z = pos

    def is_alive(self) -> bool:
        return self.health() > 0

    def unregister(self) -> None:
        from managers.entity import EntityManager, EntityType

        EntityManager.get_singleton_instance().unregister(entity=self, type=EntityType.UNIT)
        UnitManager.get_singleton_instance().remove_unit(self)

    def spawn(self, ignore_constraints: bool = False) -> NodePath | None:
        self.calculate_model_position()
        self.load_model()

    def get_model_path(self) -> Optional[str]:
        if isinstance(self._model, str):
            return self._model
        return None

    def get_actions(self) -> List[Action]:
        return self.actions

    @classmethod
    def spawn_on(cls, tile: "Tile", player: "Player", ignore_constraints: bool = False) -> "Unit":
        if (
            not ignore_constraints
            and (cls.can_spawn_on_water and tile.is_land)
            and (cls.can_spawn_on_land and tile.is_water)
        ):
            raise ValueError(f"Unit {cls.__name__} cannot spawn on tile {tile.tag} due to constraints.")

        if tile.is_passable is False:
            raise ValueError(f"Unit {cls.__name__} cannot spawn on impassable tile {tile.tag}.")

        instance = cls(tile=tile, player=player)
        instance.owner = player
        instance.spawn()

        tile.add_unit(instance)
        UnitManager.get_singleton_instance().add_unit(instance)
        tile.render()
        return instance

    def move(self, tile: "Tile") -> CantMoveReason:
        from gameplay.repositories.tile import TileRepository

        target_tile: "Tile" = tile

        if not self.can_move:
            return CantMoveReason.IMMOBILE

        if self.moves_left <= 0:
            return CantMoveReason.NO_MOVES

        if target_tile.passable is False:
            return CantMoveReason.IMPASSABLE

        if len(target_tile.units) > 0:
            return CantMoveReason.OTHER_UNIT_ON_TILE

        tiles_to_move = []
        # Attempt pathfinding
        if self.tile is not None and (tiles_to_move := TileRepository.astar(self.get_tile(), target_tile, 1.0)) is None:
            return CantMoveReason.NO_PATH

        # This was a bug for a while, but it was fixed
        if (len(tiles_to_move) - 1) == 0:
            return CantMoveReason.SAME_TILE

        if self.tile is None:
            raise AssertionError(f"Unit {self.key} has no tile assigned.")

        if tiles_to_move[0] == self.get_tile():
            del tiles_to_move[0]  # Remove the first tile as it is the current tile

        departing_tile: "Tile" = self.get_tile()  # Start off at our current tile
        current_tile: "Tile" = self.get_tile()

        for _tile in tiles_to_move:
            if (self.moves_left - _tile.movement_cost) < 0:
                self._move_to_tile(current_tile, departing_tile)
                return CantMoveReason.NO_MOVES

            self.moves_left -= _tile.movement_cost

            if _tile.is_visisted_by(self) is False:
                # Move partially onto this tile and then get trapped or do partial logic
                self._move_to_tile(_tile, departing_tile)
                return CantMoveReason.UNIT_TRAPPED_MIDWAY

            current_tile = _tile

        self._move_to_tile(current_tile, departing_tile)  # Move to the last tile in the path
        if current_tile == target_tile:
            return CantMoveReason.COULD_MOVE
        return CantMoveReason.NO_MOVES

    def _clear_departing_tile(self, tile: "Tile") -> None:
        tile.remove_unit(self)
        tile.render()

    def _move_to_tile(self, tile: "Tile", clear_departing_tile: Optional["Tile"] = None) -> None:
        if clear_departing_tile is not None:
            self._clear_departing_tile(clear_departing_tile)

        self.set_tile(tile)
        self.model = self.load_model()
        self.calculate_model_position()
        self.get_tile().add_unit(self)
        self.get_tile().render()

        if self.owner == PlayerManager.session_player():
            MessengerGlobal.messenger.send("ui.update.ui.refresh_action_bar")

    def calculate_model_position(self) -> None:
        tile_pos = self.get_tile().get_cords()
        self.pos_x, self.pos_y, self.pos_z = tile_pos
        if self.model is not None:
            self.model.setPos(
                self.pos_x + self.model_position_offset[0],
                self.pos_y + self.model_position_offset[1],
                self.pos_z + self.model_position_offset[2],
            )

    def select(self):
        if self.selection_circle is None:
            self.selection_circle = self._create_selection_circle()

        self.selection_circle.show()
        self.rotation_task = self.add_task(self._rotate_indicator_task, "rotate_selection_circle", delay=1 / 30)  # type: ignore

    def deselect(self):
        if self.selection_circle is not None:
            self.selection_circle.hide()
            self.remove_task("rotate_selection_circle")  # type: ignore

    def add_action(self, action: Action) -> None:
        self.actions.append(action)

    def remove_action(self, action: Action) -> None:
        self.actions.remove(action)

    def unload_model(self) -> None:
        if self.model is not None:
            self.model.removeNode()
            self.model = None

    def generate_unit_tag(self) -> str:
        return f"unit_{self.key}_{random.randint(0, 1000000)}"

    def tile_is_occupiable(self, tile: "Tile") -> bool:
        return tile.is_passable() and len(tile.units) == 0

    def restore_movement_points(self) -> None:
        """Resets the unit's movement points to the maximum value. Called by the Turn manager."""
        self.moves_left = self.max_moves

    def drain_movement_points(self, cost_or_zero: float | None = None) -> None:
        if cost_or_zero is None:
            self.moves_left = 0
        else:
            self.moves_left -= cost_or_zero

    def set_color(self, color: Tuple[float, float, float, float]) -> None:
        if isinstance(self.model, str) and not isinstance(self.model, NodePath):  # type: ignore
            raise ValueError(f"Unit {self.key} has no model assigned.")
        if self.model is not None:  # type: ignore
            self.model.setColor(*color)  # type: ignore If check above passes, model is NodePath

    def destroy(self, as_system: bool = False, *args: Any, **kwargs: Any) -> None:
        self.health_left = 0

        self.unload_model()

        UnitManager.get_singleton_instance().remove_unit(self)
        self.get_tile().remove_unit(self)

        if self.owner is not None:
            self.get_owner().units.remove_unit(self)

        self.set_owner(None)
        self.unregister()

        self.actions.clear()
        if hasattr(self, "tag"):
            del self.tag

        if as_system:
            messenger.send("system.unit.destroyed", [self])
        else:
            messenger.send("game.gameplay.unit.destroyed", [self])

    @classmethod
    def get_unit_by_tag(cls, tag: str) -> Optional["Unit"]:
        from managers.entity import EntityManager, EntityType

        entity: Unit | BaseEntity | None = EntityManager.get_singleton_instance().get(EntityType.UNIT, tag)
        if isinstance(entity, Unit):
            return entity
        return None

    def receive_damage(self, damage: float) -> bool:
        if damage < 0:
            raise ValueError("Damage cannot be negative.")

        self.health_left = max(0.0, self.health_left - damage)
        ratio = self.health_left / self.max_health

        # update the shader
        if hasattr(self, "_healthbar_quad"):
            self._healthbar_quad.setShaderInput("health_ratio", ratio)  # type: ignore

        if self.health_left <= 0:
            return True
        return False

    def look(self, radius: int) -> List["Tile"]:
        return TileRepository.get_neighbors(self.get_tile(), radius, False, False)

    def attack(self, target: T_TARGET) -> CombatOutcome:
        outcome = Combat.attack(self, target)
        entry = CombatLog.entry_from_outcome(outcome=outcome, text=CombatLog.outcome_to_text(outcome=outcome))  # type: ignore

        MessengerGlobal.messenger.send("ui.update.ui.combat_log.add", [entry])

        if isinstance(target, Unit) and outcome.attacker_damage > 0.0:
            spawn_damage_text(target, outcome.attacker_damage)

        if outcome.status == CombatResults.ATTACKER_KILLED:
            self.kill()
        elif outcome.status == CombatResults.DEFENDER_KILLED:
            target.kill()

        return outcome

    def get_tag(self) -> str:
        return self.tag
