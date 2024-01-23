from __future__ import annotations

import typing

import nefertem

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
    client = nefertem.create_client(output_path=output_path)
    try:
        client.add_store(store)
    except nefertem.utils.exceptions.StoreError:
        pass
    return client


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
    resources = []
    for i in inputs:
        res = {}
        res["name"] = i["name"]
        res["path"] = i["path"]
        res["store"] = store["name"]
        resources.append(res)
    return resources


def create_nt_run_config(action: str, spec: dict) -> dict:
    """
    Build nefertem run configuration.

    Parameters
    ----------
    spec : dict
        Run specification.

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
    elif action == "metric":
        operation = "metric"
    return {
        "operation": operation,
        "exec_config": [
            {
                "framework": spec.get("framework"),
                "exec_args": spec.get("exec_args", {}),
            }
        ],
        "parallel": spec.get("parallel", False),
        "num_worker": spec.get("num_worker", 1),
    }
