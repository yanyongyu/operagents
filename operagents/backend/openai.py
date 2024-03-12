from typing_extensions import override

import openai

from ._base import Backend, Message


class OpenAIBackend(Backend):
    type_ = "openai"

    def __init__(self, model: str, temperature: float | None = None) -> None:
        super().__init__()

        self.client = openai.AsyncOpenAI()
        self.model: str = model
        self.temperature: float | None = temperature

    @override
    async def generate(self, messages: list[Message]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,  # type: ignore
        )
        reply = response.choices[0].message.content
        if reply is None:
            raise ValueError("OpenAI did not return a text response")
        return reply
