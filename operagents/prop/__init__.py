from operagents.config import PropConfig
from operagents.utils import get_all_subclasses, resolve_dot_notation

from ._base import Prop as Prop
from .function import FunctionProp as FunctionProp

all_prop_types: dict[str, type[Prop]] = {p.type_: p for p in get_all_subclasses(Prop)}


def from_config(config: PropConfig) -> Prop:
    if config.type_ == "custom":
        prop_cls = resolve_dot_notation(config.path)
        return prop_cls(**config.model_dump(exclude={"type_", "path"}))
    return all_prop_types[config.type_](**config.model_dump(exclude={"type_"}))
