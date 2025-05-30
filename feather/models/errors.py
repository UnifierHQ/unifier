class FeatherError(Exception):
    """Base class for all Feather-related errors."""
    pass

class MissingImplementation(FeatherError):
    """Raised when a feature is not implemented."""
    pass
