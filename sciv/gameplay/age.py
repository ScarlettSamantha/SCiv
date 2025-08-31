from typing import Any, Dict, Tuple, Type

from gameplay.condition import Conditions
from gameplay.effect import Effect
from helpers.placeholder import Placeholder
from managers.i18n import T_TranslationOrStrOrNone
from managers.world import World


class Age:
    key: T_TranslationOrStrOrNone
    name: T_TranslationOrStrOrNone
    description: T_TranslationOrStrOrNone
    color: Tuple[int, int, int, int] | None
    order: int = -1
    icon: str = Placeholder.getPlaceholderImagePathSmallIcon()
    transition_image: str = Placeholder.getPlaceholderImagePathSmallIcon()

    in_age: bool = False

    progression_conditions: Conditions = Conditions()
    during_effects: Dict[Type[Effect], Dict[str, Any]] = {}
    enter_effects: Dict[Type[Effect], Dict[str, Any]] = {}
    leave_effects: Dict[Type[Effect], Dict[str, Any]] = {}

    @classmethod
    def can_progress(cls) -> bool:
        return cls.progression_conditions.are_met()

    def __init__(self, *args: Any, **kwargs: Any):
        self.in_age = True

        self.during_effects_instances: Dict[Type[Effect], Effect] = {}
        self.enter_effects_instances: Dict[Type[Effect], Effect] = {}
        self.leave_effects_instances: Dict[Type[Effect], Effect] = {}

    def on_enter(self) -> None:
        self.apply_enter_effects()
        self.in_age = True

    def on_leave(self) -> None:
        self.apply_leave_effects()
        self.in_age = False
        self.remove_during_effects()

    def apply_enter_effects(self) -> None:
        for _effect in self.enter_effects:
            args: Dict[str, Any] = self.enter_effects[_effect]
            args.setdefault("player", None)
            effect = _effect(**args)
            Effect.apply_to_entity(
                base_object=World.get_singleton_instance(), effect=effect, execute_on_apply=True, player=effect.player
            )
            self.enter_effects_instances[_effect] = effect

        for _effect in self.during_effects:
            args: Dict[str, Any] = self.during_effects[_effect]
            args.setdefault("player", None)
            effect = _effect(**args)
            Effect.apply_to_entity(
                base_object=World.get_singleton_instance(), effect=effect, execute_on_apply=True, player=effect.player
            )
            self.during_effects_instances[_effect] = effect

    def apply_leave_effects(self) -> None:
        for _effect in self.leave_effects:
            args: Dict[str, Any] = self.leave_effects[_effect]
            args.setdefault("player", None)
            effect = _effect(**args)
            Effect.apply_to_entity(
                base_object=World.get_singleton_instance(), effect=effect, execute_on_apply=True, player=effect.player
            )
            self.leave_effects_instances[_effect] = effect

    def remove_during_effects(self) -> None:
        for effect in list(self.during_effects_instances.values()):
            Effect.remove_effect_from_entity(
                base_object=World.get_singleton_instance(), effect=effect, execute_on_remove=True
            )

    def get_transition_image(self) -> str:
        return self.transition_image

    def get_name(self) -> T_TranslationOrStrOrNone:
        return self.name

    def dump(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "order": self.order,
            "icon": self.icon,
            "transition_image": self.transition_image,
            "cls_ref": f"{self.__class__.__module__}.{self.__class__.__name__}",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Age":
        instance = cls()
        return instance
