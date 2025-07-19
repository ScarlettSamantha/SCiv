import random
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, List, NamedTuple, Union

from gameplay.border import PlayerManager
from gameplay.rules import GameRules
from helpers.cache import Cache

if TYPE_CHECKING:
    from gameplay.cities import City
    from gameplay.improvement import Improvement
    from gameplay.player import Player
    from gameplay.unit import Unit


T_TARGET = Union["City", "Player", "Improvement", "Unit"]
T_TARGET_OPTIONAL = Union["City", "Player", "Improvement", "Unit", None]


class CombatResults(Enum):
    DEFENDER_KILLED = 0  # Target died from the attack
    DEFENDER_DAMAGED = 1  # Target took damage but survived
    ATTACKER_KILLED = 2  # Attacker died from retaliation
    ATTACKER_DAMAGED = 3  # Attacker took retaliatory damage but survived
    INTERRUPTED = 4  # Attack cut short by death (attacker killed)
    NO_RANGE = 5  # Target out of range
    NO_MOVEMENT = 6  # Attacker has moved already
    NO_POINTS = 7  # Not enough attack points
    OWN_UNIT_ATTACK_DISABLED = 8  # Cannot attack own unit (if rules disallow it)


class CombatOutcome(NamedTuple):
    status: CombatResults
    attacker_damage: float
    defender_damage: float
    attacker_killed: bool
    defender_killed: bool
    attacker_retaliated: bool
    attacker_player: "Player | None"
    defender_player: "Player | None"
    attacker_entity: T_TARGET_OPTIONAL
    defender_entity: T_TARGET_OPTIONAL
    attacker_remaining_hp: float
    defender_remaining_hp: float


@dataclass
class CombatStats:
    """
    Holds all numeric parameters affecting combat.
    """

    melee_attack: float
    ranged_attack: float
    melee_defense: float
    ranged_defense: float
    armor_penetration: float
    min_range: int
    max_range: int
    melee_cost: float
    ranged_cost: float
    can_retaliate: bool


def gather_stats(unit: Union["Unit", T_TARGET]) -> CombatStats:
    """
    Pull all relevant combat stats from a unit or target entity.
    """
    return CombatStats(
        melee_attack=unit.get_attack_power_mele(),
        ranged_attack=unit.get_attack_power_ranged(),
        melee_defense=unit.get_defense_mele(),
        ranged_defense=unit.get_defense_ranged(),
        armor_penetration=unit.get_attack_armor_penetration(),
        min_range=getattr(unit, "get_min_attack_range", lambda: 1)(),
        max_range=unit.get_attack_range(),
        melee_cost=getattr(unit, "attack_points_cost_mele", 1),
        ranged_cost=getattr(unit, "attack_points_cost_ranged", 1),
        can_retaliate=getattr(unit, "can_retaliate", False),
    )


class Combat:
    COMBAT_VARIANCE = 0.1  # ±10% random variation
    RNG = random  # injectable RNG for deterministic tests
    MELE_RANGE = 1  # Melee combat range

    rules: GameRules = Cache.get_active_rules()

    @classmethod
    def _zero(cls, status: CombatResults, attacker: "Player", defender: "Player") -> CombatOutcome:
        # No combat occurred or failed checks
        return CombatOutcome(status, 0.0, 0.0, False, False, False, attacker, defender, None, None, 0.0, 0.0)

    @classmethod
    def _roll(cls, base: float) -> float:
        variance = base * cls.COMBAT_VARIANCE
        return base + cls.RNG.uniform(-variance, variance)

    @classmethod
    def _make_outcome(
        cls,
        status: CombatResults,
        attacker_damage: float,
        defender_damage: float,
        attacker_killed: bool,
        defender_killed: bool,
        attacker_retaliated: bool,
        attacker: T_TARGET_OPTIONAL,
        defender: T_TARGET_OPTIONAL,
    ) -> CombatOutcome:
        # Capture owner and remaining HP
        att_player = attacker.get_owner() if attacker else None
        def_player = defender.get_owner() if defender else None
        att_hp = attacker.health() if attacker else 0.0
        def_hp = defender.health() if defender else 0.0
        return CombatOutcome(
            status,
            attacker_damage,
            defender_damage,
            attacker_killed,
            defender_killed,
            attacker_retaliated,
            att_player,
            def_player,
            attacker,
            defender,
            att_hp,
            def_hp,
        )

    @classmethod
    def attack(cls, attacker: "Unit", defender: T_TARGET) -> CombatOutcome:
        # 1. Gather stats
        attack_stats: CombatStats = gather_stats(attacker)
        defend_stats: CombatStats = gather_stats(defender)

        # 2. Movement check
        if getattr(attacker, "has_moved", False):
            return cls._zero(CombatResults.NO_MOVEMENT, attacker.get_owner(), defender.get_owner())

        # 3. Range check
        dist: int = attacker.get_tile().get_distance(defender.get_tile())
        if dist < attack_stats.min_range or dist > attack_stats.max_range:
            return cls._zero(CombatResults.NO_RANGE, attacker.get_owner(), defender.get_owner())

        # 4. Check if rules allow targeting own units and if this is the case.
        if attacker.get_owner() == defender.get_owner() and cls.rules.get_allow_friendly_fire_rule() is False:
            if isinstance(defender, "Unit") and defender.get_owner() == attacker.get_owner():
                return cls._zero(CombatResults.OWN_UNIT_ATTACK_DISABLED, attacker.get_owner(), defender.get_owner())

        # 5. Attack points cost check
        cost: float = attack_stats.melee_cost if dist == cls.MELE_RANGE else attack_stats.ranged_cost
        if getattr(attacker, "attack_points_left", 0) < cost:  # Not enough attack points
            return cls._zero(CombatResults.NO_POINTS, attacker.get_owner(), defender.get_owner())

        # 6. Compute attack damage
        raw_atk: float = cls._roll(attack_stats.melee_attack if dist == cls.MELE_RANGE else attack_stats.ranged_attack)
        defense_val: float = defend_stats.melee_defense if dist == cls.MELE_RANGE else defend_stats.ranged_defense
        net_atk: float = max(0.0, raw_atk - max(defense_val - attack_stats.armor_penetration, 0.0))

        # 7. Apply damage to defender
        defender_killed = defender.receive_damage(net_atk)
        attacker.attack_points_left -= cost
        if defender_killed:
            return cls._make_outcome(
                CombatResults.DEFENDER_KILLED,
                net_atk,
                0.0,
                False,
                True,
                False,
                attacker,
                defender,
            )

        # 8. Retaliation
        if defend_stats.can_retaliate and dist <= defend_stats.max_range:
            raw_ret = cls._roll(defend_stats.melee_attack if dist == 1 else defend_stats.ranged_attack)
            atk_def_val = attack_stats.melee_defense if dist == 1 else attack_stats.ranged_defense
            defender_damage = max(0.0, raw_ret - (atk_def_val - defend_stats.armor_penetration))
            attacker_killed = attacker.receive_damage(defender_damage)
            attacker_retaliated = True
            status = CombatResults.ATTACKER_KILLED if attacker_killed else CombatResults.ATTACKER_DAMAGED
            return cls._make_outcome(
                status,
                net_atk,
                defender_damage,
                attacker_killed,
                False,
                attacker_retaliated,
                attacker,
                defender,
            )

        # 9. Done, attacker damaged the defender and survived
        return cls._make_outcome(
            CombatResults.DEFENDER_DAMAGED,
            net_atk,
            0.0,
            False,
            False,
            False,
            attacker,
            defender,
        )


def test_combat_outcome() -> List[CombatOutcome]:
    player: "Player" = PlayerManager.session_player()
    items: List[CombatOutcome] = [
        CombatOutcome(
            CombatResults.DEFENDER_KILLED, 10.0, 0.0, False, True, False, player, player, None, None, 0.0, 0.0
        ),
        CombatOutcome(CombatResults.NO_RANGE, 0.0, 0.0, False, False, False, player, player, None, None, 0.0, 0.0),
        CombatOutcome(CombatResults.NO_MOVEMENT, 0.0, 0.0, False, False, False, player, player, None, None, 0.0, 0.0),
        CombatOutcome(CombatResults.NO_POINTS, 0.0, 0.0, False, False, False, player, player, None, None, 0.0, 0.0),
        CombatOutcome(CombatResults.ATTACKER_KILLED, 5.0, 8.0, True, False, True, player, player, None, None, 0.0, 0.0),
        CombatOutcome(
            CombatResults.ATTACKER_DAMAGED, 10.0, 3.0, False, False, True, player, player, None, None, 0.0, 0.0
        ),
        CombatOutcome(
            CombatResults.DEFENDER_DAMAGED, 6.0, 0.0, False, False, False, player, player, None, None, 0.0, 0.0
        ),
    ]

    for i in range(10):
        items.append(items[i % len(items)])

    return items
