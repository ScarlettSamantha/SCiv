from datetime import datetime
from enum import Enum
from typing import Dict, List, TYPE_CHECKING

from managers.combat import CombatOutcome, CombatResults
from managers.i18n import T_TranslationOrStr, t_
from collections import OrderedDict

if TYPE_CHECKING:
    from gameplay.player import Player


class CombatResultText(Enum):
    DEFENDER_KILLED = t_("ui.player_ui.combat_log.results.defender_killed")
    DEFENDER_DAMAGED = t_("ui.player_ui.combat_log.results.defender_damaged")
    ATTACKER_KILLED = t_("ui.player_ui.combat_log.results.attacker_killed")
    ATTACKER_DAMAGED = t_("ui.player_ui.combat_log.results.attacker_damaged")
    INTERRUPTED = t_("ui.player_ui.combat_log.results.interrupted")
    NO_RANGE = t_("ui.player_ui.combat_log.results.no_range")
    NO_MOVEMENT = t_("ui.player_ui.combat_log.results.no_movement")
    NO_POINTS = t_("ui.player_ui.combat_log.results.no_points")


class CombatLogEntry:
    def __init__(self, attacker: "Player", defender: "Player", outcome: CombatOutcome, text: T_TranslationOrStr = ""):
        self.attacker = attacker
        self.defender = defender
        self.outcome = outcome
        self.text = CombatLog.outcome_to_text(outcome)
        self.timestamp = datetime.now()


class CombatLog:
    log: Dict["Player", List[CombatLogEntry]] = OrderedDict()

    @classmethod
    def add_entry(cls, entry: CombatLogEntry, both_sides: bool = True) -> None:
        cls._store_entry(entry, both_sides=both_sides)

    @classmethod
    def _store_entry(cls, entry: CombatLogEntry, both_sides: bool = True) -> None:
        attacker = entry.attacker
        defender = entry.defender

        cls.log.setdefault(attacker, []).append(entry)
        if both_sides:
            cls.log.setdefault(defender, []).append(entry)

    @classmethod
    def get_entries(cls, player: "Player") -> List[CombatLogEntry]:
        return cls.log.get(player, [])

    @classmethod
    def clear_entries(cls, player: "Player"):
        if player in cls.log:
            del cls.log[player]
        else:
            raise ValueError(f"No entries found for player {player.name}")

    @classmethod
    def get_all_entries(cls) -> List[CombatLogEntry]:
        all_entries: List[CombatLogEntry] = []
        for entries in cls.log.values():
            all_entries.extend(entries)
        return all_entries

    @classmethod
    def entry(
        cls, attacker: "Player", defender: "Player", outcome: CombatOutcome, text: T_TranslationOrStr = ""
    ) -> CombatLogEntry:
        return CombatLogEntry(attacker, defender, outcome, text)

    @classmethod
    def entry_from_outcome(cls, outcome: CombatOutcome, text: T_TranslationOrStr = "") -> CombatLogEntry:
        if not outcome.attacker_player or not outcome.defender_player:
            raise ValueError("Both attacker and defender players must be specified in the outcome.")
        if text == "":
            text = cls.outcome_to_text(outcome)
        return cls.entry(outcome.attacker_player, outcome.defender_player, outcome, text)

    @classmethod
    def outcome_to_text(cls, outcome: CombatOutcome) -> str:
        """
        Convert combat outcome to a human-readable string.
        """
        defender_name = str(outcome.defender_entity.name) if outcome.defender_entity else "Unknown"
        attacker_name = str(outcome.attacker_entity.name) if outcome.attacker_entity else "Unknown"
        damage_text = f"{outcome.defender_damage}" if outcome.defender_damage > 0 else ""

        param_list = {"defending_unit": defender_name, "attacking_unit": attacker_name, "damage": damage_text}

        if outcome.status == CombatResults.DEFENDER_KILLED:
            return str(CombatResultText.DEFENDER_KILLED.value).format(**param_list)
        elif outcome.status == CombatResults.DEFENDER_DAMAGED:
            return str(CombatResultText.DEFENDER_DAMAGED.value).format(**param_list)
        elif outcome.status == CombatResults.ATTACKER_KILLED:
            return str(CombatResultText.ATTACKER_KILLED.value).format(**param_list)
        elif outcome.status == CombatResults.ATTACKER_DAMAGED:
            return str(CombatResultText.ATTACKER_DAMAGED.value).format(**param_list)
        elif outcome.status == CombatResults.INTERRUPTED:
            return str(CombatResultText.INTERRUPTED.value).format(**param_list)
        elif outcome.status == CombatResults.NO_RANGE:
            return str(CombatResultText.NO_RANGE.value).format(**param_list)
        elif outcome.status == CombatResults.NO_MOVEMENT:
            return str(CombatResultText.NO_MOVEMENT.value).format(**param_list)
        elif outcome.status == CombatResults.NO_POINTS:
            return str(CombatResultText.NO_POINTS.value).format(**param_list)
        else:
            raise ValueError(f"Unknown combat result: {outcome.status}")
