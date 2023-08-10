# Generic API Error
class GenericAPIException(Exception):
    def __init__(self, message):
        super().__init__(message)


class IncorrectAuthTokenException(Exception):
    def __init__(self, message):
        super().__init__(message)


class ResourceExhaustedException(Exception):
    def __init__(self, message):
        super().__init__(message)


class GetStockFromRepairAppsFailedException(Exception):
    def __init__(self, message):
        super().__init__(message)


class StockAllocationFailedException(Exception):
    def __init__(self, message):
        super().__init__(message)


class CreateOrderInRepairAppsFailedException(Exception):
    def __init__(self, message):
        super().__init__(message)