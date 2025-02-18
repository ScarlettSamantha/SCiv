from direct.gui.DirectGui import DirectFrame
from menus._base import BaseMenu
    
class Game(BaseMenu):
    
    def __init__(self):
        BaseMenu.__init__(self)
    
    def show(self):
        from managers.ui import ui
        ui.get_instance().get_main_menu
        
        self.frame = DirectFrame(frameColor=(0.2, 0.2, 0.2, 1),
                                 frameSize=(-0.1, 0.5, -0.2, 0.4), # 2 = width,3 = height
                                 pos=(1.2, 0, 0.55))
        

        return self.frame