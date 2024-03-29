import abc
from typing import Literal, ClassVar, TypeAlias
from typing_extensions import Self, Required, TypedDict

from operagents.prop import Prop
from operagents.config import BackendConfig


class Function(TypedDict):
    name: str
    """The name of the function to call."""
    arguments: str
    """
    The arguments to call the function with, as generated by the model in JSON
    format. Note that the model does not always generate valid JSON, and may
    hallucinate parameters not defined by your function schema. Validate the
    arguments in your code before calling your function.
    """


class MessageToolCall(TypedDict):
    type: Literal["function"]
    """The type of the tool. Currently, only `function` is supported."""
    id: str
    """The ID of the tool call."""
    function: Function
    """The function that the model called."""


class SystemMessage(TypedDict):
    role: Literal["system"]
    """The role of the messages author, in this case `system`."""
    content: str
    """The contents of the system message."""


class UserMessage(TypedDict):
    role: Literal["user"]
    """The role of the messages author, in this case `user`."""
    content: str
    """The contents of the user message."""


class AssistantMessage(TypedDict, total=False):
    role: Required[Literal["assistant"]]
    """The role of the messages author, in this case `assistant`."""
    content: str | None
    """The contents of the assistant message.

    Required unless `tool_calls` is specified.
    """
    tool_calls: list[MessageToolCall]
    """The tool calls generated by the model, such as function calls."""


Message: TypeAlias = SystemMessage | UserMessage | AssistantMessage


class Backend(abc.ABC):
    """A backend for generating messages."""

    type_: ClassVar[str]
    """The type of the backend."""

    @classmethod
    @abc.abstractmethod
    def from_config(cls, config: BackendConfig) -> Self:
        """Create a backend from a configuration."""
        raise NotImplementedError

    @abc.abstractmethod
    async def generate(
        self, messages: list[Message], props: list["Prop"] | None = None
    ) -> str:
        """Generate a message based on the given messages and props."""
        raise NotImplementedError
