from direct.gui.DirectGui import DirectFrame, DirectButton, DirectOptionMenu
from menus._base import BaseMenu


class Second(BaseMenu):
    def __init__(self):
        from managers.game import GameSettings, Game

        BaseMenu.__init__(self)
        self.settings = GameSettings(50, 50, None, None, None)
        game_instance = Game.get_instance()
        game_instance.properties = self.settings

    def show(self):
        from managers.ui import ui

        primary = ui.get_instance().get_main_menu
        game_ui = ui.get_instance().get_game_ui

        # Create the main frame
        self.frame = DirectFrame(
            frameColor=(0.2, 0.5, 0.2, 1),
            frameSize=(-0.7, 0.7, -0.4, 0.4),
            pos=(0, 0, 0),
        )

        # Drop-down for sizes
        self.size_option = DirectOptionMenu(
            parent=self.frame,
            scale=0.05,
            items=["50x50", "100x100", "150x150", "250x250", "350x350", "500x500"],
            initialitem=0,  # Which item is selected by default
            highlightColor=(0.65, 0.65, 0.65, 1),
            pos=(-0.4, 0, 0.2),
            command=self.on_size_selected,
        )

        # Drop-down for empires
        self.empire_option = DirectOptionMenu(
            parent=self.frame,
            scale=0.05,
            items=["Romans", "Egyptians"],
            initialitem=0,
            highlightColor=(0.65, 0.65, 0.65, 1),
            pos=(0.0, 0, 0.2),
            command=self.on_empire_selected,
        )

        # Start button
        self.start_button = DirectButton(
            text="Start",
            scale=0.07,
            command=game_ui,
            pos=(0, 0, 0.1),
            parent=self.frame,
        )

        # Back to Main Menu button
        self.back_button = DirectButton(
            text="Back to Main Menu",
            scale=0.07,
            command=primary,
            pos=(-0.4, 0, -0.3),
            parent=self.frame,
        )

        return self.frame

    def on_size_selected(self, selected_size):
        self.settings.width, self.settings.height = map(int, selected_size.split("x"))
        print("Selected size:", self.settings.width, self.settings.height)

    def on_empire_selected(self, selected_empire):
        self.settings.player = selected_empire
        print("Selected empire:", selected_empire)
        # Handle the empire selection logic here
