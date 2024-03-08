import abc
from typing import ClassVar


class Backend(abc.ABC):
    type_: ClassVar[str]

    # TODO: messages
    @abc.abstractmethod
    async def generate(self, messages: list) -> str:
        raise NotImplementedError
