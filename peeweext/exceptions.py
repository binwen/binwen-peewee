
class ValidationError(Exception):
    default_message = 'Invalid input'

    def __init__(self, message=None, params=None):
        if message is None:
            message = self.default_message

        if params is not None:
            message %= params

        self.message = message

    def __str__(self):
        return str(self.message)
