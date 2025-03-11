# SCiv

> 🚨 **Warning:** This project is in a very early development phase and is likely not functional yet. It may lack gameplay elements and is currently focused on testing raw system implementations.

> ⚠️ **Danger:** This code is highly dynamic and can be vulnerable to arbitrary remote code execution if modified or when using downloaded files. Malicious actors could exploit this to run harmful code(*!There is no sandbox!*). Be extremely cautious and only load trusted, verified sources.

## Running it

> Known Bugs: [Known Bugs](meta/known_bugs.md)

At the moment it will run *something* and I will attempt to keep the main branch booting into the "game" at the least.

### How to run it

Its not that hard to actually run it as its panda3d now. Please do checkout the development branch for now as the main branch will be very outdated and the dev brenches should work semi ok as most features are made in feature branches.

#### ubuntu

It might give you the standard error when trying to install python packages but ether pip or venv are required. or you need to pull your own packages from the distro's repository (eg: apt install python packages). This is why I have provided a venv route, you can choose to just system install the packages.

```bash
sudo apt install git python3-pip python3-venv
```

```bash
git clone https://github.com/ScarlettSamantha/SCiv.git
cd SCiv
python3 -m venv .
source bin/activate
bin/pip install -r requirements.txt
python3 main.py
```

#### Requirements

It requires (*for now*) a unix OS, Python3.11 or greater and hardware spec wise it depends on map size I can run a 150x150 map at zoom levels with a *7800XT* when using normal map sizes eg: *90x120* ish requires about `750MB` ram and I expect this to grow to about `2-4GB` ram required. VRAM it seems to use around `500MB` I expect this to row to some `3-6GB` In the end depending on the textures and models. its mostly single core usage so a strong single core performing cpu should be better. its also at normal zoom levels at the moment of writing on my pc cpu bound (Intel 13th gen i5).

### Debugging

I dont have windows or used it in a while so I cant help with windows debugging.

You can connect it to pstats you need to have it listening on the default port `5185` then you press `p` to activate pstats broadcasting and `l` to stop it again.

In the `config.prc` is defined it will also debug GPU data but if this is causing issues you can disable it there.

#### Lenses

There are also lenses for debugging or you can use the buttons in the debug ui they will trigger the same functions.
Beware the menu and button states dont update each other tough

- `b`: Highlights units in `blue` while tiles that have no units in `red`
- `n`: Highlights resources and their types on the map `yellow` for strategic, `green`/`yellow` for bonus, `red` for none. please note colors might look different
- `m`: Highlights water and different types of it, `tiel` is coastal and shallow, `blue` deeper and sea
- `z`: Calculates and toggles major icons on tiles
- `x`: Toggles big buttons on tiles
- `c`: Toggles small icons on tiles

#### Issues

- Its reporting module missing: Please make a bug report forgot to add it to requirements.txt
- Why venv: Because if I tell you to break system packages and something goes wrong people get mad.

## Project

> Structure [Project Structure](meta/structure.md)

> Improvements/ToDo's [TODO](meta/todo.md)

### 0.1.0 Goals - Dev

The goal of the 0.1.0 release is to have systems functional(engine, managers, rendering and world) and in a testable state.

What does this mean concrete? I the sytems to run and in the end want to be able to build a builder in a city with production calculated from the tiles, which then can build an improvement on a tile which in turn increases tile resources.
A POC/Demo state would be best case senario but that might wait till version 0.2.0 due to not planning to include save and loading in 0.1.0 goals but as one of the first 0.2.0 goals

- [x] Have world render
- [x] Have resource system
- [x] Have ok atleast map generator
- [x] Manage entities
- [x] Spawn units
- [x] Unit actions
- [x] Process a minimal turn
- [ ] Cities that can build something (WIP)
- [x] Basic player ownership and city being aware of tiles around it
- [x] UI city show ownership of tiles around it.
- [ ] Basic UI element (WIP)
- [x] Movement for units both pathfinded and weighted + UI
- [x] Basic backend system integration like managers, systems, logging
- [x] Proper Implementation UI system (kivy)

### (Provisional) 0.2.0 Goals - Dev

The goal is to have an actual semi playable and resumable game and improved building/developer experience to improve speed for future implementations.

- [ ] Saving/Loading + GUI
- [ ] Map regeneration
- [ ] Map gen parameters in GUI
- [ ] Units dumb fighting (no war or detection of rivers etc, just mele no range), meaby UI for
this.
- [ ] Improve map generator with fixed resource type spawns to prevent deadlocks in smaller games due to critical resources lacking.
- [ ] CI/CD, Would like a auto builder and checker running on my gitlab instance.
- [ ] City/Empire borders drawn
- [ ] Change log generation + Auto versioning
- [ ] Working research
- [ ] Civic system implementation
- [ ] Hide development things behind a toggle.
- [ ] Settings menu
- [ ] Basic documentation
- [ ] Dynamic spawning of models when buildings/improvements get build

### (Provisional) 0.3.0 Goals - Alpha

Adding more functionality to aready existing systems and flushing out the combat system and working on units that can inhabit a other plane eg: air, water and space(satelites) units.

This should be the first real "playable" version that should be some level of fun.

<details>

- [ ] Unit embarkaction/disembarkaction.
- [ ] Sea/Air units
- [ ] Show result before moving
- [ ] Wonders
- [ ] (?) Basic enemy AI
- [ ] Unit promotions and exp
- [ ] Auto move if a move action is to far to do it at the end of the next turn
- [ ] Build queue
- [ ] Battle result calculation UI
- [ ] Basic ingame codex UI (not fully implemented)
- [ ] Better looking tiles
- [ ] Barbarians
- [ ] Rivers (navigable ?)
- [ ] City renaming/manual naming

</details>

### Other information

- [Roadmap](meta/roadmap.md) - A rough roadmap (without timelines as this is a hobby project).
- [Contribution Guide](CONTRIBUTE.md) - Guidelines for contributing.
- [Changelog](CHANGELOG.md) - Automatically generated changelog.
- [File Structure](meta/structure.md) - The project structure
- [Todo](meta/todo.md) - Things that still need to be done in current codebase.
- [Signals](meta/technical/signals.md) - Signals used to send to other elements of the code

### Vision

> [Main document](meta/vision.md)

SCiv aims to create a larger and more complex game than Civilization VI, featuring a greater number of civilizations and deeper gameplay mechanics. Our goal is to build a game that retains the fun and engaging core gameplay of Civ6 while enhancing its complexity and mod-ability from the ground up. My aim is to create a more Stellaris-style Civ with more interesting things to do.

### Pitfalls

This is a lot of work, and the scale of the systems is significant. The main challenge might come from the lack of relevant game development experience. Currently, performance is acceptable, but we may need to revisit some aspects in the future. With careful planning and foresight, we hope to avoid major issues. But reality is almost never this good.

## Game

### Mechanics

- [Ages](./ideas/gameplay/age.md)
- [Climate](./ideas/gameplay/climate.md)
- [Disease](./ideas/gameplay/disease.md)
- [Yields](./ideas/gameplay/yields.md)
- [Movement](./ideas/gameplay/mechanics/movement.md)
- [Religion](./ideas/gameplay/mechanics/religion.md)

### Wonders

- [Early](./ideas/wonders/early.md)
- [Mid](./ideas/wonders/mid.md)
- [Late](./ideas/wonders/late.md)

### Greats

- [Artists](./ideas/gameplay/greats/artist.md)
- [Commercial](./ideas/gameplay/greats/commercial.md)
- [Folk Hero](./ideas/gameplay/greats/hero.md)
- [Holy](./ideas/gameplay/greats/faith.md)
- [Generals & Admirals](./ideas/gameplay/greats/military.md)
- [Engineers](./ideas/gameplay/greats/production.md)
- [Scientists](./ideas/gameplay/greats/science.md)

### Resources

<details>

| Resource          | Type                                                    | Code                                                  | Docs                                               |
| ----------------- | ------------------------------------------------------- | ----------------------------------------------------- | -------------------------------------------------- |
| Bison             | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](resources/core/bonus/bison.py)                 | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Cheese            | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/cheese.py)                   | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Copper            | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/copper.py)                   | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Cows              | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/cows.py)                     | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Deer              | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/deer.py)                     | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Ember             | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/ember.py)                    | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Fish              | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/fish.py)                     | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Furs              | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/furs.py)                     | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Glass             | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/glass.py)                    | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Hardwood          | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/hardwood.py)                 | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Mercury           | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/murcury.py)                  | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Obsidian          | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/obsidian.py)                 | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Pigs              | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/pigs.py)                     | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Potato            | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/potato.py)                   | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Rice              | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/rice.py)                     | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Salt              | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/salt.py)                     | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Tin               | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/tin.py)                      | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Whales            | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/whales.py)                   | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Wheat             | [Bonus](meta/ideas/gameplay/resources/BONUS.md)         | [Code](ources/core/bonus/wheat.py)                    | [Docs](meta/ideas/gameplay/resources/BONUS.md)     |
| Cats              | [Luxury](meta/ideas/gameplay/resources/LUXURY.md)       | [Code](ources/core/luxury/cats.py)                    | [Docs](meta/ideas/gameplay/resources/LUXURY.md)    |
| Diamonds          | [Luxury](meta/ideas/gameplay/resources/LUXURY.md)       | [Code](ources/core/luxury/diamonds.py)                | [Docs](meta/ideas/gameplay/resources/LUXURY.md)    |
| Dogs              | [Luxury](meta/ideas/gameplay/resources/LUXURY.md)       | [Code](ources/core/luxury/dogs.py)                    | [Docs](meta/ideas/gameplay/resources/LUXURY.md)    |
| Gold              | [Luxury](meta/ideas/gameplay/resources/LUXURY.md)       | [Code](ources/core/luxury/gold.py)                    | [Docs](meta/ideas/gameplay/resources/LUXURY.md)    |
| Ivory             | [Luxury](meta/ideas/gameplay/resources/LUXURY.md)       | [Code](ources/core/luxury/ivory.py)                   | [Docs](meta/ideas/gameplay/resources/LUXURY.md)    |
| Jade              | [Luxury](meta/ideas/gameplay/resources/LUXURY.md)       | [Code](resources/core/luxury/jade.py)                 | [Docs](meta/ideas/gameplay/resources/LUXURY.md)    |
| Marble            | [Luxury](meta/ideas/gameplay/resources/LUXURY.md)       | [Code](resources/core/luxury/marble.py)               | [Docs](meta/ideas/gameplay/resources/LUXURY.md)    |
| Silver            | [Luxury](meta/ideas/gameplay/resources/LUXURY.md)       | [Code](resources/core/luxury/silver.py)               | [Docs](meta/ideas/gameplay/resources/LUXURY.md)    |
| Aluminium         | [Strategic](meta/ideas/gameplay/resources/STRATEGIC.md) | [Code](resources/core/strategic/aluminium.py)         | [Docs](meta/ideas/gameplay/resources/STRATEGIC.md) |
| Coal              | [Strategic](meta/ideas/gameplay/resources/STRATEGIC.md) | [Code](resources/core/strategic/coal.py)              | [Docs](meta/ideas/gameplay/resources/STRATEGIC.md) |
| Gas               | [Strategic](meta/ideas/gameplay/resources/STRATEGIC.md) | [Code](resources/core/strategic/gas.py)               | [Docs](meta/ideas/gameplay/resources/STRATEGIC.md) |
| Graphite          | [Strategic](meta/ideas/gameplay/resources/STRATEGIC.md) | [Code](resources/core/strategic/graphite.py)          | [Docs](meta/ideas/gameplay/resources/STRATEGIC.md) |
| Horses            | [Strategic](meta/ideas/gameplay/resources/STRATEGIC.md) | [Code](resources/core/strategic/horses.py)            | [Docs](meta/ideas/gameplay/resources/STRATEGIC.md) |
| Oil               | [Strategic](meta/ideas/gameplay/resources/STRATEGIC.md) | [Code](resources/core/strategic/oil.py)               | [Docs](meta/ideas/gameplay/resources/STRATEGIC.md) |
| Rare Earth Metals | [Strategic](meta/ideas/gameplay/resources/STRATEGIC.md) | [Code](resources/core/strategic/rare_earth_metals.py) | [Docs](meta/ideas/gameplay/resources/STRATEGIC.md) |
| Uranium           | [Strategic](meta/ideas/gameplay/resources/STRATEGIC.md) | [Code](resources/core/strategic/uranium.py)           | [Docs](meta/ideas/gameplay/resources/STRATEGIC.md) |

</details>

### Civilizations

<details>

| Civilization                                                  | Wikipedia Link                                                         | Code                                                     |
| ------------------------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------------------- |
| [Akkadian](./ideas/civs/akkadian.md)               | [Akkadian Empire](https://en.wikipedia.org/wiki/Akkadian_Empire)       | [code](openciv/gameplay/civilization/akkadian.py)        |
| [American Empire](./ideas/civs/american_empire.md) | [American Empire](https://en.wikipedia.org/wiki/American_Empire)       | [code](openciv/gameplay/civilization/american_empire.py) |
| [Byzantine](./ideas/civs/byzantine.md)             | [Byzantine Empire](https://en.wikipedia.org/wiki/Byzantine_Empire)     | [code](openciv/gameplay/civilization/byzantine.py)       |
| [China](./ideas/civs/china.md)                     | [History of China](https://en.wikipedia.org/wiki/History_of_China)     | [code](openciv/gameplay/civilization/china.py)           |
| [Egypt](./ideas/civs/egypt.md)                     | [Ancient Egypt](https://en.wikipedia.org/wiki/Ancient_Egypt)           | [code](openciv/gameplay/civilization/egypt.py)           |
| [England](./ideas/civs/england.md)                 | [History of England](https://en.wikipedia.org/wiki/History_of_England) | [code](openciv/gameplay/civilization/england.py)         |
| [France](./ideas/civs/france.md)                   | [History of France](https://en.wikipedia.org/wiki/History_of_France)   | [code](openciv/gameplay/civilization/france.py)          |
| [Germany](./ideas/civs/germany.md)                 | [History of Germany](https://en.wikipedia.org/wiki/History_of_Germany) | [code](openciv/gameplay/civilization/germany.py)         |
| [Greece](./ideas/civs/greece.md)                   | [Ancient Greece](https://en.wikipedia.org/wiki/Ancient_Greece)         | [code](openciv/gameplay/civilization/greece.py)          |
| [Japan](./ideas/civs/japan.md)                     | [History of Japan](https://en.wikipedia.org/wiki/History_of_Japan)     | [code](openciv/gameplay/civilization/japan.py)           |
| [Korea](./ideas/civs/korea.md)                     | [History of Korea](https://en.wikipedia.org/wiki/History_of_Korea)     | [code](openciv/gameplay/civilization/korea.py)           |
| [Low Countries](./ideas/civs/low_countries.md)     | [Low Countries](https://en.wikipedia.org/wiki/Low_Countries)           | [code](openciv/gameplay/civilization/low_countries.py)   |
| [Ottoman](./ideas/civs/ottoman.md)                 | [Ottoman Empire](https://en.wikipedia.org/wiki/Ottoman_Empire)         | [code](openciv/gameplay/civilization/ottoman.py)         |
| [Persia](./ideas/civs/persia.md)                   | [Persian Empire](https://en.wikipedia.org/wiki/Persian_Empire)         | [code](openciv/gameplay/civilization/persia.py)          |
| [Rome](./ideas/civs/rome.md)                       | [Ancient Rome](https://en.wikipedia.org/wiki/Ancient_Rome)             | [code](openciv/gameplay/civilization/rome.py)            |
| [Spain](./ideas/civs/spain.md)                     | [History of Spain](https://en.wikipedia.org/wiki/History_of_Spain)     | [code](openciv/gameplay/civilization/spain.py)           |
| [USSR](./ideas/civs/ussr.md)                       | [Soviet Union](https://en.wikipedia.org/wiki/Soviet_Union)             | [code](openciv/gameplay/civilization/ussr.py)            |
| [Vikings](./ideas/civs/vikings.md)                 | [Vikings](https://en.wikipedia.org/wiki/Vikings)                       | [code](openciv/gameplay/civilization/vikings.py)         |

</details>

### Leaders

<details>

| Leader                                                                         | Wikipedia Link                                                                                       | Code                                                        |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| [Abraham Lincoln](./ideas/gameplay/leaders/abraham_lincoln.md)                 | [Abraham Lincoln (American Empire)](https://en.wikipedia.org/wiki/Abraham_Lincoln)                   | [code](openciv/gameplay/leaders/abraham_lincoln.py)         |
| [Alexander](./ideas/gameplay/leaders/alexander.md)                             | [Alexander the Great (Greece)](https://en.wikipedia.org/wiki/Alexander_the_Great)                    | [code](openciv/gameplay/leaders/alexander.py)               |
| [Ambiorix](./ideas/gameplay/leaders/ambiorix.md)                               | [Ambiorix (Low Countries)](https://en.wikipedia.org/wiki/Ambiorix)                                   | [code](openciv/gameplay/leaders/ambiorix.py)                |
| [Atatürk](./ideas/gameplay/leaders/attaturk.md)                                | [Mustafa Kemal Atatürk (Ottoman)](https://en.wikipedia.org/wiki/Mustafa_Kemal_Atat%C3%BCrk)          | [code](openciv/gameplay/leaders/attaturk.py)                |
| [Augustus](./ideas/gameplay/leaders/augustus.md)                               | [Augustus (Rome)](https://en.wikipedia.org/wiki/Augustus)                                            | [code](openciv/gameplay/leaders/augustus.py)                |
| [Caesar](./ideas/gameplay/leaders/caesar.md)                                   | [Julius Caesar (Rome)](https://en.wikipedia.org/wiki/Julius_Caesar)                                  | [code](openciv/gameplay/leaders/caesar.py)                  |
| [Charlemagne](./ideas/gameplay/leaders/charlemagne.md)                         | [Charlemagne (France)](https://en.wikipedia.org/wiki/Charlemagne)                                    | [code](openciv/gameplay/leaders/charlemagne.py)             |
| [Charles III](./ideas/gameplay/leaders/charles_iii.md)                         | [Charles III (Spain)](https://en.wikipedia.org/wiki/Charles_III_of_Spain)                            | [code](openciv/gameplay/leaders/charles_iii.py)             |
| [Charles V](./ideas/gameplay/leaders/charles_v.md)                             | [Charles V (Holy Roman Empire)](https://en.wikipedia.org/wiki/Charles_V,_Holy_Roman_Emperor)         | [code](openciv/gameplay/leaders/charles_v.py)               |
| [Cleopatra](./ideas/gameplay/leaders/cleopatra.md)                             | [Cleopatra (Egypt)](https://en.wikipedia.org/wiki/Cleopatra)                                         | [code](openciv/gameplay/leaders/cleopatra.py)               |
| [Cnut](./ideas/gameplay/leaders/cnut.md)                                       | [Cnut the Great (Vikings)](https://en.wikipedia.org/wiki/Cnut)                                       | [code](openciv/gameplay/leaders/cnut.py)                    |
| [Constantine](./ideas/gameplay/leaders/constantine.md)                         | [Constantine the Great (Byzantine)](https://en.wikipedia.org/wiki/Constantine_the_Great)             | [code](openciv/gameplay/leaders/constantine.py)             |
| [Darius](./ideas/gameplay/leaders/darius.md)                                   | [Darius the Great (Persia)](https://en.wikipedia.org/wiki/Darius_the_Great)                          | [code](openciv/gameplay/leaders/darius.py)                  |
| [De Gaulle](./ideas/gameplay/leaders/de_gaulle.md)                             | [Charles de Gaulle (France)](https://en.wikipedia.org/wiki/Charles_de_Gaulle)                        | [code](openciv/gameplay/leaders/de_gaulle.py)               |
| [Elizabeth](./ideas/gameplay/leaders/elizabeth.md)                             | [Elizabeth I (England)](https://en.wikipedia.org/wiki/Elizabeth_I)                                   | [code](openciv/gameplay/leaders/elizabeth.py)               |
| [FDR](./ideas/gameplay/leaders/fdr.md)                                         | [Franklin D. Roosevelt (American Empire)](https://en.wikipedia.org/wiki/Franklin_D._Roosevelt)       | [code](openciv/gameplay/leaders/fdr.py)                     |
| [Giovanni di Bicci de' Medici](./ideas/gameplay/leaders/goi.md)                | [Giovanni di Bicci de' Medici (Italy)](https://en.wikipedia.org/wiki/Giovanni_di_Bicci_de%27_Medici) | [code](openciv/gameplay/leaders/goi.py)                     |
| [Gorbachev](./ideas/gameplay/leaders/gorbashov.md)                             | [Mikhail Gorbachev (USSR)](https://en.wikipedia.org/wiki/Mikhail_Gorbachev)                          | [code](openciv/gameplay/leaders/gorbashov.py)               |
| [Herald](./ideas/gameplay/leaders/herald.md)                                   | [Herald of the Great Danelaw (Vikings)](https://en.wikipedia.org/wiki/Herald_of_the_Great_Danelaw)   | [code](openciv/gameplay/leaders/herald.py)                  |
| [Isabella](./ideas/gameplay/leaders/isabella.md)                               | [Isabella I of Castile (Spain)](https://en.wikipedia.org/wiki/Isabella_I_of_Castile)                 | [code](openciv/gameplay/leaders/isabella.py)                |
| [James](./ideas/gameplay/leaders/james.md)                                     | [James VI and I (England)](https://en.wikipedia.org/wiki/James_VI_and_I)                             | [code](openciv/gameplay/leaders/james.py)                   |
| [Joan van Oldenbarnevelt](./ideas/gameplay/leaders/joan_van_oldenbarnevelt.md) | [Johan van Oldenbarnevelt (Low Countries)](https://en.wikipedia.org/wiki/Johan_van_Oldenbarnevelt)   | [code](openciv/gameplay/leaders/joan_van_oldenbarnevelt.py) |
| [Justinian](./ideas/gameplay/leaders/justinian.md)                             | [Justinian I (Byzantine)](https://en.wikipedia.org/wiki/Justinian_I)                                 | [code](openciv/gameplay/leaders/justinian.py)               |
| [Kamehameha](./ideas/gameplay/leaders/kamehameha.md)                           | [Kamehameha I (Hawaii)](https://en.wikipedia.org/wiki/Kamehameha_I)                                  | [code](openciv/gameplay/leaders/kamehameha.py)              |
| [Kublai](./ideas/gameplay/leaders/kublai.md)                                   | [Kublai Khan (Mongolia)](https://en.wikipedia.org/wiki/Kublai_Khan)                                  | [code](openciv/gameplay/leaders/kublai.py)                  |
| [Lenin](./ideas/gameplay/leaders/lenin.md)                                     | [Vladimir Lenin (USSR)](https://en.wikipedia.org/wiki/Vladimir_Lenin)                                | [code](openciv/gameplay/leaders/lenin.py)                   |
| [Leonidas](./ideas/gameplay/leaders/leonidas.md)                               | [Leonidas I (Greece)](https://en.wikipedia.org/wiki/Leonidas_I)                                      | [code](openciv/gameplay/leaders/leonidas.py)                |
| [Louis XIV](./ideas/gameplay/leaders/louis.md)                                 | [Louis XIV (France)](https://en.wikipedia.org/wiki/Louis_XIV)                                        | [code](openciv/gameplay/leaders/louis.py)                   |
| [Meiji](./ideas/gameplay/leaders/meiji.md)                                     | [Meiji Emperor (Japan)](https://en.wikipedia.org/wiki/Meiji_(emperor))                               | [code](openciv/gameplay/leaders/meiji.py)                   |
| [Napoleon](./ideas/gameplay/leaders/napoleon.md)                               | [Napoleon Bonaparte (France)](https://en.wikipedia.org/wiki/Napoleon)                                | [code](openciv/gameplay/leaders/napoleon.py)                |
| [Naram-Sin](./ideas/gameplay/leaders/naram_sin.md)                             | [Naram-Sin (Akkadian)](https://en.wikipedia.org/wiki/Naram-Sin_of_Akkad)                             | [code](openciv/gameplay/leaders/naram_sin.py)               |
| [Nebuchadnezzar](./ideas/gameplay/leaders/nebuchadnezzar.md)                   | [Nebuchadnezzar II (Babylon)](https://en.wikipedia.org/wiki/Nebuchadnezzar_II)                       | [code](openciv/gameplay/leaders/nebuchadnezzar.py)          |
| [Otto](./ideas/gameplay/leaders/otto.md)                                       | [Otto von Bismarck (Germany)](https://en.wikipedia.org/wiki/Otto_von_Bismarck)                       | [code](openciv/gameplay/leaders/otto.py)                    |
| [Peter](./ideas/gameplay/leaders/peter.md)                                     | [Peter the Great (Russia)](https://en.wikipedia.org/wiki/Peter_the_Great)                            | [code](openciv/gameplay/leaders/peter.py)                   |
| [Philip II](./ideas/gameplay/leaders/phillip.md)                               | [Philip II of Spain (Spain)](https://en.wikipedia.org/wiki/Philip_II_of_Spain)                       | [code](openciv/gameplay/leaders/phillip.py)                 |
| [Qin Shi Huang](./ideas/gameplay/leaders/qin_shi_huang.md)                     | [Qin Shi Huang (China)](https://en.wikipedia.org/wiki/Qin_Shi_Huang)                                 | [code](openciv/gameplay/leaders/qin_shi_huang.py)           |
| [Ragnar](./ideas/gameplay/leaders/ragnar.md)                                   | [Ragnar Lodbrok (Vikings)](https://en.wikipedia.org/wiki/Ragnar_Lodbrok)                             | [code](openciv/gameplay/leaders/ragnar.py)                  |
| [Ramesses](./ideas/gameplay/leaders/ramesses.md)                               | [Ramesses II (Egypt)](https://en.wikipedia.org/wiki/Ramesses_II)                                     | [code](openciv/gameplay/leaders/ramesses.py)                |
| [Sargon](./ideas/gameplay/leaders/sargon.md)                                   | [Sargon of Akkad (Akkadian)](https://en.wikipedia.org/wiki/Sargon_of_Akkad)                          | [code](openciv/gameplay/leaders/sargon.py)                  |
| [Sejong](./ideas/gameplay/leaders/sejon.md)                                    | [Sejong the Great (Korea)](https://en.wikipedia.org/wiki/Sejong_the_Great)                           | [code](openciv/gameplay/leaders/sejon.py)                   |
| [Sitting Bull](./ideas/gameplay/leaders/sitting_bull.md)                       | [Sitting Bull (Sioux)](https://en.wikipedia.org/wiki/Sitting_Bull)                                   | [code](openciv/gameplay/leaders/sitting_bull.py)            |
| [Suleiman](./ideas/gameplay/leaders/suleiman.md)                               | [Suleiman the Magnificent (Ottoman)](https://en.wikipedia.org/wiki/Suleiman_the_Magnificent)         | [code](openciv/gameplay/leaders/suleiman.py)                |
| [Taisho](./ideas/gameplay/leaders/taisho.md)                                   | [Taishō Emperor (Japan)](https://en.wikipedia.org/wiki/Taish%C5%8D_Emperor)                          | [code](openciv/gameplay/leaders/taisho.py)                  |
| [Tokugawa](./ideas/gameplay/leaders/tokugawa.md)                               | [Tokugawa Ieyasu (Japan)](https://en.wikipedia.org/wiki/Tokugawa_Ieyasu)                             | [code](openciv/gameplay/leaders/tokugawa.py)                |
| [Victoria](./ideas/gameplay/leaders/victoria.md)                               | [Queen Victoria (England)](https://en.wikipedia.org/wiki/Queen_Victoria)                             | [code](openciv/gameplay/leaders/victoria.py)                |
| [Wilhelm](./ideas/gameplay/leaders/wilhelm.md)                                 | [Wilhelm II (Germany)](https://en.wikipedia.org/wiki/Wilhelm_II,_German_Emperor)                     | [code](openciv/gameplay/leaders/wilhelm.py)                 |
| [William the Silent](./ideas/gameplay/leaders/willem.md)                       | [William the Silent (Low Countries)](https://en.wikipedia.org/wiki/William_the_Silent)               | [code](openciv/gameplay/leaders/willem.py)                  |
| [Wu Zetian](./ideas/gameplay/leaders/wu_zetian.md)                             | [Wu Zetian (China)](https://en.wikipedia.org/wiki/Wu_Zetian)                                         | [code](openciv/gameplay/leaders/wu_zetian.py)               |
| [Xerxes](./ideas/gameplay/leaders/xerxes.md)                                   | [Xerxes I (Persia)](https://en.wikipedia.org/wiki/Xerxes_I)                                          | [code](openciv/gameplay/leaders/xerxes.py)                  |

</details>

### Win Conditions

<details>

| Condition                                        | Mechanic                              | Meta-Docs                                           | Code |
| ------------------------------------------------ | ------------------------------------- | --------------------------------------------------- | ---- |
| [Alliance](./ideas/gameplay/victory/alliance.md) | State Building/Diplomacy              | [alliance.md](./ideas/gameplay/victory/alliance.md) | code |
| [Commerce](./ideas/gameplay/victory/gold.md)     | Gold/Corporations/Trade               | [gold.md](./ideas/gameplay/victory/gold.md)         | code |
| [Military](./ideas/gameplay/victory/military.md) | War/Military                          | [military.md](./ideas/gameplay/victory/military.md) | code |
| [Religion](./ideas/gameplay/victory/religion.md) | Religion/War/Spy/Instability          | [religion.md](./ideas/gameplay/victory/religion.md) | code |
| [Science](./ideas/gameplay/victory/science.md)   | State Building/Diplomacy              | [science.md](./ideas/gameplay/victory/science.md)   | code |
| [Culture](./ideas/gameplay/victory/culture.md)   | Culture/Tourism/Archaeology/Diplomacy | [culture.md](./ideas/gameplay/victory/culture.md)   | code |

</details>

> ⚖️ **Disclaimer:** This game and its associated code are provided for educational and informational purposes only. The author assumes no responsibility for any errors, omissions, or inaccuracies in the code. Users are strongly advised to thoroughly review, test, the code. The author makes no guarantees regarding the security, reliability, or performance of the game. By using this code, you agree that the author shall not be held liable for any damages, losses, or other consequences arising from its use, misuse, or inability to use the game, including but not limited to any unintended or harmful actions caused by the game. Use this game at your own risk and ensure that all necessary precautions are taken.

> 🌍 **Historical Context and Point of View Disclaimer:**
> OpenCiv includes civilizations, leaders, and events inspired by real-world history but real history is complex. While I strive to create a neutral point of view, the game may simplify or alter historical events for gameplay purposes. These portrayals try to not reflect any political or cultural stance but should not be taken as any kind of truth. The content reflects my personal view and understanding from a (inherently limited) Western perspective, and I try to avoid contentious topics I am uncomfortable with dealing with. I acknowledge that many events depicted were horrible and should never be repeated. This game is for entertainment. Please don't cancel me; I want to create a fun game for everyone. 🙏
