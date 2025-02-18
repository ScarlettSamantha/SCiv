from typing import Optional, TYPE_CHECKING

from data.tiles.tile import Tile
from menus.game import Game
from mixins.singleton import Singleton

if TYPE_CHECKING:
    from managers.world import World
    
class ui(Singleton):
    
    current_menu = None
    base = None
    
    def __init__(self, showbase):
        self.showbase = showbase

        self.menus = []
        
        self.current_tile: Optional[Tile] = None
        self.previous_tile: Optional[Tile] = None
        
    def __setup__(self):
        if self.base is None:
            raise ValueError("Empty base")
        self.base.accept("tile-clicked", self.process_game_click)
        self.current_menu = None
        self.game: Optional[Game] = None
        self.map: Optional[World] = None
        self.current_tile: Optional[Tile] = None
        self.previous_tile: Optional[Tile] = None
    
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
        self.game = Game()
        self.set_current_menu(self.game.show())
        
    def select_tile(self, tile: Tile):
        self.previous_tile = self.current_tile
        self.current_tile = tile
        
        if self.previous_tile is not None:
            self.previous_tile.node.setColor(1, 1, 1, 1)
        self.current_tile.node.setColor(1, 1, 0, 1)
        
    def process_game_click(self, tile_id):
        if self.map is None or self.game is None:
            raise ValueError("Initialisation issue")
        self.game.update_label_text(tile_id)
        tile = self.map.map[tile_id]
        self.select_tile(tile)