from operagents.config import HookConfig
from operagents.utils import get_all_subclasses, resolve_dot_notation

from ._base import Hook as Hook
from .summary import SummaryHook as SummaryHook

all_hook_types: dict[str, type[Hook]] = {f.type_: f for f in get_all_subclasses(Hook)}


def from_config(config: HookConfig) -> Hook:
    if config.type_ == "custom":
        hook_cls: type[Hook] = resolve_dot_notation(config.path)
        return hook_cls.from_config(config)
    return all_hook_types[config.type_].from_config(config)
