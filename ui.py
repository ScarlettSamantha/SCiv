from direct.task import Task

def update_camera_text(self, task):
    """Display the current camera position onscreen."""
    pos = self.camera.getPos(self.render)
    self.cam_text.setText(f"Camera Position: {pos}")
    return Task.cont

    # Create onscreen text to display the camera position.
    self.cam_text = OnscreenText(
        text="",           # updated every frame
        parent=self.a2dTopLeft,
        scale=0.05,
        fg=(1, 1, 1, 1),
        align=TextNode.ALeft,
        pos=(0.05, -0.07),
        mayChange=True
    )