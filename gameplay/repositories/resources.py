from pathlib import Path
from typing import Dict, List, Optional, Type, Union
from gameplay.resource import BaseResource, ResourceType
from system.pyload import PyLoad

folder_mapping: Dict[ResourceType, str] = {
    ResourceType.BASIC: "basic",
    ResourceType.BONUS: "bonus",
    ResourceType.LUXURY: "luxury",
    ResourceType.MECHANIC: "mechanics",
    ResourceType.STRATEGIC: "strategic",
}


class ResourceRepository:
    # This is flattened cache of all resources classes
    __cached_resources_classes: List[Type[BaseResource]] = []
    __cached_resources_by_type: Dict[ResourceType, List[Type[BaseResource]]] = {}

    @classmethod
    def load_into_cache(cls):
        for resource_type, folder in folder_mapping.items():
            resource_classes: Dict[str, Type[BaseResource]] = PyLoad.load_classes(
                str(Path(__file__).parent.parent / "resources" / "core" / folder), base_classes=BaseResource
            )
            cls.__cached_resources_classes.extend(resource_classes.values())

            if resource_type not in cls.__cached_resources_by_type:
                cls.__cached_resources_by_type[resource_type] = []

            cls.__cached_resources_by_type[resource_type].extend(resource_classes.values())

    @classmethod
    def all(cls, types: Optional[List[ResourceType]] = None) -> List[Type[BaseResource]]:
        if not cls.__cached_resources_classes:
            cls.load_into_cache()

        if types is not None:
            return [resource_class for resource_class in cls.__cached_resources_classes if resource_class.type in types]  # type: ignore
        return cls.__cached_resources_classes

    @classmethod
    def all_by_type(cls, resource_type: Union[ResourceType, List[ResourceType]]) -> List[Type[BaseResource]]:
        if not cls.__cached_resources_classes:
            cls.load_into_cache()

        if isinstance(resource_type, list):
            resources = []
            for r_type in resource_type:
                resources.extend(cls.__cached_resources_by_type.get(r_type, []))
            return resources

        return cls.__cached_resources_by_type.get(resource_type, [])
