"""
Nefertem Function specification module.
"""
from sdk.entities.functions.spec import FunctionParams, FunctionSpec


class FunctionSpecNefertem(FunctionSpec):
    """
    Specification for a Function Nefertem.
    """

    def __init__(
        self,
        source: str | None = None,
        constraints: list[dict] | None = None,
        error_report: str | None = None,
        metrics: list[dict] | None = None,
        **kwargs,
    ):
        super().__init__(source, **kwargs)
        self.constraints = constraints
        self.error_report = error_report
        self.metrics = metrics


class FunctionParamsNefertem(FunctionParams):
    """
    Function Nefertem parameters model.
    """

    constraints: list[dict] | None = None
    """List of constraints for the function."""

    error_report: str | None = None
    """Error report kind for the function."""

    metrics: list[dict] | None = None
    """List of metrics for the function."""
