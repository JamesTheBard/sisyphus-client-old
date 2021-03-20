class JobRunFailureError(Exception):

    def __init__(self, message: str, module: str):
        self.message = message
        self.module = module
        super().__init__(self.message)


class JobValidationError(Exception):

    def __init__(self, message: str, module: str):
        self.message = message
        self.module = module
        super().__init__(self.message)


class JobConfigurationError(Exception):

    def __init__(self, message: str, module: str):
        self.message = message
        self.module = module
        super().__init__(self.message)
