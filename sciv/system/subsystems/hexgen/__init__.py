from system.subsystems.hexgen.mapgen import MapGen


def generate(params, debug=True, image=True):
    return MapGen(params=params, debug=debug)
