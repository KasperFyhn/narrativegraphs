from abc import ABC, abstractmethod


class Mapper(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create_mapping(self, labels: list[str]) -> dict[str, str]:
        pass
