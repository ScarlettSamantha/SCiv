from system import pyload


class PlayerRepository:
    @staticmethod
    def load_all_civilizations():
        return pyload.PyLoad.load_classes("gameplay/civilizations")

    @staticmethod
    def load_all_leaders():
        return pyload.PyLoad.load_classes("gameplay/leaders")
