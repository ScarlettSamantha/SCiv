from mixins.singleton import Singleton

class ui(Singleton):
    
    current_menu = None
    base = None
    
    def __init__(self, showbase):
        self.showbase = showbase
        self.menus = []
        
    def __setup__(self, base):
        self.base = base
    
    def cleanup_menu(self):
        if self.current_menu:
            self.current_menu.destroy()
            
    def set_current_menu(self, menu):
        self.current_menu = menu
        
    def get_current_menu(self):
        return self.current_menu

    def get_main_menu(self):
        from menus.primary import Primary
        self.cleanup_menu()  
        self.set_current_menu(Primary().show())
        
    def get_secondary_menu(self):
        from menus.second import Second
        self.cleanup_menu()
        self.set_current_menu(Second().show())
        
    def get_game_ui(self):
        from menus.game import Game
        self.cleanup_menu()
        self.set_current_menu(Game().show())