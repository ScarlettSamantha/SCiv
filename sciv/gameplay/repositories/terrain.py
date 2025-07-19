from typing import List, Set, Type, cast

from gameplay.tile import BaseTerrain


class TerrainRepository:
    _instances: Set[Type[BaseTerrain]] = set()

    @classmethod
    def register_terrain(cls, terrain: Type[BaseTerrain]) -> None:
        cls._instances.add(terrain)

    @classmethod
    def get_by_key(cls, key: str) -> Type[BaseTerrain] | None:
        for terrain in cls._instances:
            if terrain.get_key() == key:
                return terrain
        return None

    @classmethod
    def get_all(cls) -> Set[Type[BaseTerrain]]:
        return cls._instances

    @classmethod
    def clear(cls) -> None:
        cls._instances.clear()

    @classmethod
    def unregister_terrain(cls, terrain: Type[BaseTerrain]) -> None:
        if terrain in cls._instances:
            cls._instances.remove(terrain)
        else:
            raise ValueError(f"Terrain {terrain.get_key()} not found in repository.")

    @classmethod
    def load(cls, path: str) -> None:
        from system.pyload import PyLoad

        classes: List[Type[BaseTerrain]] = cast(
            List[Type[BaseTerrain]], PyLoad.load_classes(path, base_classes=(BaseTerrain,))
        )
        for terrain in classes:
            cls.register_terrain(terrain)
