# Not implemented google service error
class InvalidGoogleServiceException(Exception):
    def __init__(self, message):
        super().__init__(message)


class IncorrectSheetTitleException(Exception):
    def __init__(self, message):
        super().__init__(message)