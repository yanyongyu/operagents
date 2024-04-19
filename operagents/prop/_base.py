import abc
from typing_extensions import Self, TypeVar
from typing import TYPE_CHECKING, Any, Generic, ClassVar

from pydantic import BaseModel

from operagents.log import logger
from operagents.config import PropConfig
from operagents.exception import OperaFinished

if TYPE_CHECKING:
    from operagents.timeline import Timeline

Jsonable = str | int | float | bool | list["Jsonable"] | dict[str, "Jsonable"]

P = TypeVar("P", bound=BaseModel, default=BaseModel)


# agent use prop to call functions
class Prop(abc.ABC, Generic[P]):
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

    params: type[P] | None
    """The parameters required by the prop to call functions."""

    @classmethod
    @abc.abstractmethod
    def from_config(cls, config: PropConfig) -> Self:
        raise NotImplementedError

    async def use(self, timeline: "Timeline", params: P | None) -> Any:
        """Use the prop to call functions."""
        logger.debug(
            "Using prop {prop.name} with params: {params!r}", prop=self, params=params
        )
        try:
            result = await self.call(timeline, params)
        except OperaFinished:
            logger.info("Prop {prop.name} ended the opera", prop=self)
            # allow prop to end the opera
            raise
        except Exception:
            logger.opt(exception=True).error(
                "Prop {prop.name} raised an exception", prop=self
            )
            raise
        else:
            logger.debug(
                "Prop {prop.name} returned result: {result!r}", prop=self, result=result
            )

        return result

    @abc.abstractmethod
    async def call(self, timeline: "Timeline", params: P | None) -> Any:
        """Call function with the given parameters."""
        raise NotImplementedError
