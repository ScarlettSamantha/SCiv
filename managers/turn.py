from mixins.singleton import Singleton


class Turn(Singleton):
    PREPARE_FOR_GAME = -1
    GAME_BEGIN = 0

    def __init__(self, base):
        self.base = base
        self.active = False
        self.turn: int = self.PREPARE_FOR_GAME

    def __setup__(self, base, *args, **kwargs):
        self.base = base
        return super().__setup__(*args, **kwargs)

    def register(self):
        pass

    def de_activate(self):
        self.active = False

    def activate(self):
        self.active = True

    def end_turn(self):
        self.turn += 1

    def get_turn(self) -> int:
        return self.turn

    def set_turn(self, turn_num: int):
        pass
