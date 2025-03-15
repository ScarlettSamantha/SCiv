# Rules

## SCiv (Default)

The rules system is just a housing for generic values and should be classmethods, this way we dont have to deal with instancing and passing around the correct instance. And as the values should be fixed or at worse at some point configurable at game start.

### Actions

#### Founding cities

used in `gameplay/actions/unit/found.py` [link](/gameplay/actions/unit/found.py)

- `city_founding_distance` | default: `2` tiles radius outward
- `city_founding_in_own_territory` | default: `true` allowed, If you are allowed to build a city on tiles you already own, or must build on on-owned tiles

#### Building Improvements

- `unit_looses_movement_after_building` | default: `true` [link](/gameplay/actions/unit/build.py) If the units MP will be set to 0 after building

#### Possible Future rules

- Allowing player to retain a certain percentage of resources spend on production of unit/improvement if canceled or replaced with a other improvement. This has some gameplay implications.
