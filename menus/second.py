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
    def __init__(self):
        from managers.game import GameSettings, Game
        from system.generators.basic import Basic

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

        primary_menu = ui.get_instance().get_main_menu
        game_ui = ui.get_instance().get_game_ui

        # Main frame
        self.frame = DirectFrame(
            frameColor=(0.15, 0.15, 0.15, 0.95),  # Dark modern look
            frameSize=(-0.7, 0.7, -0.5, 0.5),
            pos=(0, 0, 0),
        )

        # Labels
        DirectLabel(
            parent=self.frame,
            text="Select Map Size:",
            scale=0.05,
            pos=(-0.4, 0, 0.35),
        )

        DirectLabel(
            parent=self.frame,
            text="Choose Your Empire:",
            scale=0.05,
            pos=(0.0, 0, 0.35),
        )

        DirectLabel(
            parent=self.frame,
            text="Number of Enemies:",
            scale=0.05,
            pos=(-0.4, 0, 0.15),
        )

        DirectLabel(
            parent=self.frame,
            text="Select Difficulty:",
            scale=0.05,
            pos=(0.0, 0, 0.15),
        )

        # Dropdown: Map Size
        self.size_option = DirectOptionMenu(
            parent=self.frame,
            scale=0.05,
            items=["5x5", "50x50", "75x75", "100x100", "125x125", "150x150"],
            initialitem=0,
            highlightColor=(0.8, 0.8, 0.8, 1),
            pos=(-0.4, 0, 0.3),
            command=self.on_size_selected,
        )

        # Dropdown: Empire Selection
        self.empire_option = DirectOptionMenu(
            parent=self.frame,
            scale=0.05,
            items=[str(civ.name) for civ in Civilization.all()],
            initialitem=0,
            highlightColor=(0.8, 0.8, 0.8, 1),
            pos=(0.0, 0, 0.3),
            command=self.on_empire_selected,
        )

        # Dropdown: Enemy Count
        self.enemies_option = DirectOptionMenu(
            parent=self.frame,
            scale=0.05,
            items=[str(x) for x in range(1, 11)],
            initialitem=0,
            highlightColor=(0.8, 0.8, 0.8, 1),
            pos=(-0.4, 0, 0.1),
            command=self.on_enemies_selected,
        )

        # Dropdown: Difficulty Level
        self.difficulty_option = DirectOptionMenu(
            parent=self.frame,
            scale=0.05,
            items=["Easy", "Normal", "Hard", "Insane"],
            initialitem=1,  # Default: Normal
            highlightColor=(0.8, 0.8, 0.8, 1),
            pos=(0.0, 0, 0.1),
            command=self.on_difficulty_selected,
        )

        # Start Game Button
        self.start_button = DirectButton(
            text="▶ Start Game",
            scale=0.07,
            command=game_ui,
            pos=(0.4, 0, -0.4),
            parent=self.frame,
            frameColor=(0.2, 0.7, 0.2, 1),  # Greenish modern button
        )

        # Back to Main Menu Button
        self.back_button = DirectButton(
            text="◀ Back to Menu",
            scale=0.07,
            command=primary_menu,
            pos=(-0.4, 0, -0.4),
            parent=self.frame,
            frameColor=(0.7, 0.2, 0.2, 1),  # Reddish cancel button
        )

        return self.frame

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
