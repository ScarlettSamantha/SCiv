from datetime import datetime
from enum import Enum
from typing import Dict, List, TYPE_CHECKING, Optional


from helpers.colors import Colors
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
    OWN_UNIT_ATTACK_DISABLED = t_("ui.player_ui.combat_log.results.own_unit_attack_disabled")


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
        from gameplay.city import City
        from gameplay.tile import Tile

        defender: Optional["Player"] = outcome.defender_player

        if isinstance(outcome.defender_entity, (Tile, City)):
            defender = outcome.defender_entity.get_owner()

        if not outcome.attacker_player or not outcome.defender_player:
            raise ValueError("Both attacker and defender players must be specified in the outcome.")

        if text == "":
            text = cls.outcome_to_text(outcome)

        return cls.entry(outcome.attacker_player, defender if defender else outcome.defender_player, outcome, text)

    @classmethod
    def outcome_to_text(cls, outcome: CombatOutcome) -> str:
        param_list = {
            "defending_unit": str(outcome.defender_entity.name) if outcome.defender_entity else "Unknown Defender",
            "attacking_unit": str(outcome.attacker_entity.name) if outcome.attacker_entity else "Unknown Attacker",
            "damage": f"{outcome.attacker_damage.__round__(2)}" if outcome.attacker_damage > 0 else "",
            "retaliation_damage": f"{outcome.defender_damage.__round__(2)}" if outcome.defender_damage > 0 else "",
            "defender_owner_name": f"[color={Colors.to_hex(outcome.defender_player.get_color())}]{outcome.defender_player.get_name_short()}[/color]"
            if outcome.defender_player
            else "Unknown Defender Owner",
            "attacker_owner_name": f"[color={Colors.to_hex(outcome.attacker_player.get_color())}]{outcome.attacker_player.get_name_short()}[/color]"
            if outcome.attacker_player
            else "Unknown Attacker Owner",
            "defender_owner_color": Colors.to_hex(outcome.defender_player.get_color())
            if outcome.defender_player
            else Colors.to_hex(Colors.WHITE),
            "attacker_owner_color": Colors.to_hex(outcome.attacker_player.get_color())
            if outcome.attacker_player
            else Colors.to_hex(Colors.WHITE),
        }

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
        elif outcome.status == CombatResults.OWN_UNIT_ATTACK_DISABLED:
            return str(CombatResultText.OWN_UNIT_ATTACK_DISABLED.value).format(**param_list)
        else:
            raise ValueError(f"Unknown combat result: {outcome.status}")
