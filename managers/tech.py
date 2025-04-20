from collections import OrderedDict
from typing import Any, List, Optional, Type

from direct.showbase import MessengerGlobal

from gameplay.tech import Tech, TechTree
from helpers.cache import Cache
from managers.base import BaseManager
from system.pyload import PyLoad


class TechManager(BaseManager):
    def __init__(self, technology_folders: List[str] = [], *args: Any, **kwargs: Any):
        BaseManager.__init__(self, *args, **kwargs)

        self.logger = Cache.get_showbase_instance().logger.gameplay.getChild("tech_manager")
        self.researching: Tech | None = None
        self.queue: OrderedDict[int, Tech] = OrderedDict()
        self.registered_techs: List[Type[Tech]] = []
        self.researched_techs: List[Tech] = []

        self._needed_science: int = 1
        self._current_science_pool: int = 0
        self._tech_tree: Optional[TechTree] = None

        self.process_folders(technology_folders)

    @property
    def needed_science(self) -> int:
        return self._needed_science

    @needed_science.setter
    def needed_science(self, value: int):
        self._needed_science = value

    @property
    def current_science(self) -> int:
        return self._current_science_pool

    @current_science.setter
    def current_science(self, value: int):
        self._current_science_pool = value

    def on_game_load(self):
        self.logger = Cache.get_showbase_instance().logger.gameplay.getChild("tech_manager")

    def process_folders(self, folders: List[str]):
        def process_folder(folder: str):
            classes = PyLoad.load_classes(folder)
            for _class in classes:
                if not isinstance(_class, Tech):
                    continue
                self.add_tech(_class)

        for folder in folders:
            process_folder(folder)

    def add_tech_to_queue(self, tech: Tech) -> None:
        self.logger.debug(f"Adding tech to queue: {tech}")
        MessengerGlobal.messenger.send("game.gameplay.research.player_queue_added_research", [tech])
        self.queue[len(self.queue)] = tech

    def reorder(self) -> None:
        self.queue = OrderedDict((i, tech) for i, tech in enumerate(self.queue.values()))

    def do_first_queue(self, tech: Tech) -> None:
        self.queue = OrderedDict([(0, tech)] + [(i + 1, t) for i, t in enumerate(self.queue.values())])

    def delete_tech(self, tech: Tech | Type[Tech]) -> None:
        if isinstance(tech, Tech):
            tech = type(tech)
        self.registered_techs.remove(tech)

    def add_tech(self, tech: Tech | Type[Tech]) -> None:
        if isinstance(tech, Tech):
            tech = type(tech)
        self.registered_techs.append(tech)

    def current_tech(self) -> Tech | None:
        return self.researching

    def next_tech(self) -> Tech | None:
        return self.researching

    def is_tech_researched(self, tech: Tech | Type[Tech]) -> bool:
        if isinstance(tech, type):
            for t in self.researched_techs:
                type_class = type(t)
                if type_class.key == tech.key:
                    return True
        else:
            for t in self.researched_techs:
                if isinstance(t, type(tech)):
                    return True
        return False

    def are_tech_requirements_met(self, tech: Tech | Type[Tech]) -> bool:
        if isinstance(tech, Tech):
            tech = type(tech)

        requirements: List[Type[Tech]] = tech.requires
        for req in requirements:
            if not self.is_tech_researched(req):
                return False
        return True

    def cancel_research(self) -> None:
        if not self.researching:
            return
        self._current_science_pool = 0
        self._needed_science = 1
        self.logger.debug(f"Cancelling research {str(self.researching.name)}")
        self.researching = None

    def is_researching(self) -> bool:
        return self.researching is not None

    def process_queue(self, complete_research: bool = True) -> None:
        if self.researching and complete_research:
            self.researched_techs.append(self.researching)
            self.researching = None

        if len(self.queue) != 0:
            tech: Tech = self.queue.pop(0)
            self.researching = tech
            self.reorder()

    def complete_research(self, auto_complete_tech: bool = True) -> None:
        if self.researching is None:
            return

        self.logger.debug(f"Completing research {str(self.researching.name)}")
        self._current_science_pool -= self._needed_science
        self.process_queue()
        MessengerGlobal.messenger.send("game.gameplay.research.player_completed_research", [self.researching])
        # We check if we can still complete more for example if the player gets a large amount of science it could complete 1 or more techs.
        if auto_complete_tech and self._current_science_pool >= self._needed_science:
            self.complete_research()

    def currently_researching(self) -> Tech | None:
        return self.researching

    def research_tech(self, tech: Tech) -> None:
        self.logger.debug(f"Researching tech: {tech}")
        if tech.__class__ in self.registered_techs:
            self.researching = tech
            self._needed_science = tech.tech_points_required
            self._current_science_pool = 0

    def add_science(self, science: int, auto_complete_tech: bool = True) -> None:
        self.logger.debug(f"Adding science: {science} to {self._current_science_pool}")
        self._current_science_pool += science

        while auto_complete_tech and self._current_science_pool >= self._needed_science and self.is_researching():
            self.complete_research(auto_complete_tech=auto_complete_tech)

    def remove_science(self, science: int):
        self.logger.debug(f"Removing science: {science} from {self._current_science_pool}")
        self._current_science_pool -= science
        if self._current_science_pool < 0:
            self._current_science_pool = 0

    def set_tech_tree(self, tech_tree: TechTree, auto_register_techs: bool = True):
        self.logger.debug(f"Setting tech tree: {tech_tree}")
        self._tech_tree = tech_tree
        if auto_register_techs:
            for tech in self._tech_tree.items():
                if tech in self.registered_techs:
                    continue
                self.registered_techs.append(tech)

    def get_tree(self) -> TechTree | None:
        return self._tech_tree
