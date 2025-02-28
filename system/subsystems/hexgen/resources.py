import random
from typing import List, Type

from gameplay.resource import BaseResource
from system.subsystems.hexgen.grid import Grid
from system.subsystems.hexgen.hex import Hex


class ResourceManager:
    def __init__(self, hex_grid: Grid):
        self.hex_grid: Grid = hex_grid

    def generate_resources(self):
        """
        Places resources on hexes based on their spawn chance and clustering attributes,
        ensuring a variety of resources appear.
        """
        print("Placing resources")

        # Placeholder function to retrieve all available resources
        def get_all_resources() -> List[Type[BaseResource]]:
            from gameplay.repositories.resources import ResourceRepository
            from gameplay.resource import ResourceType

            instance = ResourceRepository()
            resources = instance.all_by_type([ResourceType.STRATEGIC, ResourceType.BONUS, ResourceType.LUXURY])
            return resources

        # Get all available resources
        resources = get_all_resources()
        used_resources = set()

        # Iterate over each hex in the grid
        for col in self.hex_grid.grid:
            for hex_tile in col:
                # Select a resource ensuring variety
                hex_tile: Hex = hex_tile  # just for type hinting
                available_resources = [r for r in resources if r not in used_resources] or resources
                resource = random.choice(available_resources)

                # Determine the spawn chance for the resource
                if isinstance(resource.spawn_chance, tuple):
                    spawn_chance = random.uniform(resource.spawn_chance[0], resource.spawn_chance[1])
                else:
                    spawn_chance = resource.spawn_chance

                # Attempt to place the resource on the tile based on its spawn chance
                if random.uniform(0, 100) <= spawn_chance:
                    hex_tile.add_gameplay_resource(resource)  # Assign the resource to the tile
                    used_resources.add(resource)  # Track used resources to increase variety

                    # If the resource is clusterable, attempt clustering
                    if resource.clusterable is not None:
                        self._cluster_resource(hex_tile, resource)

    def _cluster_resource(self, center_tile, resource):
        """
        Handles clustering of resources around the initially placed tile.
        """

        # Determine maximum cluster radius and dropoff rate
        max_radius = (
            resource.cluster_max_radius
            if isinstance(resource.cluster_max_radius, int)
            else random.randint(resource.cluster_max_radius[0], resource.cluster_max_radius[1])
        )
        dropoff_rate = (
            resource.cluster_dropoff_amount_rate
            if isinstance(resource.cluster_dropoff_amount_rate, float)
            else random.uniform(resource.cluster_dropoff_amount_rate[0], resource.cluster_dropoff_amount_rate[1])
        )

        # Use bubble function to get all hexes within clusterable radius
        cluster_hexes = center_tile.bubble(max_radius)

        for hex_tile in cluster_hexes:
            if hex_tile.resource is None:
                # Compute probability based on distance from original tile
                distance = self._hex_distance(center_tile, hex_tile)
                new_probability = 1.0 - (dropoff_rate * distance)

                # Ensure probability is above zero before proceeding
                if new_probability > 0 and random.uniform(0, 1) <= new_probability * resource.clusterable:
                    hex_tile.resource = resource  # Assign resource to neighboring tile

    def _hex_distance(self, hex1, hex2):
        """
        Calculates the distance between two hex tiles using axial coordinates.
        """
        dx = abs(hex1.x - hex2.x)
        dy = abs(hex1.y - hex2.y)
        return max(dx, dy, abs(dx - dy))
