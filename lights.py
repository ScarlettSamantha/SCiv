from panda3d.core import AmbientLight, DirectionalLight, Vec4
    

def setup_lights(self):
    # Ambient light.
    ambient_light = AmbientLight("ambient")
    ambient_light.setColor(Vec4(0.4, 0.4, 0.4, 1))
    ambient_node = self.render.attachNewNode(ambient_light)

    # Directional light.
    directional_light = DirectionalLight("directional")
    directional_light.setColor(Vec4(0.9, 0.9, 0.8, 1))
    directional_node = self.render.attachNewNode(directional_light)
    directional_node.setHpr(45, -60, 0)

    self.render.setLight(ambient_node)
    self.render.setLight(directional_node)