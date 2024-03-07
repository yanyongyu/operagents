from operagents.config import FlowConfig
from operagents.utils import get_all_subclasses, resolve_dot_notation

from ._base import Flow as Flow
from .order import OrderFlow as OrderFlow

all_flow_types: dict[str, type[Flow]] = {f.type_: f for f in get_all_subclasses(Flow)}


def from_config(config: FlowConfig) -> Flow:
    if config.type_ == "custom":
        flow_cls = resolve_dot_notation(config.path)
        return flow_cls(**config.model_dump(exclude={"type_", "path"}))
    return all_flow_types[config.type_](**config.model_dump(exclude={"type_"}))
