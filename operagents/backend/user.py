from typing_extensions import override

from noneprompt import InputPrompt, CancelledError

from operagents.prop import Prop
from operagents.log import logger
from operagents.exception import OperaFinished

from ._base import Backend, Message


class UserBackend(Backend):
    type_ = "user"

    @override
    async def generate(
        self, messages: list[Message], props: list["Prop"] | None = None
    ) -> str:
        try:
            return await InputPrompt("You: ").prompt_async()
        except CancelledError:
            await logger.ainfo("User cancelled input.")
            raise OperaFinished() from None
