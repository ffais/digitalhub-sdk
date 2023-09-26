"""
Function module.
"""
from __future__ import annotations

import typing

from sdk.context.factory import get_context
from sdk.entities.base.entity import Entity
from sdk.entities.base.metadata import build_metadata
from sdk.entities.base.status import build_status
from sdk.entities.function.kinds import build_kind
from sdk.entities.function.spec.builder import build_spec
from sdk.entities.task.crud import create_task, new_task
from sdk.runtimes.factory import get_runtime
from sdk.utils.api import DTO_FUNC, api_ctx_create, api_ctx_update
from sdk.utils.exceptions import EntityError
from sdk.utils.generic_utils import get_uiid

if typing.TYPE_CHECKING:
    from sdk.entities.base.metadata import Metadata
    from sdk.entities.base.status import Status
    from sdk.entities.function.spec.objects.base import FunctionSpec
    from sdk.entities.run.entity import Run
    from sdk.entities.task.entity import Task


class Function(Entity):
    """
    A class representing a function.
    """

    def __init__(
        self,
        project: str,
        name: str,
        kind: str | None = None,
        metadata: Metadata | None = None,
        spec: FunctionSpec | None = None,
        status: Status | None = None,
        local: bool = False,
        embedded: bool = True,
        uuid: str | None = None,
    ) -> None:
        """
        Initialize the Function instance.

        Parameters
        ----------
        project : str
            Name of the project.
        name : str
            Name of the object.
        uuid : str
            UUID.
        kind : str
            Kind of the object.
        metadata : Metadata
            Metadata of the object.
        spec : FunctionSpec
            Specification of the object.
        status : Status
            State of the object.
        local: bool
            If True, export locally.
        embedded: bool
            If True, embed object in backend.
        """
        super().__init__()
        self.project = project
        self.name = name
        self.id = get_uiid(uuid=uuid)
        self.kind = kind if kind is not None else build_kind()
        self.metadata = metadata if metadata is not None else build_metadata(name=name)
        self.spec = spec if spec is not None else build_spec(self.kind, **{})
        self.status = status if status is not None else build_status()
        self.embedded = embedded

        # Private attributes
        self._local = local
        self._tasks: dict[str, Task] = {}
        self._context = get_context(self.project)

    #############################
    #  Save / Export
    #############################

    def save(self, uuid: str | None = None) -> dict:
        """
        Save function into backend.

        Parameters
        ----------
        uuid : str
            Specify uuid for the function update

        Returns
        -------
        dict
            Mapping representation of Function from backend.
        """
        if self._local:
            raise EntityError("Use .export() for local execution.")

        obj = self.to_dict(include_all_non_private=True)

        if uuid is None:
            api = api_ctx_create(self.project, DTO_FUNC)
            return self._context.create_object(obj, api)

        self.id = uuid
        api = api_ctx_update(self.project, DTO_FUNC, self.name, uuid)
        return self._context.update_object(obj, api)

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
        filename = (
            filename
            if filename is not None
            else f"function_{self.project}_{self.name}.yaml"
        )
        self._export_object(filename, obj)

    #############################
    #  Function Methods
    #############################

    def run(
        self,
        action: str,
        inputs: dict | None = None,
        outputs: dict | None = None,
        parameters: dict | None = None,
        local_execution: bool = False,
        resources: dict | None = None,
    ) -> Run:
        """
        Run function.

        Parameters
        ----------
        action : str
            Action to execute.
        inputs : dict
            Function inputs. Used in Run.
        outputs : dict
            Function outputs. Used in Run.
        parameters : dict
            Function parameters. Used in Run.
        local_execution : bool
            Flag to determine if object has local execution.
        resources : dict
            K8s resource. Used in Task.
        Returns
        -------
        Run
            Run instance.
        """

        # Create task if not exists
        if self._tasks.get(action) is None:
            self._tasks[action] = new_task(
                project=self.project,
                kind=action,
                function=self._get_function_string(),
                resources=resources,
                local=self._local,
                uuid=self.id,
            )

        # Run function from task
        run = self._tasks[action].run(inputs, outputs, parameters, local_execution)

        # If local execution, merge spec and run locally
        if local_execution:
            spec = {
                **self.spec.to_dict(),
                **self._tasks[action].spec.to_dict(),
                **run.spec.to_dict(),
            }
            runtime = get_runtime(self.kind, action, spec, run.id, self.project)
            return runtime.run()

        # otherwise, return run launched by backend
        return run

    def update_task(self, action: str, spec: dict) -> None:
        """
        Update task.

        Parameters
        ----------
        action : str
            Action to execute.
        spec : dict
            The new Specification of the object.

        Returns
        -------
        None

        Raises
        ------
        EntityError
            If the task is not already created.
        """
        if self._tasks.get(action) is None:
            raise EntityError("Task is not created.")
        _id = self._tasks[action].id
        self._tasks[action] = create_task(
            project=self.project,
            kind=action,
            function=self._get_function_string(),
            resources=spec,
            uuid=_id,
            local=self._local,
        )
        self._tasks[action].save(_id)

    def _get_function_string(self) -> str:
        """
        Get function string.

        Returns
        -------
        str
            Function string.
        """
        return f"{self.kind}://{self.project}/{self.name}:{self.id}"

    #############################
    #  Getters and Setters
    #############################

    @property
    def local(self) -> bool:
        """
        Get local flag.

        Returns
        -------
        bool
            Local flag.
        """
        return self._local

    #############################
    #  Generic Methods
    #############################

    @classmethod
    def from_dict(cls, obj: dict) -> "Function":
        """
        Create object instance from a dictionary.

        Parameters
        ----------
        obj : dict
            Dictionary to create object from.

        Returns
        -------
        Function
            Self instance.
        """
        parsed_dict = cls._parse_dict(obj)
        _obj = cls(**parsed_dict)
        _obj._local = _obj._context.local
        return _obj

    @staticmethod
    def _parse_dict(obj: dict) -> dict:
        """
        Parse dictionary.

        Parameters
        ----------
        obj : dict
            Dictionary to parse.

        Returns
        -------
        dict
            Parsed dictionary.
        """

        # Mandatory fields
        project = obj.get("project")
        name = obj.get("name")
        if project is None or name is None:
            raise EntityError("Project or name are not specified.")

        # Optional fields
        uuid = obj.get("id")
        kind = obj.get("kind")
        kind = build_kind(kind)
        embedded = obj.get("embedded")

        # Build metadata, spec, status
        spec = obj.get("spec")
        spec = spec if spec is not None else {}
        spec = build_spec(kind=kind, **spec)
        metadata = obj.get("metadata", {"name": name})
        metadata = build_metadata(**metadata)
        status = obj.get("status")
        status = status if status is not None else {}
        status = build_status(**status)

        return {
            "project": project,
            "name": name,
            "kind": kind,
            "uuid": uuid,
            "metadata": metadata,
            "spec": spec,
            "status": status,
            "embedded": embedded,
        }


def function_from_parameters(
    project: str,
    name: str,
    description: str = "",
    kind: str | None = None,
    source: str | None = None,
    image: str | None = None,
    tag: str | None = None,
    handler: str | None = None,
    command: str | None = None,
    requirements: list | None = None,
    sql: str | None = None,
    local: bool = False,
    embedded: bool = True,
    uuid: str | None = None,
    **kwargs,
) -> Function:
    """
    Create function.

    Parameters
    ----------
    project : str
        Name of the project.
    name : str
        Identifier of the Function.
    description : str
        Description of the Function.
    kind : str
        The type of the Function.
    source : str
        Path to the Function's source code on the local file system.
    image : str
        Name of the Function's container image.
    tag : str
        Tag of the Function's container image.
    handler : str
        Function handler name.
    command : str
        Command to run inside the container.
    requirements : list
        List of requirements for the Function.
    sql : str
        SQL query.
    local : bool
        Flag to determine if object will be exported to backend.
    embedded : bool
        Flag to determine if object must be embedded in project.
    uuid : str
        UUID.
    **kwargs
        Keyword arguments.

    Returns
    -------
    Function
        Function object.
    """
    kind = build_kind(kind)
    spec = build_spec(
        kind,
        source=source,
        image=image,
        tag=tag,
        handler=handler,
        command=command,
        requirements=requirements,
        sql=sql,
        **kwargs,
    )
    meta = build_metadata(name=name, description=description)
    return Function(
        project=project,
        name=name,
        kind=kind,
        metadata=meta,
        spec=spec,
        local=local,
        embedded=embedded,
        uuid=uuid,
    )


def function_from_dict(obj: dict) -> Function:
    """
    Create function from dictionary.

    Parameters
    ----------
    obj : dict
        Dictionary to create function from.

    Returns
    -------
    Function
        Function object.
    """
    return Function.from_dict(obj)
