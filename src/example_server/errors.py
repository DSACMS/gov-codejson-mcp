"""Application errors shared by project readers and tools."""


class DuplicateProjectError(ValueError):
    """More than one inventory entry matched the requested ID."""


class InvalidComparisonRequest(ValueError):
    """The requested comparison has invalid entry IDs."""
