from cjw.aistory.adventure.Teller import Teller
from cjw.aistory.utilities.ChatPrompt import ChatPrompt
from cjw.aistory.utilities.GptPortal import GptPortal


class GptTeller(Teller):

    @classmethod
    def of(cls, key: str) -> "GptTeller":
        return GptTeller(GptPortal.of(key))

    def __init__(self, gpt: GptPortal):
        self.portal = gpt

    def getName(self) -> str:
        return "gpt"

    def isCompatible(self, name: str) -> bool:
        return name in [self.getName()]

    async def generate(self, prompt: ChatPrompt, redo: bool = True) -> str:

        try:
            completed = await self.portal.chatCompletion(prompt.messages)
        except GptPortal.TooManyTokensError as e:
            raise Teller.TooManyTokensError(e)

        if completed:
            completed = completed["content"]
        prompt.bot(completed, replace=redo)
        return completed

    def getNumTokens(self, prompt: str | ChatPrompt) -> int:
        if isinstance(prompt, str):
            return self.portal.estimateTokens(prompt)
        else:
            return sum(self.portal.estimateTokens(m["content"]) for m in prompt.messages)

    def createPrompt(self) -> ChatPrompt:
        return ChatPrompt(bot="assistant")


