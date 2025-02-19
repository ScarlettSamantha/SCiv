from panda3d.core import NodePath
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from direct.showbase.DirectObject import DirectObject
from mixins.singleton import Singleton


class PauseMenu(Singleton, DirectObject):
    def __setup__(self, base, *args, **kwargs):
        super().__setup__(*args, **kwargs)
        self.base = base

    def __init__(self, base):
        """
        Initialize the pause menu, but keep it hidden until triggered.
        """
        self.base = base

        # Create a parent node for all pause-menu GUI elements.
        # By default, aspect2d is used for 2D GUI in Panda3D.
        # If you want absolute pixel-level positioning, use pixel2d instead.
        self.root = NodePath("pause_menu_root")
        self.root.reparentTo(self.base.aspect2d)

        # Ensure this is rendered last/on top:
        #   1) Disables depth checking, so it always appears on top
        #   2) Places it into a higher-priority bin
        self.root.setBin("gui-popup", 0)
        self.root.setDepthTest(False)
        self.root.setDepthWrite(False)

        # Oversized background panel (to span the entire screen):
        self.bg_frame = DirectFrame(
            parent=self.root,
            frameSize=(-2, 2, -2, 2),  # oversize to ensure coverage
            frameColor=(0, 0, 0, 0.7),  # semi-transparent dark overlay
        )

        # Title label
        self.title_label = DirectLabel(
            parent=self.bg_frame,
            text="Paused",
            scale=0.1,
            pos=(0, 0, 0.4),
            text_fg=(1, 1, 1, 1),
        )

        # Resume button
        self.resume_btn = DirectButton(
            parent=self.bg_frame,
            text="Resume",
            scale=0.07,
            pos=(0, 0, 0.3),
            command=self.hide,  # Hide the pause menu on click
        )

        # Save button
        self.save_btn = DirectButton(
            parent=self.bg_frame,
            text="Save",
            scale=0.07,
            pos=(0, 0, 0.15),
            command=None,  # No functionality for now
        )

        # Load button
        self.load_btn = DirectButton(
            parent=self.bg_frame,
            text="Load",
            scale=0.07,
            pos=(0, 0, 0.0),
            command=None,  # No functionality for now
        )

        # Options button
        self.options_btn = DirectButton(
            parent=self.bg_frame,
            text="Options",
            scale=0.07,
            pos=(0, 0, -0.15),
            command=None,  # No functionality for now
        )

        # Main Menu button
        self.main_menu_btn = DirectButton(
            parent=self.bg_frame,
            text="Main Menu",
            scale=0.07,
            pos=(0, 0, -0.3),
            command=None,  # No functionality for now
        )

        # Quit button
        self.quit_btn = DirectButton(
            parent=self.bg_frame,
            text="Quit",
            scale=0.07,
            pos=(0, 0, -0.45),
            command=self.quit_game,  # your own quit logic
        )

        # Initially hide the entire pause menu
        self.hide()

    def show(self):
        """Show the pause menu."""
        self.root.show()

    def hide(self):
        """Hide the pause menu."""
        self.root.hide()

    def is_hidden(self):
        """Check if the pause menu is hidden."""
        return self.root.isHidden()

    def toggle(self):
        """Toggle pause menu visibility."""
        if self.root.isHidden():
            self.show()
        else:
            self.hide()

    def quit_game(self):
        """Example quit action."""
        print("Quitting game...")
        # You could do something like self.base.userExit() or messenger.send(...)
