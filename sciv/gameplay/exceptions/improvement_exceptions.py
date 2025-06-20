from gameplay.exceptions.gameplay_exception import GameplayException


class ImprovementException(GameplayException):
    pass


class ImprovementUpgradeException(ImprovementException):
    pass
