from exceptions._base_exception import BaseException


class ConditionException(BaseException):
    pass


class ConditionObjectPropertyDoesNotExist(ConditionException):
    pass
