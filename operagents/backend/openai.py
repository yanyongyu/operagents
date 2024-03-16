from typing import TYPE_CHECKING
from typing_extensions import override

import openai

from operagents.prop import Prop

from ._base import Backend, Message

if TYPE_CHECKING:
    from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam


class OpenAIBackend(Backend):
    type_ = "openai"

    def __init__(self, model: str, temperature: float | None = None) -> None:
        super().__init__()

        self.client = openai.AsyncOpenAI()
        self.model: str = model
        self.temperature: float | None = temperature

    @override
    async def generate(
        self, messages: list[Message], props: list["Prop"] | None = None
    ) -> str:
        tools: list["ChatCompletionToolParam"] = (
            [
                {
                    "type": "function",
                    "function": {
                        "name": prop.name,
                        "description": prop.description,
                        "parameters": prop.params,
                    },
                }
                for prop in props
            ]
            if props
            else []
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,  # type: ignore
            tools=tools,
        )
        reply = response.choices[0].message.content
        if reply is None:
            raise ValueError("OpenAI did not return a text response")
        return reply
