from logging import Logger
from typing import Any, List, Optional, Type

from gameplay.civic import Civic, CivicSubtree, CivicTree
from helpers.cache import Cache
from managers.base import BaseManager


class CivicsManager(BaseManager):
    def __init__(self, *args: Any, **kwargs: Any):
        BaseManager.__init__(self, *args, **kwargs)

        self.logger: Logger = Cache.get_showbase_instance().logger.gameplay.getChild("civics_manager")

        self.civic_points: int = 0

        self.sub_trees: List[CivicSubtree] = []
        self.registered_civics: List[Type[Civic]] = []
        self.civic_tree: Optional[CivicTree] = None

        self.civics_activated: List[Civic] = []

    def process_civics(self):
        if self.civic_tree is None:
            self.logger.warning("No civic tree found. Cannot process civics.")
            return

        for civic in self.civic_tree.get_all_civics():
            if civic not in self.registered_civics:
                self.registered_civics.append(civic)

    def get_tree(self) -> CivicTree | None:
        return self.civic_tree

    def set_tree(self, tree: CivicTree):
        self.civic_tree = tree

    def is_civic_tree_unlocked(self, tree: Type[CivicTree]) -> bool:
        return self.civic_tree is not None and isinstance(self.civic_tree, tree)

    def is_civic_subtree_unlocked(self, civic: Type[CivicSubtree]) -> bool:
        if self.civic_tree is None:
            return False
        return civic in self.civic_tree.get_all_subtrees()

    def activate_civic(self, civic: Type[Civic]):
        if civic not in self.registered_civics:
            self.logger.warning(f"Civic {civic} is not registered. Cannot activate.")
            return

        if any(isinstance(activated_civic, civic) for activated_civic in self.civics_activated):
            self.logger.warning(f"Civic {civic} is already activated.")
            return

        self.civics_activated.append(civic())
        self.logger.info(f"Civic {civic} activated.")

    def is_civic_activated(self, civic: Type[Civic]) -> bool:
        return any(isinstance(activated_civic, civic) for activated_civic in self.civics_activated)
