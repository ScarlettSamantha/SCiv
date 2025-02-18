from direct.gui.DirectGui import DirectFrame, DirectButton
from menus._base import BaseMenu
    
class Second(BaseMenu):
    
    def __init__(self):
        BaseMenu.__init__(self)
    
    def show(self):
        from managers.ui import ui
        primary = ui.get_instance().get_main_menu
        game_ui = ui.get_instance().get_game_ui
        
        self.frame = DirectFrame(frameColor=(0.2, 0.5, 0.2, 1),
                                    frameSize=(-0.7, 0.7, -0.4, 0.4),
                                    pos=(0, 0, 0))
        
        self.label = DirectButton(text="Start",
                                    scale=0.07,
                                    command=game_ui,
                                    pos=(0, 0, 0.1),
                                    parent=self.frame)
        
        self.back_button = DirectButton(text="Back to Main Menu",
                                        scale=0.07,
                                        command=primary,
                                        pos=(-0.4, 0, -0.3),
                                        parent=self.frame)
        return self.frame