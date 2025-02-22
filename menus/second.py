from direct.gui.DirectGui import (
    DirectFrame,
    DirectButton,
    DirectOptionMenu,
    DirectLabel,
)
from gameplay.civilizations.rome import Rome
from gameplay.repositories import civilization
from gameplay.repositories.civilization import Civilization
from menus._base import BaseMenu


class Second(BaseMenu):
    def __init__(self, base):
        from managers.game import GameSettings, Game
        from system.generators.basic import Basic

        self.base = base
        super().__init__()
        self.settings = GameSettings(
            width=5,
            height=5,
            num_enemies=2,
            generator=Basic,
            player=Rome,
            victory_conditions=None,
            enemies=None,
            difficulty=1,
        )
        game_instance = Game.get_instance()
        game_instance.properties = self.settings

    def show(self):
        from managers.ui import ui

    def all_civilizations(self):
        return ["test", "test2"]

    # Event Handlers
    def on_size_selected(self, selected_size):
        self.settings.width, self.settings.height = map(int, selected_size.split("x"))
        print(f"Selected size: {self.settings.width}x{self.settings.height}")

    def on_empire_selected(self, selected_empire):
        self.settings.player = civilization.Civilization.get(selected_empire)
        print(f"Selected empire: {selected_empire}")

    def on_enemies_selected(self, selected_enemies):
        self.settings.num_enemies = int(selected_enemies)
        print(f"Selected number of enemies: {self.settings.num_enemies}")

    def on_difficulty_selected(self, selected_difficulty):
        self.settings.difficulty = selected_difficulty
        print(f"Selected difficulty: {selected_difficulty}")
