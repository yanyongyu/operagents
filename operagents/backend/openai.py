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

from ._base import Backend, Message, PropMessage, GenerateResponse

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

    async def _use_prop(
        self, timeline: "Timeline", prop: Prop, usage_id: str, args: str
    ) -> PropMessage:
        if prop.params is None:
            param = None
        else:
            try:
                param = prop.params.model_validate_json(args)
            except ValidationError as e:
                return PropMessage(
                    role="prop",
                    usage_id=usage_id,
                    prop=prop,
                    raw_params=args,
                    params=None,
                    result=await self.prop_validation_error_renderer.render_async(
                        prop=prop, exc=e
                    ),
                )

        return PropMessage(
            role="prop",
            usage_id=usage_id,
            prop=prop,
            raw_params=args,
            params=param,
            result=await prop.use(timeline, param),
        )

    def _messages_to_openai(
        self, messages: list[Message]
    ) -> list["ChatCompletionMessageParam"]:
        result: list["ChatCompletionMessageParam"] = []
        tool_calls: list[PropMessage] = []

        def commit_tool_calls():
            if tool_calls:
                assitant: "ChatCompletionAssistantMessageParam" = {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "type": "function",
                            "id": call["usage_id"],
                            "function": {
                                "name": call["prop"].name,
                                "arguments": call["raw_params"],
                            },
                        }
                        for call in tool_calls
                    ],
                }
                result.append(assitant)
                result.extend(
                    {
                        "role": "tool",
                        "tool_call_id": tool_result["usage_id"],
                        "content": tool_result["result"],
                    }
                    for tool_result in tool_calls
                )
                tool_calls.clear()

        for message in messages:
            if message["role"] == "system":
                commit_tool_calls()
                result.append(
                    {
                        "role": "system",
                        "content": message["content"],
                    }
                )
            elif message["role"] == "user":
                commit_tool_calls()
                result.append(
                    {
                        "role": "user",
                        "content": message["content"],
                    }
                )
            elif message["role"] == "assistant":
                commit_tool_calls()
                result.append(
                    {
                        "role": "assistant",
                        "content": message["content"],
                    }
                )
            elif message["role"] == "tool":
                tool_calls.append(message)
            else:
                # This should never happen
                raise ValueError(f"Unknown message role: {message['role']}")

        commit_tool_calls()
        return result

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
    ) -> GenerateResponse:
        openai_messages = self._messages_to_openai(messages)

        tools: list["ChatCompletionToolParam"] = (
            [self._prop_to_tool(prop) for prop in props] if props else []
        )
        if props:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_format={"type": self.response_format},
                messages=openai_messages,
                tools=tools,
                tool_choice=(
                    await self.tool_choice.choose(timeline, openai_messages, props)
                ),
            )
        else:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_format={"type": self.response_format},
                messages=openai_messages,
            )

        reply = response.choices[0].message
        prop_usage: list[PropMessage] = []

        while reply.tool_calls:
            if not props:
                raise BackendError(
                    "OpenAI returned tool calls but no props were provided"
                )

            openai_messages.append(
                cast(
                    "ChatCompletionAssistantMessageParam",
                    reply.model_dump(exclude_unset=True),
                )
            )

            available_props = {prop.name: prop for prop in props}
            results = await asyncio.gather(
                *(
                    self._use_prop(
                        timeline,
                        available_props[call.function.name],
                        call.id,
                        call.function.arguments,
                    )
                    for call in reply.tool_calls
                )
            )
            prop_usage.extend(results)

            openai_messages.extend(
                cast(
                    "ChatCompletionToolMessageParam",
                    {
                        "role": "tool",
                        "tool_call_id": result["usage_id"],
                        "content": result["result"],
                    },
                )
                for result in results
            )

            if props:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    response_format={"type": self.response_format},
                    messages=openai_messages,
                    tools=tools,
                    tool_choice=(
                        await self.tool_choice.choose(timeline, openai_messages, props)
                    ),
                )
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    response_format={"type": self.response_format},
                    messages=openai_messages,
                )
            reply = response.choices[0].message

        if reply.content is None:
            raise BackendError("OpenAI did not return a text response")
        return GenerateResponse(content=reply.content, prop_usage=prop_usage)
