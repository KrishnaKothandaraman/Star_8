from abc import ABC, abstractmethod


class APIInterface(ABC):
    @abstractmethod
    def getOrdersFromToday(self):
        ...
