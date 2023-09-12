

class ApidatanotfoundException(Exception):
    def __init__(self, message):
        self.message = message


class ApidatacomputeException(Exception):
    def __init__(self, message):
        self.message = message


class DataformatErrorException(Exception):
    def __init__(self, message):
        self.message = message