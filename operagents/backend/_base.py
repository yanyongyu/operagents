import abc
from typing_extensions import Self, TypeVar, TypedDict
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    ClassVar,
    Annotated,
    TypeAlias,
    NamedTuple,
)

from pydantic import Field, BaseModel

from operagents.config import BackendConfig

if TYPE_CHECKING:
    from operagents.prop import Prop
    from operagents.timeline import Timeline

P = TypeVar("P", bound=BaseModel, default=BaseModel)


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


class AssistantMessage(TypedDict):
    role: Literal["assistant"]
    """The role of the messages author, in this case `assistant`."""
    content: str
    """The contents of the assistant message."""


class PropMessage(TypedDict, Generic[P]):
    role: Literal["prop"]
    """The role of the messages author, in this case `prop`."""
    usage_id: str
    """The usage id of the prop."""
    prop: "Prop[P]"
    """The prop that the message is about."""
    raw_params: str
    """The raw input of the prop that the message is about."""
    params: P | None
    """The parameter of the prop that the message is about."""
    result: Any
    """The result of the prop message."""


Message: TypeAlias = Annotated[
    SystemMessage | UserMessage | AssistantMessage | PropMessage,
    Field(discriminator="role"),
]


class GenerateResponse(NamedTuple):
    """The response from generating messages."""

    content: str
    prop_usage: list[PropMessage]


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
        self,
        timeline: "Timeline",
        messages: list[Message],
        props: list["Prop"] | None = None,
    ) -> GenerateResponse:
        """Generate a message based on the given messages and props."""
        raise NotImplementedError
