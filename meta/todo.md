# TODO

> Back to [Main](README.md)

These are not features more things that exist right now and needs to be done something with in the future but not yet the time or not yet sure if/how.

## De-integrate

- [ ] Delete/Refactor: system/saving.py
- [ ] Delete/Implement(?): managers/assets.py

## CI/CD

- [ ] Implement basic CI/CD as I have my gitlab server in any case which can use its runners.

## Refactors

- [ ] Move lights.py to a system ?
- [ ] Move camera.py to a system ?
- [ ] Remove old classes from old engine.
- [ ] Move more logic from main into the game manager of possible.

## Improvements

- [ ] Add crash handler for sending back debug crash data.
- [ ] Make it so player cant controll enemy units, its already aware what enemy units are and whats its own.
- [x] Colidable mixin should not calculate geometry of ui elements every tick but every few ticks
