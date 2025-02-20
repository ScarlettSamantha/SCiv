from direct.showbase.ShowBase import ShowBase


class BaseMenu(ShowBase):
    def __init__(self):
        from managers.ui import ui
        from managers.world import World

        self.frame = None
        self.ui = ui.get_instance()
        self.world = World.get_instance()
