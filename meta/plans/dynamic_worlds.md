# Dynamic Worlds: Civ-inspired generator plan

## Purpose

This document is a research-backed plan for evolving SCiv's `Dynamic Worlds` generator by borrowing the strongest ideas from Civilization V and VI map generation without copying their implementation wholesale.

The goal is not to recreate Firaxis map scripts line for line. The goal is to adopt the patterns that consistently make Civ maps feel good to play:

- strong macro identity
- readable continent structure
- believable climate and river placement
- late-stage fairness correction instead of early overconstraint
- starts and resources treated as first-class systems
- options that bias the generator instead of replacing it with one-off scripts

## Current SCiv baseline

SCiv already has a solid foundation:

- `sciv/system/generators/dynamic.py` exposes user-facing setup fields for landmass, biome style, world age, temperature, humidity, and sea level.
- `Dynamic.build_map_params()` already converts those options into a numeric recipe.
- `sciv/system/generators/dynamic_worlds/mapgen.py` already wraps hexgen through `DynamicMapGen`.
- `sciv/system/generators/dynamic_worlds/profiles.py` already provides named landmass and biome presets.
- post-generation passes already exist for coastline polish, region naming, river naming, and start-tile scoring.
- world-generation telemetry already exists through `world_generation_stats`.

That means the next step is not a rewrite. The next step is to deepen the generation pipeline.

## Research summary

### Civ VI patterns worth learning from

#### Fantastical Map Script

The strongest lesson from Fantastical Map Script is its staged pipeline.

It treats map generation as a sequence of increasingly concrete decisions:

1. establish a world frame
2. shape landmasses and seas
3. derive climate and regions
4. place mountains and rivers
5. assign terrain and features
6. determine continents
7. place resources, wonders, and starts

The important insight is structural: topology comes first, climate comes after topology, and balance comes late.

Fantastical also shows that high-variance maps still feel coherent when the script keeps persistent intermediate concepts such as:

- oceans
- continents
- inland seas
- regions
- climate cells
- mountain ranges
- river systems

Those intermediate concepts are more important than the exact noise math.

#### YnAMP and TerraMap

YnAMP is most useful for late-stage world usability rather than raw terrain formation.

Important lessons:

- starting positions are judged with explicit fertility heuristics instead of relying on terrain randomness alone
- true-start and scenario maps still perform local land blending and replacement to keep starts viable
- landmasses can be composed from named regional layers rather than a single global fractal
- resources and wonders are easier to control when the generator keeps region and reference-map metadata alive until the end

TerraMap in particular reinforces a strong Civ pattern:

- macro geography can be authored as old world vs new world regions
- land and sea layers can be blended in passes
- rivers should come after elevation and terrain assignment inputs are stable enough to support them
- cliffs, lowlands, resources, and starts all depend on the earlier morphology passes

### Civ V patterns worth learning from

#### Tectonic map script

The Civ V `Tectonic` script is the best direct reference for morphology.

It models the world around seeded plates and relative motion classes:

- collision boundaries raise rough land and mountains
- transform boundaries create rough transitional belts
- rift boundaries lower land and encourage seas or channels

Important lessons:

- macro terrain identity comes from relationships between plates, not just raw elevation noise
- user options should change the strength of systems, not swap out unrelated algorithms
- sea level, island density, continent chunkiness, plate count, and plate motion can all be expressed as numeric modifiers inside one consistent generator
- coast generation works best as an explicit post-pass after land/water classification

This is a very strong fit for SCiv because `Dynamic Worlds` already uses preset-driven option profiles.

#### Civ V AssignStartingPlots

Even from the API surface and modder discussions, the design intent is clear:

- the world is divided into regions
- those regions are measured for fertility and major terrain identity
- civilizations are matched against regions using bias rules
- starts are normalized after placement
- luxuries, strategics, and city states are placed with global and regional rules

Key Civ V lessons:

- start placement is its own subsystem, not a final random pick
- fertility should be measured before final placement, then corrected afterward
- region typing matters for civ flavor and fair distribution
- normalization and resource balancing are a separate phase after starts are chosen

Community analysis of `AssignStartingPlots.lua` also highlights that Civ V start bias behavior is region-aware rather than purely positional. That matters because it shifts the design focus away from "pick the best tile" and toward "pick the best region, then the best tile in that region."

## Core design principles for SCiv

From the Civ research and SCiv's current architecture, the next version of `Dynamic Worlds` should follow these rules.

### 1. Build the map in layers of meaning

Do not jump directly from height noise to final terrain tags.

Keep explicit intermediate concepts:

- macro basins and ocean corridors
- landmasses and subcontinents
- mountain belts and rift corridors
- moisture fields and rain shadows
- candidate start regions
- resource provinces

### 2. Keep user options as biases, not hard script forks

Civ's best scripts use options to nudge a common pipeline.

SCiv should keep a single main pipeline where options alter:

- world frame selection
- water coverage
- tectonic intensity
- climate bias
- hydrology richness
- fairness strictness

This preserves variety and keeps the codebase maintainable.

### 3. Separate morphology, climate, and fairness

These should be distinct phases.

- morphology decides where the land is and how rough it is
- climate decides what kinds of land those places become
- fairness decides whether the result is playable

If these phases are blended too early, the generator becomes harder to reason about and harder to debug.

### 4. Let starts and resources react to the world

Do not force the whole world into fairness.

Instead:

- generate a world with strong identity first
- identify candidate regions
- place starts into those regions
- run local repairs and targeted balance passes only where needed

This is closer to how Civ maps feel handcrafted without actually hand-authoring them.

### 5. Prefer debug visibility over hidden magic

Every major phase should leave behind inspectable data.

SCiv already stores world-generation stats. Expand that system so each pass can explain what it did.

## Proposed target pipeline

## Phase 0: world recipe compilation

Responsibility:

- normalize setup options into one internal recipe
- combine landmass, biome, world-age, humidity, and sea-level presets
- derive secondary knobs such as tectonic intensity, ocean corridor width, inland sea chance, and fairness aggressiveness

Keep in:

- `Dynamic.build_map_params()`
- `dynamic_worlds/profiles.py`

Add:

- a richer internal recipe object or dict contract
- advanced derived values that later phases can consume without reinterpreting user options

Why:

Civ-style scripts work because the expensive phases operate on a stable recipe.

## Phase 1: macro topology frame

Responsibility:

- decide the broad world archetype before local terrain generation
- reserve macro structures such as:
  - pangaea core
  - twin-continent split
  - fractured continent bands
  - island arc belts
  - Terra-style old-world/new-world separation
  - inland sea candidates
  - major ocean corridors

Possible outputs:

- low-resolution macro land mask
- ocean corridor mask
- continent seed regions
- old-world/new-world tags when applicable

Best home:

- new `dynamic_worlds/topology.py`
- orchestrated by `DynamicMapGen`

Why:

This is the biggest gap between current SCiv generation and the Civ-inspired approach. Right now SCiv has landmass presets, but not a strong world-frame stage.

## Phase 2: tectonic morphology

Responsibility:

- generate or approximate plate seeds
- classify neighboring plate relationships as collision, transform, or rift-like
- use those relationships to bias elevation, ridge placement, rough hills, trench-like seas, and chokepoints
- scale roughness and volcanism by world age

Possible outputs:

- tectonic stress field
- ridge mask
- rift mask
- uplift/depression adjustments applied to the heightmap

Best home:

- new `dynamic_worlds/tectonics.py`
- invoked inside `DynamicMapGen` before final hex classification

Why:

This is the cleanest way to import the best idea from Civ V's Tectonic script without needing to reproduce its exact algorithm.

## Phase 3: landmass carving and water connectivity

Responsibility:

- turn the macro frame and tectonic field into final large-scale land/water separation
- carve inland seas, channels, and coastal shelves
- prevent ugly one-tile chokepoints unless the archetype wants them
- classify water into coast, sea, and ocean classes based on connectivity and neighborhood metrics

Best home:

- partly `dynamic_worlds/landmasses.py`
- partly a new `dynamic_worlds/waters.py`
- preserve `apply_scripted_coastline_polish()` as the final cleanup layer, not the main shaper

Why:

Civ maps feel better when seas, coasts, and oceans have gameplay meaning rather than all being "water."

## Phase 4: hydrology

Responsibility:

- choose river source zones from elevation, rainfall, and spacing rules
- favor mountain fronts, uplands, and wet interiors
- carve valleys before or during river routing so major rivers visibly shape the land
- create lakes after primary drainage paths are stable
- reject river systems that terminate too early unless they feed inland basins intentionally

Best home:

- extend `dynamic_worlds/rivers.py`
- optionally split into `rivers.py` and `hydrology.py`

Why:

Both Civ VI and YnAMP reinforce the same lesson: rivers are downstream of morphology and upstream of start quality.

## Phase 5: climate simulation

Responsibility:

- compute temperature from latitude plus world-shape adjustments
- compute moisture from coasts, lakes, rivers, prevailing wind assumptions, and rain shadows
- allow presets to bias Hadley-like dry belts and coastal decay
- produce climate cells before final biome labels are assigned

Best home:

- new `dynamic_worlds/climate.py`
- keep biome-style presets in `profiles.py`

Why:

Current SCiv already exposes temperature and humidity, but a dedicated climate pass would make those options produce more legible world patterns.

## Phase 6: biome and landform realization

Responsibility:

- assign terrain biomes from climate fields
- distinguish deserts, steppe, plains, grassland, tundra, snow, wetlands, jungle belts, and forests using climate plus local relief
- use tectonic masks to encourage mountain chains, foothills, volcanic belts, and broken uplands
- preserve special treatment for archipelago, arid, verdant, and frigid profiles

Best home:

- extend `dynamic_worlds/biomes.py`
- optionally add `dynamic_worlds/landforms.py`

Why:

The Civ-style result comes from terrain being a consequence of world structure, not a decorative overlay.

## Phase 7: region semantics and metadata

Responsibility:

- detect continents, subcontinents, archipelagos, inland seas, and major biomes
- compute per-region metrics:
  - fertility
  - freshwater density
  - coastal access
  - expansion room
  - mountain pressure
  - luxury candidate pools
  - naval accessibility
- generate stable IDs and names for those regions

Best home:

- extend existing naming/metadata helpers
- add new `dynamic_worlds/regions.py`

Why:

This provides the bridge from terrain generation to start placement, resources, and later AI/world flavor systems.

## Phase 8: start-region planning

Responsibility:

- divide inhabitable land into candidate major-player regions
- distinguish region types such as coastal, river valley, open inland, island, jungle edge, tundra frontier, desert river, and mountain basin
- assign civs to regions using available bias rules
- within each region, evaluate tile candidates with the existing scoring model plus region-aware constraints

Best home:

- new `dynamic_worlds/starts.py`
- leave `Dynamic.place_starting_units()` as the outer orchestration point until the new system is proven

Why:

This is the single most important Civ V lesson to import.

Current SCiv start placement is already better than pure randomness, but it is still mostly tile-centric. The next step is region-first placement.

## Phase 9: normalization and fairness repair

Responsibility:

- audit each chosen start for minimum viability
- perform local corrections rather than global smoothing
- possible corrections:
  - add or promote nearby freshwater access
  - soften one excessive terrain penalty
  - add a hill or food tile to weak starts
  - guarantee baseline strategic access within a reasonable radius
  - avoid extreme first-ring dead zones
- keep local identity intact while reducing outliers

Best home:

- new `dynamic_worlds/balance.py`
- or a fairness layer attached to `starts.py`

Why:

This matches the Civ pattern of letting maps be flavorful first and fair second.

## Phase 10: resource ecology

Responsibility:

- place luxuries by continent, biome, and regional role
- place strategics with global caps and local floor guarantees
- ensure island and coast-heavy maps do not starve naval civs of meaningful nearby value
- keep resource placement aware of start normalization so the same start is not fixed twice in conflicting ways

Best home:

- mostly existing `ResourceAllocator`
- add hooks so region and climate metadata can influence placement

Why:

Civ V and VI both make resources part of the balance story, not just decoration.

## Phase 11: final audit and telemetry

Responsibility:

- compute summary metrics for the finished world
- flag seeds that fall outside acceptable thresholds
- optionally reroll or repair only the failing phase
- persist diagnostic metadata for later inspection

Suggested metrics:

- landmass count and size distribution
- coast-to-interior ratio
- river density
- biome coverage percentages
- average start fertility and worst-start fertility
- coastal-start share
- average luxury distance from starts
- strategic resource floor compliance

Best home:

- extend `world_generation_stats`
- add optional debug overlays or CSV-like dumps later

## Architecture plan for SCiv

### Keep these boundaries

- `Basic` remains the baseline world-conversion orchestrator.
- `Dynamic` remains the high-level gameplay generator entry point.
- `DynamicMapGen` remains the procedural map-generation coordinator.
- existing profile modules remain the source of user-facing option definitions.

### Shift more responsibility into `dynamic_worlds/*`

The long-term target should be:

- `dynamic.py` handles setup, high-level orchestration, and world metadata handoff
- `DynamicMapGen` coordinates generation phases in order
- specialized modules own each phase's logic

### Recommended module additions

| Module | Role |
| --- | --- |
| `dynamic_worlds/topology.py` | macro world frame, ocean corridors, Terra-style splits, continent seeds |
| `dynamic_worlds/tectonics.py` | plate seeding, uplift/rift masks, ridge placement |
| `dynamic_worlds/hydrology.py` | river source planning, basin logic, lake policy |
| `dynamic_worlds/climate.py` | temperature and moisture fields, rain shadows, wind bias |
| `dynamic_worlds/regions.py` | continent/subregion detection, fertility summaries, start-region metadata |
| `dynamic_worlds/starts.py` | region-first start assignment and constraints |
| `dynamic_worlds/balance.py` | normalization, local repair passes, fairness audits |
| `dynamic_worlds/telemetry.py` | structured worldgen stats and optional debug exports |

Not all of these need to land immediately. The pipeline matters more than the exact final file split.

## Option model roadmap

### Keep the current default UI simple

The existing fields are good as the default surface:

- landmass
- biome style
- world age
- temperature
- humidity
- sea level

### Add advanced controls only after the pipeline exists

Good candidates for an advanced panel later:

- world template: classic, Terra, island chains, inland seas, shattered world
- tectonic intensity
- coastline complexity
- inland sea amount
- start fairness strictness
- resource richness policy
- old-world/new-world emphasis

This mirrors the best Civ scripts: approachable defaults, deeper controls when the system underneath is strong enough to justify them.

## Implementation phases

### Phase A: refactor for observability

Goal:

- make the current pipeline easier to inspect before changing behavior

Work:

- formalize the internal world recipe
- expand `world_generation_stats`
- store intermediate counts for landmasses, rivers, coast classes, and start quality

Success criteria:

- any seed can be explained after generation
- future pass failures are measurable instead of anecdotal

### Phase B: add macro topology and tectonics

Goal:

- give each map a stronger macro identity

Work:

- implement topology masks
- add plate-like stress or boundary fields
- feed uplift/rift effects into heightmap shaping

Success criteria:

- pangaea, continents, and archipelago feel structurally distinct even before terrain assignment
- mountain belts and channels stop feeling arbitrary

### Phase C: add climate and hydrology feedback loops

Goal:

- make rivers and biomes emerge from world structure

Work:

- dedicated climate pass
- dedicated hydrology pass
- better lake handling and river spacing

Success criteria:

- arid vs wet settings produce visibly different drainage and biome outcomes
- rivers cluster in plausible places and matter to start quality

### Phase D: move to region-first start placement

Goal:

- match Civ V's strongest gameplay-facing generator behavior

Work:

- define start regions
- classify region types
- place civs by region suitability before tile suitability
- add a post-start normalization pass

Success criteria:

- starts feel more thematic and less swingy
- coastal and river bias behavior becomes explainable
- weak-start outliers drop sharply

### Phase E: resource ecology and final polish

Goal:

- make the whole world play better, not just the start positions

Work:

- region-aware luxuries and strategics
- continent-role-based balancing
- better telemetry and debug exports

Success criteria:

- resources reinforce map identity
- island and inland starts each receive distinct strategic opportunities

## Validation plan

Every phase should be tested with a fixed seed suite.

Suggested seed suite dimensions:

- each landmass preset
- each biome style
- each world age
- small, medium, and large map sizes
- at least one extreme combination such as hot + arid + high sea level

For each seed, record:

- landmass summary
- biome coverage summary
- river count and average length proxy
- start scores for all players
- worst-start and best-start deltas
- luxury and strategic accessibility near starts

The target is not perfect symmetry. The target is bounded unfairness with strong world identity.

## Practical heuristics to borrow directly

These heuristics are worth carrying into SCiv almost verbatim at the conceptual level.

- Generate macro land/water form before terrain details.
- Use collision-like boundaries to create ridges and mountains.
- Use rift-like boundaries to create channels, seas, and separation.
- Let rivers depend on relief and moisture, not just randomness.
- Measure start quality with explicit fertility scoring.
- Pick starts by regions first, then by tiles.
- Normalize weak starts after placement instead of flattening the whole world.
- Place resources after starts are known, with both global and regional constraints.
- Keep debug metadata for every phase.

## Things SCiv should not copy blindly

- Civ V's exact start-bias ordering rules
- Civ VI's exact continent or wonder placement rules
- extremely script-specific region tables from YnAMP
- giant monolithic generator files with every rule in one place

SCiv should borrow structure, not baggage.

## Main open design questions

These are not blockers for phase A or B, but they should be decided before the full system is finished.

1. Should `Dynamic Worlds` support a real Terra mode with explicit old-world/new-world exploration pacing?
2. How strict should fairness be relative to world flavor?
3. Should different civ factions eventually expose explicit start-bias tags in SCiv?
4. Should resources be purely ecological, partly fairness-driven, or both?
5. Do we want natural wonders or other landmark systems to participate in the same late-stage balance pipeline?
6. How much generation time is acceptable for large maps if the result quality improves materially?

## Recommended next move

The best next implementation step is not "make better maps" in general.

It is:

1. formalize the internal world recipe
2. add richer telemetry
3. introduce a dedicated macro-topology stage
4. introduce a tectonic morphology pass

That sequence creates the missing backbone. Once that exists, better rivers, climates, starts, and resources become much easier to add without turning `Dynamic Worlds` into an unmaintainable pile of special cases.

## Source signals used for this plan

High-signal references used while forming this plan:

- Civ VI Fantastical Map Script
- Civ VI YnAMP core script
- Civ VI TerraMap script
- Civ V Tectonic map script
- Civ V `AssignStartingPlots` API surface and override hooks
- Civ V `GenerateMap` API surface
- Civ V community reverse-engineering discussion of `AssignStartingPlots.lua`

These sources collectively point to the same conclusion:

The best strategy for SCiv is a phase-based generator with strong intermediate world semantics, region-first starts, and late fairness correction.