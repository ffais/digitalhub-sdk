from __future__ import annotations

import typing

import nefertem
from digitalhub_core.utils.exceptions import EntityError
from digitalhub_core.utils.logger import LOGGER
from nefertem_core.utils.exceptions import StoreError

if typing.TYPE_CHECKING:
    from nefertem.client.client import Client

if typing.TYPE_CHECKING:
    from nefertem.client.client import Client


####################
# Configuration
####################


def create_client(output_path: str, store: dict) -> Client:
    """
    Create Nefertem client.

    Parameters
    ----------
    output_path : str
        Output path where to store Nefertem results.
    store : dict
        Store configuration.

    Returns
    -------
    Client
        Nefertem client.
    """
    try:
        client = nefertem.create_client(output_path=output_path)
        try:
            client.add_store(store)
        except StoreError:
            pass
        return client
    except Exception:
        msg = "Error. Nefertem client cannot be created."
        LOGGER.exception(msg)
        raise EntityError(msg)


def create_nt_resources(inputs: list[dict], store: dict) -> list[dict]:
    """
    Create nefertem resources.

    Parameters
    ----------
    inputs : list
        The list of inputs dataitems.
    store : dict
        The store configuration.

    Returns
    -------
    list[dict]
        The list of nefertem resources.
    """
    try:
        resources = []
        for i in inputs:
            res = {}
            res["name"] = i["name"]
            res["path"] = i["path"]
            res["store"] = store["name"]
            resources.append(res)
        return resources
    except KeyError:
        msg = "Error. Dataitem path is not given."
        LOGGER.exception(msg)
        raise EntityError(msg)


def create_nt_run_config(action: str, framework: str, exec_args: dict, parallel: bool, num_worker: int) -> dict:
    """
    Build nefertem run configuration.

    Parameters
    ----------
    action : str
        Action to execute.
    framework : str
        Framework to execute.
    exec_args : dict
        Framework execution arguments.
    parallel : bool
        Whether to run nefertem run in parallel.
    num_worker : int
        Number of workers.

    Returns
    -------
    dict
        The nefertem run configuration.
    """
    if action == "infer":
        operation = "inference"
    elif action == "profile":
        operation = "profiling"
    elif action == "validate":
        operation = "validation"
    return {
        "operation": operation,
        "exec_config": [
            {
                "framework": framework,
                "exec_args": exec_args,
            }
        ],
        "parallel": parallel,
        "num_worker": num_worker,
    }
