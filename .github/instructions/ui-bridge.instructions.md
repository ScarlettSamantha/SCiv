---
name: "SCiv UI Bridge Routing"
description: "Use when editing the Panda3D and Kivy bridge, screen flow, loading-screen handoff, UI manager, UI signals, or SCiv menu code. Routes bridge and UI work to the right docs first."
applyTo: "{sciv/menus/**,sciv/managers/ui.py,sciv/game.py}"
---

# SCiv UI Bridge Routing

- Read [`meta/technical/startup.md`](../../meta/technical/startup.md), [`meta/technical/architecture.md`](../../meta/technical/architecture.md), and [`meta/technical/ui-runtime.md`](../../meta/technical/ui-runtime.md) before changing screen flow, `system.main.ready`, or the Panda3D/Kivy handoff.
- If the change touches messenger events or screen-triggered state flow, also read [`meta/technical/signals.md`](../../meta/technical/signals.md).
- Keep the shared-window assumption in mind: SCiv runs Kivy inside the Panda3D lifecycle rather than as a separate app.
- If the bridge contract or live screen behavior changes, update the startup, UI runtime, and signal docs in the same change and review [`meta/technical/update-triggers.md`](../../meta/technical/update-triggers.md).
