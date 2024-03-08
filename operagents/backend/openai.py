from typing_extensions import override

import openai

from ._base import Backend


class OpenAIBackend(Backend):
    type_ = "openai"

    def __init__(self, model: str) -> None:
        super().__init__()

        self.client = openai.AsyncOpenAI()
        self.model: str = model

    @override
    async def generate(self, messages: list) -> str:
        # TODO: messages
        response = await self.client.chat.completions.create(
            model=self.model, messages=messages
        )
        reply = response.choices[0].message.content
        if reply is None:
            raise ValueError("OpenAI did not return a text response")
        return reply
