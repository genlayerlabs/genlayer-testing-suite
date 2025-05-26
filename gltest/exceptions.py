class DeploymentError(Exception):
    """Raised when a contract deployment fails."""

    pass


class FixtureSnapshotError(Exception):
    """Raised when there's an error restoring a snapshot."""

    pass


class FixtureAnonymousFunctionError(Exception):
    """Raised when a fixture is an anonymous function."""

    pass


class InvalidSnapshotError(Exception):
    """Raised when a snapshot is invalid."""

    pass


class HelperError(Exception):
    """Raised when a helper function fails."""

    pass
