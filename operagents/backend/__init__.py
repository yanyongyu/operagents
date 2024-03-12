from operagents.config import BackendConfig
from operagents.utils import get_all_subclasses, resolve_dot_notation

from ._base import Backend as Backend
from ._base import Message as Message
from .user import UserBackend as UserBackend
from ._base import UserMessage as UserMessage
from ._base import SystemMessage as SystemMessage
from .openai import OpenAIBackend as OpenAIBackend
from ._base import AssistantMessage as AssistantMessage

all_backend_types: dict[str, type[Backend]] = {
    b.type_: b for b in get_all_subclasses(Backend)
}


def from_config(config: BackendConfig) -> Backend:
    """Create a backend from a configuration."""
    if config.type_ == "custom":
        backend_cls = resolve_dot_notation(config.path)
        return backend_cls(**config.model_dump(exclude={"type_", "path"}))
    return all_backend_types[config.type_](**config.model_dump(exclude={"type_"}))
