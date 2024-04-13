import abc
import asyncio
from typing_extensions import Self, override
from collections.abc import Callable, Awaitable
from typing import TYPE_CHECKING, Literal, cast

import openai
from pydantic import ValidationError

from operagents.prop import Prop
from operagents.exception import BackendError
from operagents.utils import resolve_dot_notation, get_template_renderer
from operagents.config import (
    TemplateConfig,
    OpenaiBackendConfig,
    OpenaiBackendToolChoiceConfig,
    OpenaiBackendAutoToolChoiceConfig,
    OpenaiBackendFunctionToolChoiceConfig,
)

from ._base import Backend, Message

if TYPE_CHECKING:
    from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
    from openai.types.chat.chat_completion_message_param import (
        ChatCompletionMessageParam,
    )
    from openai.types.chat.chat_completion_tool_message_param import (
        ChatCompletionToolMessageParam,
    )
    from openai.types.chat.chat_completion_assistant_message_param import (
        ChatCompletionAssistantMessageParam,
    )
    from openai.types.chat.chat_completion_tool_choice_option_param import (
        ChatCompletionToolChoiceOptionParam,
    )

    from operagents.timeline import Timeline


class OpenAIBackendToolChoice(abc.ABC):
    @abc.abstractmethod
    async def choose(
        self,
        timeline: "Timeline",
        messages: list["ChatCompletionMessageParam"],
        props: list[Prop],
    ) -> "ChatCompletionToolChoiceOptionParam": ...


class OpenAIBackendAutoToolChoice(OpenAIBackendToolChoice):
    async def choose(
        self,
        timeline: "Timeline",
        messages: list["ChatCompletionMessageParam"],
        props: list[Prop],
    ) -> "ChatCompletionToolChoiceOptionParam":
        return "auto"


class OpenAIBackendFunctionToolChoice(OpenAIBackendToolChoice):
    def __init__(
        self,
        function: Callable[
            ["Timeline", list["ChatCompletionMessageParam"], list[Prop]],
            Awaitable["ChatCompletionToolChoiceOptionParam"],
        ],
    ) -> None:
        self.function = function

    async def choose(
        self,
        timeline: "Timeline",
        messages: list["ChatCompletionMessageParam"],
        props: list[Prop],
    ) -> "ChatCompletionToolChoiceOptionParam":
        return await self.function(timeline, messages, props)


def openai_backend_tool_choice_from_config(
    config: OpenaiBackendToolChoiceConfig,
) -> OpenAIBackendToolChoice:
    if isinstance(config, OpenaiBackendAutoToolChoiceConfig):
        return OpenAIBackendAutoToolChoice()
    elif isinstance(config, OpenaiBackendFunctionToolChoiceConfig):
        return OpenAIBackendFunctionToolChoice(resolve_dot_notation(config.function))


class OpenAIBackend(Backend):
    type_ = "openai"

    def __init__(
        self,
        model: str,
        temperature: float | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        max_retries: int = 2,
        response_format: Literal["text", "json_object"] = "text",
        tool_choice: OpenAIBackendToolChoice,
        prop_validation_error_template: TemplateConfig,
    ) -> None:
        super().__init__()

        self.client = openai.AsyncOpenAI(
            api_key=api_key, base_url=base_url, max_retries=max_retries
        )
        self.model: str = model
        self.temperature: float | None = temperature
        self.response_format: Literal["text", "json_object"] = response_format
        self.tool_choice = tool_choice

        self.prop_validation_error_renderer = get_template_renderer(
            prop_validation_error_template
        )

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: OpenaiBackendConfig
    ) -> Self:
        return cls(
            model=config.model,
            temperature=config.temperature,
            api_key=config.api_key,
            base_url=config.base_url,
            response_format=config.response_format,
            max_retries=config.max_retries,
            tool_choice=openai_backend_tool_choice_from_config(config.tool_choice),
            prop_validation_error_template=config.prop_validation_error_template,
        )

    async def _use_prop(self, prop: Prop, args: str) -> str:
        if prop.params is None:
            param = None
        else:
            try:
                param = prop.params.model_validate_json(args)
            except ValidationError as e:
                return await self.prop_validation_error_renderer.render_async(
                    prop=prop, exc=e
                )

        return str(await prop.use(param))

    def _prop_to_tool(self, prop: Prop) -> "ChatCompletionToolParam":
        if prop.params is None:
            return {
                "type": "function",
                "function": {
                    "name": prop.name,
                    "description": prop.description,
                },
            }
        else:
            return {
                "type": "function",
                "function": {
                    "name": prop.name,
                    "description": prop.description,
                    "parameters": prop.params.model_json_schema(),
                },
            }

    @override
    async def generate(
        self,
        timeline: "Timeline",
        messages: list[Message],
        props: list["Prop"] | None = None,
    ) -> str:
        messages_ = cast(list["ChatCompletionMessageParam"], messages)

        tools: list["ChatCompletionToolParam"] = (
            [self._prop_to_tool(prop) for prop in props] if props else []
        )
        if props:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_format={"type": self.response_format},
                messages=messages_,
                tools=tools,
                tool_choice=(await self.tool_choice.choose(timeline, messages_, props)),
            )
        else:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_format={"type": self.response_format},
                messages=messages_,
            )

        reply = response.choices[0].message

        while reply.tool_calls:
            if not props:
                raise BackendError(
                    "OpenAI returned tool calls but no props were provided"
                )

            messages_.append(
                cast(
                    "ChatCompletionAssistantMessageParam",
                    reply.model_dump(exclude_unset=True),
                )
            )

            available_props = {prop.name: prop for prop in props}
            results = await asyncio.gather(
                *(
                    self._use_prop(
                        available_props[call.function.name], call.function.arguments
                    )
                    for call in reply.tool_calls
                )
            )

            messages_.extend(
                (
                    cast(
                        "ChatCompletionToolMessageParam",
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": result,
                        },
                    )
                    for call, result in zip(reply.tool_calls, results)
                )
            )

            if props:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    response_format={"type": self.response_format},
                    messages=messages_,
                    tools=tools,
                    tool_choice=(
                        await self.tool_choice.choose(timeline, messages_, props)
                    ),
                )
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    response_format={"type": self.response_format},
                    messages=messages_,
                )
            reply = response.choices[0].message

        if reply.content is None:
            raise BackendError("OpenAI did not return a text response")
        return reply.content
