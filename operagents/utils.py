import importlib
from typing import Any, TypeVar
from collections.abc import Generator

import jinja2

from operagents.config import TemplateConfig

T = TypeVar("T")


def resolve_dot_notation(obj_str: str) -> Any:
    """Resolve a string to an object using dot notation.

    Example:
        ```python
        resolve_dot_notation("path.to.your_module:obj")
        ```
    """
    modulename, _, cls = obj_str.partition(":")
    if not cls:
        raise ValueError(f"Invalid dot notation string: {obj_str}")
    module = importlib.import_module(modulename)
    instance = module
    for attr_str in cls.split("."):
        instance = getattr(instance, attr_str)
    return instance


def generate_dot_notation(obj: Any) -> str:
    """Generate a dot notation string from an object."""
    return f"{obj.__module__}:{obj.__qualname__}"


def get_all_subclasses(cls: type[T]) -> Generator[type[T], Any, None]:
    """Get all subclasses of a class."""
    for s in cls.__subclasses__():
        yield s
        yield from get_all_subclasses(s)


DEFAULT_RENDERER = jinja2.Environment(autoescape=False, enable_async=True)


def get_template_renderer(template: TemplateConfig) -> jinja2.Template:
    """Get a Jinja2 template renderer from a template configuration."""
    if isinstance(template, str):
        return DEFAULT_RENDERER.from_string(template)

    env = jinja2.Environment(autoescape=False, enable_async=True)
    env.globals.update(
        (func_name, resolve_dot_notation(func_path))
        for func_name, func_path in template.custom_functions.items()
    )
    return env.from_string(template.content)
