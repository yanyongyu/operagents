from operagents.config import ScenePrepareConfig
from operagents.utils import get_all_subclasses, resolve_dot_notation

from ._base import ScenePrepare as ScenePrepare
from .preface import PrefaceScenePrepare as PrefaceScenePrepare
from .function import FunctionScenePrepare as FunctionScenePrepare

all_scene_prerpare_types: dict[str, type[ScenePrepare]] = {
    p.type_: p for p in get_all_subclasses(ScenePrepare)
}


def from_config(config: ScenePrepareConfig) -> ScenePrepare:
    if config.type_ == "custom":
        scene_prepare_cls: type[ScenePrepare] = resolve_dot_notation(config.path)
        return scene_prepare_cls.from_config(config)
    return all_scene_prerpare_types[config.type_].from_config(config)
