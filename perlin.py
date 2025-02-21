import noise
import random

seed = random.uniform(0, 10000)
scale = 5.0

for x in range(5):
    for y in range(5):
        val = noise.pnoise2(
            (x + seed) / scale,
            (y + seed) / scale,
            octaves=6,
            persistence=0.5,
            lacunarity=2.0,
            repeatx=99999,
            repeaty=99999,
            base=int(seed),
        )
        print(f"Noise at ({x}, {y}): {val}")
