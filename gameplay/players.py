from gameplay.player import Player
from typing import Type, Dict


class Players:
    def __init__(self):
        self._data: Dict[int, Player] = {}

    def addPlayer(self, player: Player):
        self._data[player.turn_order] = player
        self.reorderTurnOrder()

    def removePlayer(self, player: Player):
        del self._data[player.turn_order]
        self.reorderTurnOrder()

    def __getitem__(self, _, key):
        return self._data[key]

    def __delitem__(self, _, key: Type[int | Player]):
        if isinstance(key, int):
            self.removePlayer(self._data[key])
        elif isinstance(key, Player):
            self.removePlayer(key)

    def reorderTurnOrder(self):
        sorted_items = sorted(self._data.items(), key=lambda item: item[1].turn_order)
        self._data = dict(sorted_items)
