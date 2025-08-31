from typing import TYPE_CHECKING, Any, Dict, Self, Type, cast

if TYPE_CHECKING:
    from gameplay.age import Age
from sciv.mixins.singleton import Singleton


class Property:
    def __init__(self, name: str, value: Any):
        self.name: str = name
        self.value: Any = value

    def dump(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        return cls(name=data["name"], value=data["value"])


class PropertiesManager(Singleton):
    def __init__(self):
        self.properties: Dict[str, Property] = {}

    def __setup__(self, *args: Any, **kwargs: Any) -> None:
        self.properties: Dict[str, Property] = {}

    def add_property(self, key: str, value: Any) -> None:
        self.properties[key] = value

    def get_property(self, key: str) -> Property:
        if (result := self.properties.get(key)) is not None:
            return result
        raise ValueError(f"Property with key {key} not found")

    def dump(self) -> Dict[str, Any]:
        return {key: prop.dump() for key, prop in self.properties.items()}

    def load(self, data: Dict[str, Any]) -> None:
        from managers.entity import EntityManager

        _cls: Type["Age"] = cast(
            Type["Age"],
            EntityManager.dynamic_import(data.get("game.current_age").value["cls_ref"]),  # type: ignore
        )

        self.properties = {key: _cls.from_dict(data=prop_data) for key, prop_data in data.items()}  # type: ignore
