from exceptions._base_exception import BaseException


class GreatException(BaseException):
    pass


class GreatLoadingException(GreatException):
    pass


class GreatLoadingFolderNotFoundException(GreatLoadingException):
    pass


class GreatPersonNotLoaded(GreatException):
    pass


class GreatPersonTreeNotLoaded(GreatException):
    pass
