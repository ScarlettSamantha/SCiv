from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Self, Type

from direct.showbase import MessengerGlobal

from gameplay._units import Units
from gameplay.cities import Cities
from gameplay.citizen import Citizen
from gameplay.citizens import Citizens
from gameplay.civic import CivicSubtree
from gameplay.civilization import Civilization
from gameplay.claims import Claims
from gameplay.government import Government
from gameplay.leader import Leader
from gameplay.mood import Mood
from gameplay.moods import Moods
from gameplay.personality import Personality
from gameplay.player_tiles import PlayerTiles
from gameplay.relationships import Relationships
from gameplay.tech import Tech
from gameplay.trades import Trades
from gameplay.votes import Votes
from gameplay.yields import Yields
from helpers.cache import Cache
from helpers.colors import Colors, Tuple4f
from managers.civics import Civic, CivicsManager, CivicTree
from managers.i18n import T_TranslationOrStrOrNone
from managers.tech import TechManager
from system.effects import Effect, Effects
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.tiles.base_tile import BaseTile
    from gameplay.units.unit_base import UnitBaseClass


class Player(BaseEntity):
    def __init__(
        self,
        name: str,
        turn_order: int,
        personality: Personality,
        civilization: Civilization,
        leader: Leader,
        color: Optional[Tuple4f] = None,
    ) -> None:
        super().__init__()
        from gameplay._units import Units
        from gameplay.resource import Resources

        self.logger = Cache.get_showbase_instance().logger.gameplay.getChild(f"player.{str(turn_order)}")
        self.name: T_TranslationOrStrOrNone = name
        self.id: str | None = None
        self.identifier: str | None = None
        self.color: Tuple4f = color if color else Colors.sequence()

        self.turn_order: int = turn_order

        self.is_human: int = 0
        self.is_being_controlled: int = 0
        self.instance_controller: int = 0

        self.personality: Personality = personality
        self.civilization: Civilization = civilization
        self.leader: Leader = leader

        self.mood: Mood = Mood()
        self.moods: Moods = Moods()
        self.relationships: Relationships = Relationships()

        self.focus = None  # @todo
        self.commitment = 0  # @todo
        self.goal: None = None  # @todo

        self.war_readiness: int = 0  # can be negative and positive.
        self.war_fatigue: int = 0  # can be negative and positive.

        self.size_penalty: float = 0  # 0-3, multiplicative penalty based on the size of the empire.
        self.population_penalty: float = 0  # 0-3, multiplicative penalty based on the population of the empire.
        self.population: int = 0  # total population of the empire.
        self.citizens: Citizens = (
            Citizens()
        )  # keeps track of the citizens in the empire, but citizens are primarily stored in cities.

        # Empire stats
        self.revolt: float = 0.0  # revolt is a percentage of the empire that is in revolt. 0-100
        self.anarchy: float = 0.0  # anarchy is a percentage of the empire that is in anarchy. 0-100
        self.suppression: float = 0.0  # multiplicative bonus on the effectiveness of suppression operations and oppression of revolt and anarchy.
        self.popularity: float = 0.0  # 0-100, percentage of the population that supports the government. This is not loyalty to the government, but support for the empire in general. (not a border mechanic)
        self.taxes: int = 0  # 0-100, percentage of the civilian income that is taxed.

        self.police_effectiveness: float = 0.0  # 0-3 multiplier on the effectiveness of police operations.
        self.counter_intelligence_effectiveness: float = (
            0.0  # 0-3 multiplier on the effectiveness of counter intelligence operations.
        )

        self.world_standing: float = 0.0  # can be negative or positive, 0 is neutral. range is only implied and not defined. but can be assumed to be -100 to 100
        self.delegates: float = 0.0  # absolute number of delegates the player has in the world congress.

        self.government_strength = 0
        self.government: Government = Government()

        self.cities: Cities = Cities()
        self.capital: "City | None" = None  # Capital city of the player, can be None if player has no cities and just a settler or an endgame condition has been met.
        self.tiles: PlayerTiles = PlayerTiles()
        self.claims: Claims = Claims()
        self.units: Units = Units()
        self.votes: Votes = Votes()

        self.trades: Trades = Trades()

        self.resources: Resources = Resources()
        # self.greats: Greats = Greats()

        self.effects: Effects = Effects(self)

        self.science: Yields = Yields(science=0)
        self.culture: Yields = Yields(culture=0)
        self.faith: Yields = Yields(faith=0)
        self.gold: Yields = Yields(gold=0)

        self.tech: TechManager = TechManager()
        self.civics: CivicsManager = CivicsManager()
        self._register_callbacks()

    def register(self) -> None:
        from managers.entity import EntityManager, EntityType

        EntityManager.get_singleton_instance().register(
            entity=self, type=EntityType.PLAYER, key=f"{self.name}-{self.turn_order}"
        )

        if self.is_human:
            self.accept(
                "game.gameplay.research.request_start_research_session_player", self.on_request_start_research_session
            )

    def on_game_load(self) -> None:
        """This will be called when the game is restored from a save file."""
        self.register()
        self.logger = Cache.get_showbase_instance().logger.gameplay.getChild(f"player.{str(self.turn_order)}")
        self.tech.on_game_load()

    def unregister(self) -> None:
        from managers.entity import EntityManager, EntityType

        EntityManager.get_singleton_instance().unregister(entity=self, type=EntityType.PLAYER)

    def _register_callbacks(self) -> None:
        self.citizens.register_callback(event="on_birth", callback=self.on_citizen_birth)

    def on_request_start_research_session(self, tech: Type[Tech], add_to_queue: bool = False) -> None:
        self.logger.debug(f"Player {str(self.name)} requested to start research session for {tech.__name__}")
        instanced_tech: Tech = tech()

        if add_to_queue:
            self.tech.add_tech_to_queue(instanced_tech)
        else:
            self.tech.research_tech(instanced_tech)

        MessengerGlobal.messenger.send("game.gameplay.research.player_starts_research", [self, tech])

    def on_request_cancel_research_session(self) -> None:
        self.logger.debug(f"Player {str(self.name)} requested to cancel research session.")
        self.tech.cancel_research()
        MessengerGlobal.messenger.send("game.gameplay.research.player_cancels_research", [self])

    # @todo make citizens separate thing.
    def on_citizen_birth(self, citizen: Citizen) -> None:
        self.population += 1

    def contribute(self, yield_: Yields) -> None:
        self.science += yield_
        self.culture += yield_
        self.faith += yield_
        self.gold += yield_

        if self.tech.is_researching():
            self.tech.add_science(
                int(yield_.science.value), auto_complete_tech=True
            )  # Contribute to the current research.

    def _recalculate(self) -> None:
        properties: tuple[
            Literal["citizens"],
            Literal["revolt"],
            Literal["anarchy"],
            Literal["suppression"],
            Literal["popularity"],
        ] = ("citizens", "revolt", "anarchy", "suppression", "popularity")
        city_loop_needed: bool = False
        for prop in properties:
            if prop == "citizens":
                city_loop_needed = True
            else:
                pass

        def _city_loop(self: Self) -> None:
            self.citizens.reset()
            for city in self.cities:
                self.citizens.create(num=city.population)

        if city_loop_needed:
            _city_loop(self=self)

    def get_effect(self, key: str) -> Effect | None:
        return self.effects.get_effect(key)

    def get_effects(self) -> Effects:
        return self.effects

    def add_effect(self, effect: Effect) -> None:
        self.effects.add_effect(effect)

    def remove_effect(self, effect: Effect) -> None:
        self.effects.remove_effect(effect)

    def add_unit(self, unit: "UnitBaseClass") -> None:
        self.units.add_unit(unit)

    def remove_unit(self, unit: "UnitBaseClass") -> None:
        self.units.remove_unit(unit)

    def destroy(self):
        """Player is destroyed or wiped out."""
        self.unregister()

    def get_units(self) -> Units:
        return self.units

    def get_all_units(self) -> List["UnitBaseClass"]:
        return self.get_units().all()

    def add_city(self, city: "City") -> None:
        self.cities.add(city)

    def remove_city(self, city: "City") -> None:
        self.cities.remove(city)

    def on_turn_end(self, turn: int):
        self.effects.on_turn_end(turn)

    def has_researched_tech(self, tech: Type[Tech]) -> bool:
        return self.tech.is_tech_researched(tech)

    def get_all_cities(self) -> Cities:
        return self.cities

    def get_all_tiles(self) -> Dict[tuple[int, int], "BaseTile"]:
        return self.tiles.get_tiles()

    def owns_tile(self, x: int, y: int) -> bool:
        return self.tiles.get_tiles().get((x, y), None) is not None

    def has_civic_tree_unlocked(self, civic_tree: Type[CivicTree]) -> bool:
        return self.civics.is_civic_tree_unlocked(civic_tree)

    def has_civic_subtree_unlocked(self, sub_tree: Type[CivicSubtree]) -> bool:
        return self.civics.is_civic_subtree_unlocked(sub_tree)

    def has_civic(self, civic: Type["Civic"]) -> bool:
        return self.civics.is_civic_activated(civic)

    def get_civic_tree(self) -> CivicTree | None:
        return self.civics.get_tree()
