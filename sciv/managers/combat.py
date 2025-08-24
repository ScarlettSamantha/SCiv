import random
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, List, NamedTuple, Union

from gameplay.border import PlayerManager
from gameplay.rules import GameRules
from helpers.cache import Cache

if TYPE_CHECKING:
    from gameplay.cities import City
    from gameplay.improvement import Improvement
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit


T_TARGET = Union["City", "Player", "Improvement", "Unit", "Tile"]
T_TARGET_OPTIONAL = Union["City", "Player", "Improvement", "Unit", "Tile", None]


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
    melee_cost: Any | int = getattr(unit, "attack_points_cost_mele", 1)
    ranged_cost: Any | int = getattr(unit, "attack_points_cost_ranged", 1)
    if callable(melee_cost):
        melee_cost = melee_cost()
    if callable(ranged_cost):
        ranged_cost = ranged_cost()
    get_min = getattr(unit, "get_min_attack_range", lambda: 1)

    return CombatStats(
        melee_attack=unit.get_attack_power_mele(),
        ranged_attack=unit.get_attack_power_ranged(),
        melee_defense=unit.get_defense_mele(),
        ranged_defense=unit.get_defense_ranged(),
        armor_penetration=unit.get_attack_armor_penetration(),
        min_range=get_min(),
        max_range=unit.get_attack_range(),
        melee_cost=melee_cost,
        ranged_cost=ranged_cost,
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
    def attack(cls, attacker: "Unit", defender: T_TARGET, simulation: bool = False) -> CombatOutcome:
        attack_stats: CombatStats = gather_stats(attacker)
        defend_stats: CombatStats = gather_stats(defender)

        # movement
        if getattr(attacker, "has_moved", False):
            return cls._zero(CombatResults.NO_MOVEMENT, attacker.get_owner(), defender.get_owner())

        # range
        dist: int = attacker.get_tile().get_distance(defender.get_tile())
        if dist < attack_stats.min_range or dist > attack_stats.max_range:
            return cls._zero(CombatResults.NO_RANGE, attacker.get_owner(), defender.get_owner())

        # friendly fire (no isinstance with string)
        if attacker.get_owner() == defender.get_owner() and not cls.rules.get_allow_friendly_fire_rule():
            return cls._zero(CombatResults.OWN_UNIT_ATTACK_DISABLED, attacker.get_owner(), defender.get_owner())

        # points
        cost: float = attack_stats.melee_cost if dist == cls.MELE_RANGE else attack_stats.ranged_cost
        if getattr(attacker, "attack_points_left", 0) < cost:
            return cls._zero(CombatResults.NO_POINTS, attacker.get_owner(), defender.get_owner())

        # damage calc (attacker → defender)
        raw_atk: float = cls._roll(attack_stats.melee_attack if dist == cls.MELE_RANGE else attack_stats.ranged_attack)
        defense_val: float = defend_stats.melee_defense if dist == cls.MELE_RANGE else defend_stats.ranged_defense
        net_atk: float = max(0.0, raw_atk - max(defense_val - attack_stats.armor_penetration, 0.0))

        if not simulation:
            defender_killed = defender.receive_damage(net_atk)
        else:
            defender_killed = defender.health() - net_atk <= 0

        attacker_killed = False
        attacker_retaliated = False
        defender_damage = 0.0

        # retaliation only if defender survived and is in range
        if (
            not defender_killed
            and defend_stats.can_retaliate
            and dist >= defend_stats.min_range
            and dist <= defend_stats.max_range
        ):
            raw_ret = cls._roll(defend_stats.melee_attack if dist == cls.MELE_RANGE else defend_stats.ranged_attack)
            atk_def_val = attack_stats.melee_defense if dist == cls.MELE_RANGE else attack_stats.ranged_defense
            defender_damage = max(0.0, raw_ret - max(atk_def_val - defend_stats.armor_penetration, 0.0))
            if not simulation:
                attacker_killed = attacker.receive_damage(defender_damage)
            else:
                attacker_killed = attacker.health() - defender_damage <= 0
            attacker_retaliated = True

        # spend points only in real combat
        if not simulation:
            attacker.attack_points_left -= cost

        # final status
        if defender_killed:
            status = CombatResults.DEFENDER_KILLED
        elif attacker_killed:
            status = CombatResults.ATTACKER_KILLED
        elif attacker_retaliated and defender_damage > 0:
            status = CombatResults.ATTACKER_DAMAGED
        else:
            status = CombatResults.DEFENDER_DAMAGED

        return cls._make_outcome(
            status, net_atk, defender_damage, attacker_killed, defender_killed, attacker_retaliated, attacker, defender
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
