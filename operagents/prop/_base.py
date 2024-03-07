import abc
from typing import Generic, TypeVar, ClassVar

from pydantic import BaseModel

Jsonable = str | int | float | bool | list["Jsonable"] | dict[str, "Jsonable"]

P = TypeVar("P", bound=BaseModel)
R = TypeVar(
    "R",
)


# agent use prop to call functions
class Prop(abc.ABC, Generic[P, R]):
    """Prop is used by agents to access external functionality by calling functions."""

    type_: ClassVar[str]
    """The type of the prop."""

    @property
    def name(self) -> str:
        """The name of the prop."""
        return self.__class__.__name__

    @property
    def description(self) -> str:
        """A description of the prop."""
        return self.__doc__ or ""

    params: type[P]
    """The parameters required by the prop to call functions."""

    @abc.abstractmethod
    def use(self, params: P) -> R:
        """Call function with the given parameters."""
        raise NotImplementedError
