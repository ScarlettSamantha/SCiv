# Workings

## Players

...

## State  

The main state of non-entity objects (e.g., managers and mechanic-focused implementations) can be stored in the state manager, ensuring persistence between saves.  

The state manager has two internal object types:  

- Flags: Limited to strings, integers, floats, and booleans. These are designed for frequent changes, with minimal checks for faster processing.  
- Internal State: Can store more complex objects, but not lambdas due to pickle limitations.  

The system primarily functions as a data store with utility functions to simplify state management.

## Effects

> Source: [system/effects.py](./system/effects.py)  
> Implementations: [gameplay/effects/*](./gameplay/effects)

Effects are stateful entities that represent game mechanics, such as a farm increasing the food yield of adjacent grassland tiles by +1.  

They support several default placement methods:

- Empire: Applies the effect across the entire empire of the affected player. Can also target other players if needed.  
- Tile: Targets a single tile (can be its own).  
- Tiles: Targets a list of specific tiles.  
- City: Applies the effect directly to a city object, rather than to individual tiles.  
- City_Owned: Targets all tiles owned by a city, including the tile the city is on.  
- Tile_Radius: Targets all tiles within a given radius from a center tile.  

Effects can also accept a callable function, allowing them to define custom behavior when triggered.

### State and Behavior  

*Cast effects* may contain state, but it is preferable to keep state minimal to improve reusability. Effects are primarily designed to modify game mechanics rather than store large amounts of state. Keeping effects general ensures better long-term maintainability.

### Triggering and Duration  

Effects are triggered via messages that can be broadcast from various parts of the game. They can:  

- Last multiple turns or be tied to condition checks that determine when they expire.  
- Be evaluated every turn, or trigger under special conditions (e.g., a city being destroyed might activate an effect).  

### Relation to Actions  

Effects are similar to Actions in that they represent and execute game mechanics, but they also serve a UI role. Each effect can include an icon, text, and description, or remain invisible to the user. This allows the system to handle both background mechanics and player-visible effects.

## Tile Improvements

## City Improvements

> Mostly housed in the city object [gameplay/city.py](./gameplay/city.py) and UI [menus/kivy/parts/city.py](./menus/kivy/parts/city.py)

When a player initiates building a unit, the process begins with a button click in the city GUI, which sends a request signal to the city's tagged messenger. The city then performs basic validation checks to determine whether it can build the requested unit or improvement. If valid, the city resets its building state and begins the construction process.

Once construction starts, a signal is sent to notify the UI, which listens for the update and refreshes to reflect the new unit or improvement in progress. The city object then marks the selected unit/improvement as the active build project and instances it accordingly.

Each turn, the city processes its production and adds progress to the current build. Once the required cost is reached, the city:

- Places the improvement (adding it to self.improvements), or
- Spawns the unit (registering it and calling spawn).

### Maintenance Costs

City improvements can charge maintenance to the player or city. During the turn processing phase, upkeep costs are handled:

- For players: The player.contribute() method is called, where negative values represent expenses deducted from the player’s resources.
- For cities: Upkeep is mainly in food, rather than production, and is calculated separately.

## Rules

> Source [gameplay/rules.py](./gameplay/rules.py)

Rules are classes with class methods, implementing a common interface base class that provides stubs for all rule methods.

Each rule set (e.g., SCIVRules) extends this interface and defines concrete values. Since rules are class-based, future overrides (e.g., player-defined rules) can be implemented easily by subclassing.

All rules should be predefined in the interface and registered in the get_rules method, which returns a dictionary mapping rule names to their current values.

## Actions

> Source [system/actions.py](./system/actions.py)

The Action system provides a generic, stateless way to handle actions in the game. Actions are used for units, buildings, and other game objects that perform temporary operations.

Actions cannot be stateful—they execute once and do not persist. They can have conditions to determine if they can run and callbacks for success or failure. While active, they may have properties that influence execution, but they should not store state.

Actions are not registered in the entity manager and are not saved. They are used as one-off actions that execute and then disappear.

Ideal Use Cases:

- Direct UI actions (e.g., move unit, found city, attack)
- Triggering effects based on conditions without modifying game state
- Handling UI-related logic without cluttering entity files

Execution Flow:

- Check condition (if defined)
- Run action if allowed
- Trigger success or failure callback (if defined)

Actions are best for immediate UI interactions where state persistence is not required.
