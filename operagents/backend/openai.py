import asyncio
from typing_extensions import Self, override
from typing import TYPE_CHECKING, Literal, cast

import openai
from pydantic import ValidationError

from operagents.prop import Prop
from operagents.exception import BackendError
from operagents.utils import get_template_renderer
from operagents.config import TemplateConfig, OpenaiBackendConfig

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


class OpenAIBackend(Backend):
    type_ = "openai"

    def __init__(
        self,
        model: str,
        temperature: float | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        response_format: Literal["text", "json_object"] = "text",
        prop_validation_error_template: TemplateConfig,
    ) -> None:
        super().__init__()

        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model: str = model
        self.temperature: float | None = temperature
        self.response_format: Literal["text", "json_object"] = response_format

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
        self, messages: list[Message], props: list["Prop"] | None = None
    ) -> str:
        tools: list["ChatCompletionToolParam"] = (
            [self._prop_to_tool(prop) for prop in props] if props else []
        )
        messages_ = cast(list["ChatCompletionMessageParam"], messages)

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            response_format={"type": self.response_format},
            messages=messages_,
            tools=tools or openai.NOT_GIVEN,
            tool_choice="auto" if tools else openai.NOT_GIVEN,
        )
        reply = response.choices[0].message

        while reply.tool_calls:
            if not props:
                raise BackendError(
                    "OpenAI returned tool calls but no props were provided"
                )

            messages_.append(cast("ChatCompletionAssistantMessageParam", reply))

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
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_format={"type": self.response_format},
                messages=messages_,
                tools=tools,
            )
            reply = response.choices[0].message

        if reply.content is None:
            raise BackendError("OpenAI did not return a text response")
        return reply.content
