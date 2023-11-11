from abc import ABC, abstractmethod

from cjw.aistory.utilities.ChatPrompt import ChatPrompt


class Teller(ABC):

    class TooManyTokensError(Exception):
        """Raise when number of tokens in prompt and response exceeds the limit"""
        def __init__(self, message):
            super().__init__(message)

    @abstractmethod
    def getName(self) -> str:
        pass

    @abstractmethod
    def isCompatible(self, name: str) -> bool:
        pass

    @abstractmethod
    async def generate(self, prompt: ChatPrompt, redo: bool = True) -> str:
        pass

    @abstractmethod
    def getNumTokens(self, prompt: str | ChatPrompt) -> int:
        pass

    @abstractmethod
    def createPrompt(self) -> ChatPrompt:
        pass

