from collections import OrderedDict
from typing import Any, List, Optional

from gameplay.tech import Tech, TechTree
from managers.base import BaseManager
from system.pyload import PyLoad


class TechManager(BaseManager):
    def __init__(self, technology_folders: List[str] = [], *args: Any, **kwargs: Any):
        BaseManager.__init__(self, *args, **kwargs)

        self.researching: Tech | None = None
        self.queue: OrderedDict[int, Tech] = OrderedDict()
        self.registered_techs: List[Tech] = []
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
        self.queue[len(self.queue)] = tech

    def reorder(self) -> None:
        self.queue = OrderedDict((i, tech) for i, tech in enumerate(self.queue.values()))

    def do_first_queue(self, tech: Tech) -> None:
        self.queue = OrderedDict([(0, tech)] + [(i + 1, t) for i, t in enumerate(self.queue.values())])

    def delete_tech(self, tech: Tech) -> None:
        self.registered_techs.remove(tech)

    def add_tech(self, tech: Tech) -> None:
        self.registered_techs.append(tech)

    def current_tech(self) -> Tech | None:
        return self.researching

    def next_tech(self) -> Tech | None:
        return self.researching

    def cancel_research(self) -> None:
        if self.researching:
            self._current_science_pool = 0
            self._needed_science = 1
            self.researching = None

    def process_queue(self, complete_research: bool = True) -> None:
        if self.queue:
            if self.researching and complete_research:
                self.researched_techs.append(self.researching)
                self.researching = None
            tech: Tech = self.queue.pop(0)
            self.researching = tech
            self.reorder()

    def complete_research(self, auto_complete_tech: bool = True) -> None:
        self._current_science_pool -= self._needed_science
        self.process_queue()

        # We check if we can still complete more for example if the player gets a large amount of science it could complete 1 or more techs.
        if auto_complete_tech and self._current_science_pool >= self._needed_science:
            self.complete_research()

    def currently_researching(self) -> Tech | None:
        return self.researching

    def research_tech(self, tech: Tech) -> None:
        if tech in self.registered_techs:
            self.researching = tech
            self._needed_science = tech.tech_points_required
            self._current_science_pool = 0

    def add_science(self, science: int, auto_complete_tech: bool = True) -> None:
        self._current_science_pool += science

        while auto_complete_tech and self._current_science_pool >= self._needed_science and self.queue:
            self.complete_research(auto_complete_tech=auto_complete_tech)

    def remove_science(self, science: int):
        self._current_science_pool -= science
        if self._current_science_pool < 0:
            self._current_science_pool = 0

    def set_tech_tree(self, tech_tree: TechTree):
        self._tech_tree = tech_tree

    def get_tree(self) -> TechTree:
        return self._tech_tree
