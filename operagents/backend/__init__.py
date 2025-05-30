from operagents.config import BackendConfig
from operagents.utils import get_all_subclasses, resolve_dot_notation

from ._base import AssistantMessage as AssistantMessage
from ._base import Backend as Backend
from ._base import GeneratePropUsage as GeneratePropUsage
from ._base import GenerateResponse as GenerateResponse
from ._base import Message as Message
from ._base import PropMessage as PropMessage
from ._base import SystemMessage as SystemMessage
from ._base import UserMessage as UserMessage
from .openai import OpenAIBackend as OpenAIBackend
from .user import UserBackend as UserBackend

all_backend_types: dict[str, type[Backend]] = {
    b.type_: b for b in get_all_subclasses(Backend)
}


def from_config(config: BackendConfig) -> Backend:
    """Create a backend from a configuration."""
    if config.type_ == "custom":
        backend_cls: type[Backend] = resolve_dot_notation(config.path)
        return backend_cls.from_config(config)
    return all_backend_types[config.type_].from_config(config)
