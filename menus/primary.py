from direct.gui.DirectGui import DirectFrame, DirectOptionMenu, DirectButton
from menus._base import BaseMenu


class Primary(BaseMenu):
    
    def __init__(self):
        BaseMenu.__init__(self)
    
    def show(self):
        from managers.ui import ui
        second = ui.get_instance().get_secondary_menu
        
        
        self.frame = DirectFrame(frameColor=(0.2, 0.2, 0.2, 1),
                                 frameSize=(-0.7, 0.7, -0.4, 0.4),
                                 pos=(0, 0, 0))
        
        self.options = ["Option 1", "Option 2", "Option 3", "Option 4"]
        
        self.dropdowns = []
        for i in range(3):
            dropdown = DirectOptionMenu(text="Select",
                                        scale=0.07,
                                        items=self.options,
                                        initialitem=0,
                                        highlightColor=(0.5, 0.5, 0.5, 1),
                                        pos=(-0.3, 0, 0.2 - i * 0.2),
                                        parent=self.frame)
            self.dropdowns.append(dropdown)
        
        self.back_button = DirectButton(text="Exit",
                                        scale=0.07,
                                        command=second,
                                        pos=(-0.4, 0, -0.3),
                                        parent=self.frame)
        
        self.forward_button = DirectButton(text="Configure",
                                           scale=0.07,
                                           command=second,
                                           pos=(0.4, 0, -0.3),
                                           parent=self.frame)
        return self.frame