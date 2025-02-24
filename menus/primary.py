from direct.gui.DirectGui import DirectFrame, DirectOptionMenu, DirectButton
from gameplay.repositories import civilization
from menus._base import BaseMenu


class Primary(BaseMenu):
    def __init__(self, base):
        BaseMenu.__init__(self)
        self.base = base

    def show(self):
        from managers.ui import ui

        second = ui.get_instance().get_secondary_menu

        self.frame = DirectFrame(
            frameColor=(0.2, 0.2, 0.2, 1),
            frameSize=(-0.7, 0.7, -0.4, 0.4),
            pos=(0, 0, 0),
        )

        self.options = ["Option 1", "Option 2", "Option 3", "Option 4"]

        self.dropdowns = []
        for i in range(3):
            dropdown = DirectOptionMenu(
                text="Select",
                scale=0.07,
                items=self.options,
                initialitem=0,
                highlightColor=(0.5, 0.5, 0.5, 1),
                pos=(-0.3, 0, 0.2 - i * 0.2),
                parent=self.frame,
            )
            self.dropdowns.append(dropdown)

        self.back_button = DirectButton(
            text="Exit",
            scale=0.07,
            command=second,
            pos=(-0.4, 0, -0.3),
            parent=self.frame,
        )

        self.forward_button = DirectButton(
            text="Configure",
            scale=0.07,
            command=self.start_game_config,
            pos=(0.4, 0, -0.3),
            parent=self.frame,
        )
        return self.frame

    def all_civilizations(self):
        return [str(civ.name) for civ in civilization.Civilization.all()]

    def start_game_config(self):
        from menus.game_config import CivSelectorApp
        from direct.showbase.MessengerGlobal import messenger
        from managers.ui import ui

        messenger.send("system.game.start", ["100x100", "rome", 5])

        self.hidden = True  # type: ignore
        self.frame.hide()
        self.frame.remove_node()
