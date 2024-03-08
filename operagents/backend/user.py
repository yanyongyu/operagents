from typing_extensions import override

from ._base import Backend


class UserBackend(Backend):
    type_ = "user"

    @override
    async def generate(self, messages: list) -> str:
        return input("You: ")
