from typing import Dict, Optional

from exceptions.invalid_pregame_condition import InvalidPregameCondition
from gameplay.player import Player
from managers.base import BaseManager


class PlayerManager(BaseManager):
    _players: Dict[
        int, Player
    ] = {}  # Players are stored in a dictionary with the key being the turn order. recalculated each turn.
    _session_player: Player | None = None
    _nature_player: None = None

    @classmethod
    def reset(cls) -> None:
        cls._players = {}
        cls._session_player = None
        cls._nature_player = None

    @classmethod
    def add(cls, player: Player, is_session: bool = False) -> None:
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

    @classmethod
    def get(cls, turn: int) -> Player:
        return cls._players[turn]

    @classmethod
    def players(cls) -> Dict[int, Player]:
        return cls._players

    @classmethod
    def player(cls) -> Player:
        if cls._session_player is None:
            raise InvalidPregameCondition("No player has been set for this session.")
        return cls._session_player

    @classmethod
    def session_player(cls) -> Player | None:
        return cls._session_player

    @classmethod
    def get_nature(cls) -> Optional[Player]:
        return cls._nature_player

    @classmethod
    def is_session_player(cls, player: Player) -> bool:
        return cls._session_player == player
