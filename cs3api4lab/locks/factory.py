from cs3api4lab.locks.metadata import Metadata
from cs3api4lab.locks.cs3 import Cs3


class LockApiFactory:

    @staticmethod
    def create(log, config):
        if config.locks_api == 'metadata':
            return Metadata(log, config)
        elif config.locks_api == 'cs3':
            return Cs3(log, config)
        else:
            raise NotImplementedError("Lock API implementation not found")
