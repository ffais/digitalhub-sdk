"""
Models for task specifications.
"""
from __future__ import annotations

from typing import Union

from pydantic import BaseModel
from typing_extensions import Literal


class Item(BaseModel):
    """
    Item model.
    """

    key: str
    """Item name."""

    path: str
    """Item mount path inside the container."""


class ConfigMap(BaseModel):
    """
    Spec for config map volume.
    """

    name: str
    """Config map name."""

    items: list[Item] = None
    """List of keys to mount into the container in the specified path.
    If None, all items will be mounted."""


class Secret(BaseModel):
    """
    Spec for secret volume.
    """

    secret_name: str
    """Secret name."""

    items: list[Item] = None
    """List of keys to mount into the container in the specified path.
    If None, all items will be mounted."""


class PVC(BaseModel):
    """
    Spec for persistent volume claim volume.
    """

    claim_name: str
    """Persistent volume claim name."""


class Volume(BaseModel):
    """
    Volume model.
    """

    volume_type: Literal["config_map", "secret", "persistent_volume_claim"]
    """Volume type."""

    name: str
    """Volume name."""

    mount_path: str
    """Volume mount path inside the container."""

    spec: Union[ConfigMap, Secret, PVC]


class NodeSelector(BaseModel):
    """
    NodeSelector model.
    """

    key: str
    """Node selector key."""

    value: str
    """Node selector value."""


class Resource(BaseModel):
    """
    Resource model.
    """

    resource_type: Literal["cpu", "memory", "gpu"]
    """Resource kind (cpu, memory, gpu)."""

    requests: str
    """Resource requests."""

    limits: str
    """Resource limits."""


class Env(BaseModel):
    """
    Env variable model.
    """

    name: str
    """Env variable name."""

    value: str
    """Env variable value."""


class Label(BaseModel):
    """
    Label model.
    """

    name: str
    """Label name."""

    value: str
    """Label value."""


### Affinity and Tolerations ###


class Toleration(BaseModel):
    """
    Toleration model.
    """

    key: str = None
    """Toleration key."""

    operator: str = None
    """Toleration operator."""

    value: str = None
    """Toleration value."""

    effect: str = None
    """Toleration effect."""

    toleration_seconds: int = None
    """Toleration seconds."""


class V1NodeSelectorRequirement(BaseModel):
    key: str
    operator: str
    values: list[str] = None


class V1NodeSelectorTerm(BaseModel):
    match_expressions: list[V1NodeSelectorRequirement] = None
    match_fields: list[V1NodeSelectorRequirement] = None


class V1NodeSelector(BaseModel):
    node_selector_terms: list[V1NodeSelectorTerm]


class V1PreferredSchedulingTerm(BaseModel):
    preference: V1NodeSelector
    weight: int


class V1LabelSelectorRequirement(BaseModel):
    key: str
    operator: str
    values: list[str] = None


class V1LabelSelector(BaseModel):
    match_expressions: list[V1LabelSelectorRequirement] = None
    match_labels: dict[str, str] = None


class V1PodAffinityTerm(BaseModel):
    label_selector: V1LabelSelector = None
    match_label_keys: list[str] = None
    mismatch_label_keys: list[str] = None
    namespace_selector: V1LabelSelector = None
    namespaces: list[str] = None
    topology_key: str


class V1WeightedPodAffinityTerm(BaseModel):
    pod_affinity_term: V1PodAffinityTerm
    weight: int


class V1NodeAffinity(BaseModel):
    preferred_during_scheduling_ignored_during_execution: list[V1PreferredSchedulingTerm] = None
    required_during_scheduling_ignored_during_execution: V1NodeSelector = None


class V1PodAffinity(BaseModel):
    preferred_during_scheduling_ignored_during_execution: list[V1WeightedPodAffinityTerm] = None
    required_during_scheduling_ignored_during_execution: list[V1PodAffinityTerm] = None


class V1PodAntiAffinity(BaseModel):
    preferred_during_scheduling_ignored_during_execution: list[V1WeightedPodAffinityTerm] = None
    required_during_scheduling_ignored_during_execution: list[V1PodAffinityTerm] = None


class Affinity(BaseModel):
    """
    Affinity model.
    """

    node_affinity: V1NodeAffinity = None
    """Node affinity."""

    pod_affinity: V1PodAffinity = None
    """Pod affinity."""

    pod_anti_affinity: V1PodAntiAffinity = None
    """Pod anti affinity."""
