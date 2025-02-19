from abc import ABC, abstractmethod


class BaseGenerator(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def generate(self):
        pass
