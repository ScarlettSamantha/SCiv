# TODO

> Back to [Main](README.md)

These are not features more things that exist right now and needs to be done something with in the future but not yet the time or not yet sure if/how.

## De-integrate

- [x] Delete and de-implement/~~Refactor~~: system/saving.py
- [x] ~~Delete~~/Implement(?): managers/assets.py (@after: Implemented it as a proper asset manager and cache)

## CI/CD

- [ ] Implement basic CI/CD as I have my gitlab server in any case which can use its runners.

## Refactors

- [x] Move lights.py to a system type class?
- [x] Move camera.py to a system type class?
- [x] Remove old classes from old engine.
- [ ] Move more logic from main into the game manager of possible.
- [x] Rename tile yield to something more generic as its used as the generic resource container
- [ ] Promotion system rework as it has to many properties.
- [ ] Move system/generators to gameplay maybe as they contain spawning logic which is gameplay or maybe split them?

## Improvements

- [ ] Add crash handler for sending back debug crash data.
- [ ] Make it so player cant control enemy units, its already aware what enemy units are and whats its own.
- [x] Collidable mixin should not calculate geometry of ui elements every tick but every few ticks
- [x] Refactor class file into a non-collision and better named.
- [x] Cities need to check if they are buildable and not to close to other cities.
- [x] Units loose focus to often
- [ ] UI sometimes mostly the first clicks are not registered.
- [ ] Better resource spawner thats not just a random percentage pick but is more region and tile type aware. also make sure that critical resources that are needed for gameplay flow are always spawned. and based on map size and on the type of resource.
- [ ] Rule customizer
- [ ] Conditions that check actual state dynamically of objects and can influence gameplay based on this.
- [ ] Look into making turn processing async to let rendering continue for bigger games where turn processing will become a second(s) situation.
- [ ] Make sure previous waiting ui action (eg: move) is canceled when clicking a other action so we have no phantom actions by units that have already been destroyed.

## Features

- [ ] Upgradable buildings, the skeleton is in there but its not yet working.
