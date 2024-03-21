import asyncio
from typing import TYPE_CHECKING, cast
from typing_extensions import Self, override

import openai
from pydantic import ValidationError

from operagents.prop import Prop
from operagents.config import OpenaiBackendConfig
from operagents.exception import BackendError, OperagentsException

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

    def __init__(self, model: str, temperature: float | None = None) -> None:
        super().__init__()

        self.client = openai.AsyncOpenAI()
        self.model: str = model
        self.temperature: float | None = temperature

    @classmethod
    @override
    def from_config(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls, config: OpenaiBackendConfig
    ) -> Self:
        return cls(model=config.model, temperature=config.temperature)

    async def _use_prop(self, prop: Prop, args: str) -> str:
        if prop.params is None:
            param = None
        else:
            try:
                param = prop.params.model_validate_json(args)
            except ValidationError as e:
                return str(e)

        try:
            return str(await prop.use(param))
        except OperagentsException:
            # bypass operagents exceptions
            raise
        except Exception as e:
            return str(e)

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
                messages=messages_,
                tools=tools,
            )
            reply = response.choices[0].message

        if reply.content is None:
            raise BackendError("OpenAI did not return a text response")
        return reply.content
