"""
Workflow module.
"""
from __future__ import annotations

import typing

from sdk.context.builder import get_context
from sdk.entities._base.entity import Entity
from sdk.entities._builders.metadata import build_metadata
from sdk.entities._builders.spec import build_spec
from sdk.entities._builders.status import build_status
from sdk.utils.api import api_ctx_create, api_ctx_update
from sdk.utils.commons import WKFL
from sdk.utils.generic_utils import build_uuid, get_timestamp

if typing.TYPE_CHECKING:
    from sdk.context.context import Context
    from sdk.entities.workflows.metadata import WorkflowMetadata
    from sdk.entities.workflows.spec import WorkflowSpec
    from sdk.entities.workflows.status import WorkflowStatus


class Workflow(Entity):
    """
    A class representing a workflow.
    """

    def __init__(
        self,
        uuid: str,
        kind: str,
        metadata: WorkflowMetadata,
        spec: WorkflowSpec,
        status: WorkflowStatus,
    ) -> None:
        """
        Constructor.

        Parameters
        ----------
        uuid : str
            UUID.
        kind : str
            Kind of the object.
        metadata : WorkflowMetadata
            Metadata of the object.
        spec : WorkflowSpec
            Specification of the object.
        status : WorkflowStatus
            Status of the object.
        """
        super().__init__()
        self.id = uuid
        self.kind = kind
        self.metadata = metadata
        self.spec = spec
        self.status = status

        self.project = self.metadata.project
        self.name = self.metadata.name
        self.embedded = self.metadata.embedded
        self._obj_attr.extend(["project", "name", "embedded"])

    #############################
    #  Save / Export
    #############################

    def save(self, update: bool = False) -> dict:
        """
        Save workflow into backend.

        Parameters
        ----------
        update : bool
            Flag to indicate update.

        Returns
        -------
        dict
            Mapping representation of Workflow from backend.
        """
        obj = self.to_dict()

        if not update:
            api = api_ctx_create(self.metadata.project, WKFL)
            return self._context().create_object(obj, api)

        self.metadata.updated = obj["metadata"]["updated"] = get_timestamp()
        api = api_ctx_update(self.metadata.project, WKFL, self.metadata.name, self.id)
        return self._context().update_object(obj, api)

    def export(self, filename: str | None = None) -> None:
        """
        Export object as a YAML file.

        Parameters
        ----------
        filename : str
            Name of the export YAML file. If not specified, the default value is used.

        Returns
        -------
        None
        """
        obj = self.to_dict()
        filename = filename if filename is not None else f"workflow_{self.metadata.project}_{self.metadata.name}.yaml"
        self._export_object(filename, obj)

    #############################
    #  Context
    #############################

    def _context(self) -> Context:
        """
        Get context.

        Returns
        -------
        Context
            Context.
        """
        return get_context(self.metadata.project)


def workflow_from_parameters(
    project: str,
    name: str,
    kind: str,
    description: str | None = None,
    embedded: bool = True,
    uuid: str | None = None,
    **kwargs,
) -> Workflow:
    """
    Create a new Workflow instance with the specified parameters.

    Parameters
    ----------
    project : str
        A string representing the project associated with this workflow.
    name : str
        The name of the workflow.
    description : str
        A description of the workflow.
    kind : str
        Kind of the object.
    embedded : bool
        Flag to determine if object must be embedded in project.
    uuid : str
        UUID.
    **kwargs
        Keyword arguments.

    Returns
    -------
    Workflow
        An instance of the created workflow.
    """
    uuid = build_uuid(uuid)
    metadata = build_metadata(
        WKFL,
        project=project,
        name=name,
        version=uuid,
        description=description,
        embedded=embedded,
    )
    spec = build_spec(
        WKFL,
        kind,
        **kwargs,
    )
    status = build_status(WKFL)
    return Workflow(
        uuid=uuid,
        kind=kind,
        metadata=metadata,
        spec=spec,
        status=status,
    )


def workflow_from_dict(obj: dict) -> Workflow:
    """
    Create Workflow instance from a dictionary.

    Parameters
    ----------
    obj : dict
        Dictionary to create Workflow from.

    Returns
    -------
    Workflow
        Workflow instance.
    """
    return Workflow.from_dict(WKFL, obj)
