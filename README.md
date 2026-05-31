# SCiv

> 🚨 **Warning:** This project is in a very early development phase and is likely not fully functional yet. It may lack gameplay elements and is currently focused on testing system implementations.

> ⚠️ **Danger:** This code is highly dynamic and can be vulnerable to arbitrary remote code execution if modified or when using downloaded files. Malicious actors could exploit this to run harmful code (*There is no sandbox*). Be cautious and only load trusted, verified sources.

This project is a hobby and an exercise in something semi-related to my profession. I am trying to make a Civ-like game as I really enjoy the franchise, but not the direction it's currently heading with Civ7.

The main goal (BFG) is to create something functionally similar to Civ. I don't intend to make a clone or a port, but I believe Civ5 and Civ6 had some good ideas, just like Stellaris.

I am building this in a project called [panda3d](https://github.com/panda3d/panda3d), which is a Python game engine written in C++ for the performance-critical parts. I'm using [kivy](https://github.com/kivy/kivy) as the main GUI, as the old DirectGUI system is very outdated. I am aiming for this to remain as much as possible in python as possible with little databases or other systems, more so as to see if I can then out of practicality.

## Requirements

It currently requires (*for now*) a Unix/Windows-based OS, Python 3.13 or greater. Hardware requirements depend on map size: I can run a 150x150 map at zoom levels with a *7800XT*. Normal map sizes (e.g. *90x190*) require about `~3GB` RAM; I expect this to be around `2-4GB`. VRAM usage is about `900MB`, which may grow to `2-4GB` depending on textures and models. It's mostly single-core usage, so a CPU with strong single-thread performance is preferred. At normal zoom levels, it is currently CPU-bound on my Intel 13th-gen i5.

## How to run it

> Known Bugs: [Known Bugs](known_bugs.md)

At the moment, it will remain a basic POC until around version *0.2* It contains some gameplay elements but is still primarily focused on implementation.

It's not difficult to run, thanks to Panda3D. Please check out the development branch for now, as the main branch is outdated. Dev branches should work semi-okay since most features are developed in feature branches.

There might be builds available for your OS, but they're probably outdated minor versions. For now, I suggest running it via Python.

When installed via binary releases, the packages are not signed and require administrator rights on Windows and sudo on Linux to run. This is because, for now, it writes logs and data files to its own directory, which requires elevated rights on both OSes. This will change in the future.

If you install it via Python, it doesn't need admin rights if you place it somewhere it can write to its own directory.

### Ubuntu

#### Binary

You can download the latest release of the `.deb` release and install that it will install its self in `/usr/local` and you can run it via `sudo sciv`(see above on why `sudo`) or via the menu entry it creates in your start menu.

#### GIT

You might encounter standard errors when installing Python packages. Either `pip` or `venv` is required, or you need to install packages via your distro's package manager (e.g., `apt install python3-packages`). I've provided a venv setup, but you can also use system-wide packages.

```bash
sudo apt install git python3-pip python3-venv
```

```bash
git clone https://github.com/ScarlettSamantha/SCiv.git
cd SCiv
python3 -m venv .
source bin/activate
bin/pip install -r requirements.txt
python3 run.py
```

### Windows

As of version `0.1.5`, Windows should work decently. Some images may be missing due to paths not converting properly, but it should still run.

I'm somewhat dependent on friends for Windows testing, as I don't have a Windows PC capable of running the game properly.

Releases (e.g., `.msi`) should work and are usually tested, but dev branches might not.

#### Installer

There should be a `.msi` installer which is just a windows installer format based on the wix installer. You can install that and from that it should create system menu entry for the application and you can run that with administrator rights (see above why `administrator`). If you choose to install it for all users it will install its self in `C://Program Files/sciv` there is no folder selection option yet that I can find but maybe in the future.

#### Git

Install [Python 3.13+](https://www.python.org/downloads/windows/) and [Git](https://gitforwindows.org/).

Clone the repo into a folder of your choice. I recommend using Git Bash, or PowerShell if you're more familiar with that.

```bash
git clone https://github.com/ScarlettSamantha/SCiv.git
chdir SCiv
python -m pip install -r requirements.txt
python run.py
```

Note: use `python` and not `python3`, because Windows links the `python3` command to the Microsoft Store for some reason.

### Debugging

I don't have a Windows machine and haven't used it in a while, so I can't help much with Windows debugging.

You can connect it to `pstats`. Start it listening on the default port `5185`, then press `p` to activate pstats broadcasting and `l` to stop it.

In `config.prc`, GPU debug data is enabled by default. You can disable it there if it causes issues.

## Project

> Docs: [Documentation Index](meta/INDEX.md)  
> Structure: [Project Structure](meta/structure.md)  
> Improvements/ToDo's: [TODO](meta/todo.md)

### 0.1.0 Goals - PoC/Demo

The aim of the 0.1.0 release is to have core systems (engine, managers, rendering, and world mechanics) functional and testable.

#### Key Objective

At this stage, I want the core gameplay loop to function at a basic level:

- A city can build a builder unit.
- The builder can construct an improvement on a tile.
- The improvement modifies tile yields, affecting production.
- A playable PoC or demo would be ideal, but this might be pushed to 0.2.0 since saving/loading is not planned for 0.1.0 and is a priority for 0.2.0.

<details>

- [x] Have world render  
- [x] Have resource system  
- [x] Have a usable map generator  
- [x] Manage entities  
- [x] Spawn units  
- [x] Unit actions  
- [x] Process a minimal turn  
- [x] Cities that can build something  
- [x] Basic player ownership and tile awareness  
- [x] UI shows city ownership of nearby tiles  
- [x] Basic UI elements  
- [x] Movement for units with pathfinding and weighted cost + UI  
- [x] Basic backend systems: managers, systems, logging  
- [x] Proper implementation of UI system (Kivy)  
- [x] Effects implementation  
- [x] Tile improvements  

</details>

### 0.2.0 Goals - Dev

The goal is to have a semi-playable and resumable game, with improved building/dev experience for future development.

- [x] Saving/Loading + GUI  
- [x] Improved map generator with fixed resource type spawns to prevent deadlocks in small games  
- [x] Map regeneration/reroll (same settings)  
- [x] CI/CD with auto-builder and checker on GitLab  
- [x] Working research system  
  - [x] Resource-specific improvements and resource system improvements  
- [x] Civic system implementation + city borders  
- [x] City/Empire borders rendered  
- [x] Barbarians + Nature player + basic AI  
- [x] Basic combat (melee only, no range, river detection, etc.) + UI  
- [ ] Map generator parameters in GUI  
- [X] Better development tools  
- [X] Hide development tools behind a toggle  
- [X] Settings menu  
- [ ] Basic documentation  
- [ ] Dynamic spawning of models when buildings/improvements are constructed  

### (Planning) 0.3.0 Goals - Alpha

Add more functionality to existing systems, flesh out the combat system, and introduce unit types for different planes (air, sea, satellites).

This should be the first truly playable version that's somewhat fun.

<details>

- [ ] Unit embarkation/disembarkation  
- [ ] Fog of war + discovery  
- [ ] Sea/Air units  
- [ ] Show move result before committing  
- [ ] Wonders  
- [ ] (?) Basic enemy AI  
- [ ] Unit promotions and experience  
- [ ] Auto-move for long distance actions across turns  
- [ ] Build queue  
- [ ] Battle result calculation UI  
- [ ] In-game codex UI (basic)  
- [ ] Better tile visuals  
- [ ] Rivers (navigable?)  
- [ ] City renaming/manual naming  
- [ ] Rule customizer  

</details>

### Other Information

- [Documentation Index](meta/INDEX.md) - Start here for Git-tracked project docs  
- [Known Bugs](known_bugs.md) - Tracked issues and rough edges  
- [Changelog](CHANGELOG.md) - Automatically generated  
- [File Structure](meta/structure.md) - Generated project layout  
- [Project Index JSON](meta/generated/project-index.json) - Machine-readable project inventory  
- [Architecture](meta/technical/architecture.md) - Runtime subsystem overview  
- [Startup Flow](meta/technical/startup.md) - Bootstrap and UI handoff path  
- [Entities & Save/Load](meta/technical/entities.md) - Persistence model and entity lifecycle  
- [Turn Processing](meta/technical/turns.md) - Turn pipeline and signal timing  
- [Todo](meta/todo.md) - Remaining tasks  
- [Signals](meta/technical/signals.md) - Internal signal definitions  
- [Rules](meta/technical/rules.md) - Customizable game rules (editor coming ~0.3)  
- [Workings](meta/technical/workings.md) - System overviews  
