"""
Dbt Function specification module.
"""
from __future__ import annotations

from digitalhub_core.entities.functions.spec import FunctionParams, FunctionSpec
from digitalhub_core.utils.exceptions import EntityError
from digitalhub_core.utils.generic_utils import decode_string, encode_string


class FunctionSpecDbt(FunctionSpec):
    """
    Specification for a Function Dbt.
    """

    def __init__(
        self,
        source: str | None = None,
        sql: str | None = None,
        **kwargs,
    ) -> None:
        """
        Constructor.

        Parameters
        ----------
        sql : str
            SQL query to run inside Dbt.
        """
        super().__init__(source, **kwargs)
        if sql is None:
            raise EntityError("SQL query must be provided.")

        # This is to avoid re-encoding the SQL query when
        # it is already encoded.
        try:
            sql = decode_string(sql)
        except Exception:
            ...
        self.sql = encode_string(sql)


class FunctionParamsDbt(FunctionParams):
    """
    Function Dbt parameters model.
    """

    sql: str = None
    """SQL query to run inside the container."""
