from operagents.config import FlowConfig
from operagents.utils import get_all_subclasses, resolve_dot_notation

from ._base import Flow as Flow
from .user import UserFlow as UserFlow
from .model import ModelFlow as ModelFlow
from .order import OrderFlow as OrderFlow

all_flow_types: dict[str, type[Flow]] = {f.type_: f for f in get_all_subclasses(Flow)}


def from_config(config: FlowConfig) -> Flow:
    if config.type_ == "custom":
        flow_cls: type[Flow] = resolve_dot_notation(config.path)
        return flow_cls.from_config(config)
    return all_flow_types[config.type_].from_config(config)
