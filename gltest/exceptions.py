class DeploymentError(Exception):
    """Raised when a contract deployment fails."""

    pass


class SchemaDiscoveryError(ValueError):
    """Raised when no client can provide a contract's schema.

    Stays a ``ValueError`` so existing handlers keep working. When it is raised
    by ``ContractFactory.deploy()`` the contract is already deployed:
    ``contract_address`` and ``receipt`` identify that deployment, so callers
    can recover it instead of deploying again.
    """

    def __init__(self, message, contract_address=None, receipt=None):
        super().__init__(message)
        self.contract_address = contract_address
        self.receipt = receipt


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
