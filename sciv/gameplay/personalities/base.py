from abc import ABC


class BasePersonality(ABC):
    name: str = "Base Personality"

    def __init__(self):
        pass
