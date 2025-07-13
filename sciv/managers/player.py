from typing import TYPE_CHECKING, Dict, Optional

from exceptions.invalid_pregame_condition import InvalidPregameCondition
from managers.base import BaseManager

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.player import Player


class PlayerManager(BaseManager):
    _players: Dict[
        int, "Player"
    ] = {}  # Players are stored in a dictionary with the key being the turn order. recalculated each turn.
    _session_player: "Player | None" = None
    _nature_player: "Player | None" = None
    _barbarian_player: "Player | None" = None

    @classmethod
    def load(cls, data: Dict[str, "Player"]) -> None:
        cls._players = {}
        for (
            _,
            player,
        ) in data.items():  # We need to find the player that is human and assign them to the session player.
            if player.is_human:
                cls._session_player = player
            if player.is_nature:
                player.on_game_load()
                cls._nature_player = player
                continue
            if player.is_barbarian:
                player.on_game_load()
                cls._barbarian_player = player
                continue
            cls._players[player.turn_order] = player
            player.on_game_load()

    @classmethod
    def reset(cls) -> None:
        cls._players = {}
        cls._session_player = None
        cls._nature_player = None

    @classmethod
    def add(cls, player: "Player", is_session: bool = False) -> None:
        if cls.turn_exists(player.turn_order):
            raise InvalidPregameCondition(f"Player with turn order {player.turn_order} already exists.")
        cls._players[player.turn_order] = player
        if is_session:
            cls._session_player = player

    @classmethod
    def turn_exists(cls, turn: int) -> bool:
        for _, obj in cls._players.items():
            if obj.turn_order == turn:
                return True
        return False

    def on_game_start(self):
        self.get_nature().on_game_start()

        for _, player in self._players.items():
            player.on_game_start()

    @classmethod
    def get(cls, turn: int) -> "Player":
        return cls._players[turn]

    @classmethod
    def get_by_tag(cls, tag: str) -> "Player | None":
        for player in cls._players.values():
            if player.tag == tag:
                return player
        return None

    @classmethod
    def all(cls, add_mechanic_players: bool = False) -> Dict[int, "Player"]:
        players = cls._players.copy()
        if add_mechanic_players:
            if cls._session_player is not None:
                players[cls._session_player.turn_order] = cls._session_player
            if cls._nature_player is not None:
                players[cls._nature_player.turn_order] = cls._nature_player
            if cls._barbarian_player is not None:
                players[cls._barbarian_player.turn_order] = cls._barbarian_player
        return players

    @classmethod
    def players(cls) -> Dict[int, "Player"]:
        return cls._players

    @classmethod
    def player(cls) -> "Player":
        if cls._session_player is None:
            raise InvalidPregameCondition("No player has been set for this session.")
        return cls._session_player

    @classmethod
    def session_player(cls) -> "Player":
        if cls._session_player is None:
            raise InvalidPregameCondition("No player has been set for this")

        return cls._session_player

    @classmethod
    def get_nature(cls) -> "Player":
        if cls._nature_player is None:
            raise InvalidPregameCondition("No nature player has been set.")
        return cls._nature_player

    @classmethod
    def set_nature(cls, player: "Player") -> None:
        cls._nature_player = player

    @classmethod
    def get_barbarian(cls) -> "Player":
        if cls._barbarian_player is None:
            raise InvalidPregameCondition("No barbarian player has been set.")
        return cls._barbarian_player

    @classmethod
    def set_barbarian(cls, player: "Player") -> None:
        cls._barbarian_player = player

    @classmethod
    def is_session_player(cls, player: "Player") -> bool:
        return cls._session_player == player

    @classmethod
    def if_has_capital(cls, player: Optional["Player"] = None) -> bool:
        if player is None:
            player = cls.player()
        return len(player.cities) > 0

    @classmethod
    def get_capital(cls, player: Optional["Player"] = None) -> "City | None":
        if player is None:
            player = cls.player()
        for city in player.cities:
            if city.is_capital:
                return city
        return None
