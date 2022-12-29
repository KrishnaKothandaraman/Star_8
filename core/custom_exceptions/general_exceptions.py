# Generic API Error
class GenericAPIException(Exception):
    def __init__(self, message):
        super().__init__(message)


class IncorrectSheetTitleException(Exception):
    def __init__(self, message):
        super().__init__(message)