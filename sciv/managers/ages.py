from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Type, cast

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from helpers.paths import PathsHelper
from mixins.singleton import Singleton
from system.pyload import PyLoad

if TYPE_CHECKING:
    from gameplay.age import Age


class AgesManager(DirectObject, Singleton):
    def __init__(self):
        super(DirectObject, self).__init__()
        Singleton.__init__(self)

    def __setup__(self, *args: Any, **kwargs: Any) -> None:
        self.ages: Dict[int, "Age"] = {}
        self.current_age: "Age | None" = None

    def add_age(self, age: "Age"):
        self.ages[age.order] = age

    def _set_current_age(self, age: "Age" | Type["Age"]):
        from gameplay.age import Age

        if isinstance(age, Age):
            age = type(age)
        for _age in self.ages.values():
            if type(_age) == age:
                self.current_age = age()
                return
        raise ValueError(f"Age with key {type(age)} not found")

    def get_current_age(self) -> "Age":
        assert self.current_age is not None, "Current age is not set"
        return self.current_age

    def _get_all_ages(self) -> List[Type["Age"]]:
        ages: List[Type["Age"]] = cast(
            List[Type["Age"]],
            PyLoad(str(PathsHelper.get_base_path() / "gameplay" / "ages" / "core"), package="gameplay.ages.core")
            .load()
            .values(),
        )
        return ages

    def get_age(self, key: str) -> "Age":
        if not self.ages:
            self.load_ages()
        for age in self.ages.values():
            if age.key == key:
                return age
        raise ValueError(f"Age with key {key} not found")

    def set_age(self, age: "Age"):
        MessengerGlobal.messenger.send("game.era.setting", [age])
        self._set_current_age(age)

    def progress_age(self, new_age: "Age"):
        self._set_current_age(new_age)
        MessengerGlobal.messenger.send("game.era.progressing", [new_age])
        print(f"Age progressed to {new_age.name}")

    def on_turn_end(self, turn: int):
        progressed, new_age = self._age_progression_check()
        if progressed and new_age:
            print(f"Age progressed to {new_age.name} on turn {turn}")
            self.progress_age(new_age)

    def _age_progression_check(self) -> Tuple[bool, "Age | None"]:
        if self.current_age is None:
            return False, None
        next_age_order: int = self.current_age.order + 1
        next_age: "Age | None" = self.ages.get(next_age_order)
        if next_age and self._check_age_unlock_conditions(next_age):
            self.current_age = next_age
            return True, next_age
        return False, None

    def _check_age_unlock_conditions(self, age: "Age") -> bool:
        return age.progression_conditions.are_met()

    def load_ages(self):
        ages: List[Type["Age"]] = self._get_all_ages()
        for age in ages:
            self.add_age(age())

    def begin(self, at_age: "Age | None" = None):
        if not self.ages:
            self.load_ages()

        if self.ages:
            if at_age:
                self._set_current_age(at_age)
            else:
                self.current_age = self.ages[min(self.ages.keys())]

    def dump(self) -> Dict[str, Any]:
        return {
            "current_age": self.current_age.key if self.current_age else None,
        }

    def load(self, data: Dict[str, Any]):
        self.load_ages()
        current_age_key = data.get("current_age")
        if current_age_key and current_age_key in self.ages:
            self.current_age = self.ages[current_age_key]
        else:
            self.current_age = None
