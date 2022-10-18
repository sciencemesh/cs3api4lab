class ShareError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message

class ShareAlreadyExistsError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message


class ShareNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message


class ResourceNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message


class ProviderNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message


class LockNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message


class FileLockedError(IOError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.__class__.__name__ + ": " + self.message


class OCMDisabledError(Exception):
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