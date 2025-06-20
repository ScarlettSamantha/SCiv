from typing import Any
from exceptions.gameplay_exception import GameplayException


class EffectException(GameplayException):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


class EffectDoesNotExist(EffectException):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


class EffectAlreadyExists(EffectException):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)


class EffectCannotBeBoughtOff(EffectException):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
