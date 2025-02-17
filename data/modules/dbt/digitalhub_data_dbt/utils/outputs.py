"""
Runtime Dbt parsing utils module.
"""
from __future__ import annotations

import typing
from dataclasses import dataclass

from dbt.cli.main import dbtRunnerResult
from digitalhub_core.entities._base.status import State
from digitalhub_core.runtimes.results import get_entity_info
from digitalhub_core.utils.generic_utils import encode_string
from digitalhub_core.utils.logger import LOGGER
from digitalhub_data.entities.dataitems.crud import create_dataitem
from digitalhub_data.utils.data_utils import get_data_preview
from digitalhub_data_dbt.utils.env import get_connection
from psycopg2 import sql

if typing.TYPE_CHECKING:
    from dbt.contracts.results import RunResult
    from digitalhub_data.entities.dataitems.entity import Dataitem


# Postgres type mapper to frictionless types.
TYPE_MAPPER = {
    16: "boolean",  # bool
    18: "string",  # char
    20: "integer",  # int8
    21: "integer",  # int2
    23: "integer",  # int4
    25: "string",  # text
    114: "object",  # json
    142: "str",  # xml
    650: "str",  # cidr
    700: "number",  # float4
    701: "number",  # float8
    774: "str",  # macaddr8
    829: "str",  # macaddr
    869: "str",  # inet
    1043: "string",  # varchar
    1082: "date",  # date
    1083: "time",  # time
    1114: "datetime",  # timestamp
    1184: "datetime",  # timestamptz
    1266: "time",  # timetz
    1700: "number",  # numeric
    2950: "str",  # uuid
}


@dataclass
class ParsedResults:
    """
    Parsed results class.
    """

    name: str
    path: str
    raw_code: str
    compiled_code: str
    timings: dict


def parse_results(run_result: dbtRunnerResult, output: str, project: str) -> ParsedResults:
    """
    Parse dbt results.

    Parameters
    ----------
    run_result : dbtRunnerResult
        The dbt result.
    output : str
        The output table name.
    project : str
        The project name.

    Returns
    -------
    ParsedResults
        Parsed results.
    """
    result: RunResult = validate_results(run_result, output, project)
    try:
        path = get_path(result)
        raw_code = get_raw_code(result)
        compiled_code = get_compiled_code(result)
        timings = get_timings(result)
        name = result.node.name
        return ParsedResults(name, path, raw_code, compiled_code, timings)
    except Exception:
        msg = "Something got wrong during results parsing."
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def validate_results(run_result: dbtRunnerResult, output: str, project: str) -> RunResult:
    """
    Parse dbt results.

    Parameters
    ----------
    run_result : dbtRunnerResult
        The dbt result.
    output : str
        The output table name.
    project : str
        The project name.

    Returns
    -------
    RunResult
        Run result.

    Raises
    ------
    RuntimeError
        If something got wrong during function execution.
    """
    try:
        # Take last result, final result of the query
        result: RunResult = run_result.result[-1]
    except IndexError:
        msg = "No results found."
        LOGGER.error(msg)
        raise RuntimeError(msg)

    if not result.status.value == "success":
        msg = f"Function execution failed: {result.status.value}."
        LOGGER.error(msg)
        raise RuntimeError(msg)

    if not result.node.package_name == project.replace("-", "_"):
        msg = f"Wrong project name. Got {result.node.package_name}, expected {project.replace('-', '_')}."
        LOGGER.error(msg)
        raise RuntimeError(msg)

    if not result.node.name == output:
        msg = f"Wrong output name. Got {result.node.name}, expected {output}."
        LOGGER.error(msg)
        raise RuntimeError(msg)

    return result


def get_path(result: RunResult) -> str:
    """
    Get path from dbt result (sql://database/schema/table).

    Parameters
    ----------
    result : RunResult
        The dbt result.

    Returns
    -------
    str
        SQL path.
    """
    try:
        components = result.node.relation_name.replace('"', "")
        components = "/".join(components.split("."))
        return f"sql://{components}"
    except Exception:
        msg = "Something got wrong during path parsing."
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def get_raw_code(result: RunResult) -> str:
    """
    Get raw code from dbt result.

    Parameters
    ----------
    result : RunResult
        The dbt result.

    Returns
    -------
    str
        The raw code.
    """
    try:
        return encode_string(str(result.node.raw_code))
    except Exception:
        msg = "Something got wrong during raw code parsing."
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def get_compiled_code(result: RunResult) -> str:
    """
    Get compiled code from dbt result.

    Parameters
    ----------
    result : RunResult
        The dbt result.

    Returns
    -------
    str
        The compiled code.
    """
    try:
        return encode_string(str(result.node.compiled_code))
    except Exception:
        msg = "Something got wrong during compiled code parsing."
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def get_timings(result: RunResult) -> dict:
    """
    Get timings from dbt result.

    Parameters
    ----------
    result : RunResult
        The dbt result.

    Returns
    -------
    dict
        A dictionary containing timings.
    """
    try:
        compile_timing = None
        execute_timing = None
        for entry in result.timing:
            if entry.name == "compile":
                compile_timing = entry
            elif entry.name == "execute":
                execute_timing = entry
        return {
            "compile": {
                "started_at": compile_timing.started_at.isoformat(),
                "completed_at": compile_timing.completed_at.isoformat(),
            },
            "execute": {
                "started_at": execute_timing.started_at.isoformat(),
                "completed_at": execute_timing.completed_at.isoformat(),
            },
        }
    except Exception:
        msg = "Something got wrong during timings parsing."
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def create_dataitem_(result: ParsedResults, project: str, uuid: str) -> Dataitem:
    """
    Create new dataitem.

    Parameters
    ----------
    result : ParsedResults
        The parsed results.
    project : str
        The project name.
    uuid : str
        The uuid of the model for outputs versioning.

    Returns
    -------
    list[dict]
        The output dataitem infos.

    Raises
    ------
    RuntimeError
        If something got wrong during dataitem creation.
    """
    try:
        # Get columns and data sample from dbt results
        columns, data = get_data_sample(result.name, uuid)

        # Prepare dataitem kwargs
        kwargs = {}
        kwargs["project"] = project
        kwargs["name"] = result.name
        kwargs["kind"] = "dataitem"
        kwargs["path"] = result.path
        kwargs["uuid"] = uuid
        kwargs["schema"] = get_schema(columns)
        kwargs["raw_code"] = result.raw_code
        kwargs["compiled_code"] = result.compiled_code

        # Create dataitem
        dataitem = create_dataitem(**kwargs)

        # Update dataitem status with preview
        dataitem.status.preview = _get_data_preview(columns, data)

        # Save dataitem in core and return it
        dataitem.save()
        return dataitem

    except Exception:
        msg = "Something got wrong during dataitem creation."
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def get_data_sample(table_name: str, uuid: str) -> None:
    """
    Get columns and data sample from dbt results.

    Parameters
    ----------
    table_name : str
        The output table name.
    uuid : str
        The uuid of the model for outputs versioning.

    Returns
    -------
    None
    """
    LOGGER.info("Getting columns and data sample from dbt results.")
    try:
        connection = get_connection()
        query = sql.SQL("SELECT * FROM {table} LIMIT 10;").format(table=sql.Identifier(f"{table_name}_v{uuid}"))
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = cursor.description
                data = cursor.fetchall()
        return columns, data
    except Exception:
        msg = "Something got wrong during data fetching."
        LOGGER.exception(msg)
        raise RuntimeError(msg)
    finally:
        LOGGER.info("Closing connection to postgres.")
        connection.close()


def get_schema(columns: tuple) -> list[dict]:
    """
    Get schema from dbt result.

    Parameters
    ----------
    columns : tuple
        The columns.

    Returns
    -------
    list
        A list of dictionaries containing schema.
    """
    try:
        schema = [{"name": c.name, "type": TYPE_MAPPER.get(c.type_code, "any")} for c in columns]
        return {"schema": schema}
    except Exception:
        msg = "Something got wrong during schema parsing."
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def _get_data_preview(columns: tuple, data: list[tuple]) -> list[dict]:
    """
    Get data preview from dbt result.

    Parameters
    ----------
    columns : tuple
        The columns.
    data : list[tuple]
        The data.

    Returns
    -------
    list
        A list of dictionaries containing data.
    """
    try:
        columns = [i.name for i in columns]
        return get_data_preview(columns, data)
    except Exception:
        msg = "Something got wrong during data preview creation."
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def build_status(dataitem: Dataitem, results: dbtRunnerResult) -> dict:
    """
    Build status.

    Parameters
    ----------
    dataitem : Dataitem
        The dataitem output.
    results : dbtRunnerResult
        The dbt results.

    Returns
    -------
    dict
        The status.
    """
    return {
        "state": State.COMPLETED.value,
        "outputs": {
            "dataitems": [get_entity_info(dataitem, "dataitems")],
        },
        "results": results.result[-1].to_dict(),
    }
