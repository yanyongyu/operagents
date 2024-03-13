from operagents.config import DirectorConfig
from operagents.utils import get_all_subclasses, resolve_dot_notation

from ._base import Director as Director
from .user import UserDirector as UserDirector
from .model import ModelDirector as ModelDirector

all_director_types: dict[str, type[Director]] = {
    f.type_: f for f in get_all_subclasses(Director)
}


def from_config(config: DirectorConfig) -> Director:
    if config.type_ == "custom":
        director_cls = resolve_dot_notation(config.path)
        return director_cls(**config.model_dump(exclude={"type_", "path"}))
    return all_director_types[config.type_].from_config(config)
