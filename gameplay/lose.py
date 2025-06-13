from enum import Enum
from typing import TYPE_CHECKING, Literal, Optional

from direct.showbase import MessengerGlobal

from managers.player import PlayerManager

if TYPE_CHECKING:
    from gameplay.player import Player


class LoseConditions(Enum):
    ELIMINATED = "eliminated"


class Lose:
    @classmethod
    def check_if_player_eliminated(cls, player: "Player") -> LoseConditions | Literal[False] | Literal[True]:
        lose: Optional[LoseConditions] = None
        if player.cities.count() == 0 and player.units.count() == 0:
            lose = LoseConditions.ELIMINATED

        if lose is not None:
            player.lose(LoseConditions.ELIMINATED)
            if player.is_human:
                MessengerGlobal.messenger.send("system.game.player_game_over", [player, lose])
                return True
            else:
                MessengerGlobal.messenger.send("system.game.opponent_game_over", [player, lose])
            return lose
        return False

    @classmethod
    def check_if_game_over(cls) -> bool:
        for player in PlayerManager.all().values():
            if player.is_defeated is True:
                continue

            if cls.check_if_player_eliminated(player) is True:
                return True  # only triggers if a human player is eliminated
        return False  # No human player has been eliminated, so the game is not over yet
