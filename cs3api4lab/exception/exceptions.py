class ShareAlreadyExistsError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message


class ShareNotExistsError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message


class InvalidTypeError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message


class ParamError(Exception):
    def __init__(self, key_error):
        self.message = "Missing argument: " + str(key_error)
        super().__init__(self.message)

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message