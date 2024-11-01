

class CadesException(Exception):
    default_message = "A general exception occures"

    def __init__(self, *args, **kwargs):
        if not args or not kwargs:
            super().__init__(self.default_message)


class AuthError(CadesException):
    default_message = "Authentication FAILED"
