import json
from abc import ABC, abstractmethod
from typing import List

from cjw.aistory.adventure.Condenser import Condenser
from cjw.aistory.adventure.Teller import Teller
from cjw.aistory.utilities.ChatPrompt import ChatPrompt


class Story(ABC):

    class IncompatibleStoryTypeError(Exception):
        def __init__(self, right: str, wrong: str):
            self.message = f"Incompatible story type {wrong} ({right} expected)"

    class IncompatibleTellerTypeError(Exception):
        def __init__(self, right: str, wrong: str):
            self.message = f"Incompatible teller type {wrong} ({right} expected)"

    DEFAULT_MAX_PROMPT_TOKENS = 6500

    def __init__(
            self,
            teller: Teller,
            maxPromptTokens: int = DEFAULT_MAX_PROMPT_TOKENS,
            condenseFolds: int = 3,
    ):
        self.teller = teller
        self.condenser = Condenser(teller, condenseFolds)
        self.maxPromptTokens = maxPromptTokens

        self.workingPrompt = self.teller.createPrompt()
        self.archivedPrompt = self.teller.createPrompt()

        self.condensingFromArchive = True
        self.uncondensedMessages = 0
        self.currentPromptTokens = 0

    async def add(self, content: str, replace: bool = True) -> "Story":
        if replace and self.archivedPrompt.getRole(-1) == self.archivedPrompt.userRoleName:
            # Replacing the last user message, so adjust the accounting as if the last item was removed
            self.uncondensedMessages -= 1
            self.currentPromptTokens -= self.teller.getNumTokens(self.archivedPrompt.getContent(-1))

        self.archivedPrompt.user(content, replace=replace)
        self.workingPrompt.user(content, replace=replace)
        self.currentPromptTokens += self.teller.getNumTokens(content)
        self.uncondensedMessages += 1

        if self.currentPromptTokens > self.maxPromptTokens:
            await self.condense()

        return self

    async def replace(self, content: str, index: int = -1) -> "Story":
        self.archivedPrompt.replace(content, index)

        # reverseIndex is the index of the replaced item counted from the end, therefore, shall always be negative
        reverseIndex = index - self.archivedPrompt.length() if index >= 0 else index

        if reverseIndex < -self.uncondensedMessages:
            # The item to be replaced is already being condensed.  So we re-condense
            self.condensingFromArchive = True
            await self.condense()
        else:
            # The itme to replaced is not part of the condensed text, so we directly remove it is in the workingPrompt
            self.currentPromptTokens -= self.teller.getNumTokens(self.workingPrompt.getContent(reverseIndex))
            self.workingPrompt.replace(content, reverseIndex)
            self.currentPromptTokens += self.teller.getNumTokens(content)

            if self.currentPromptTokens > self.maxPromptTokens:
                # If the length of the prompt is over the token limit, condense earlier text
                await self.condense()

        return self

    async def insert(self, other: ChatPrompt | List[dict], at: int = None) -> "Story":
        messages = other.messages if isinstance(other, ChatPrompt) else other

        self.archivedPrompt.insert(messages, at)

        workingIndex = at - self.archivedPrompt.length() if at and at >= 0 else at

        if workingIndex and workingIndex < -self.uncondensedMessages:
            self.condensingFromArchive = True
            await self.condense()
        else:
            self.workingPrompt.insert(messages, workingIndex)
            self.uncondensedMessages += len(messages)
            self.currentPromptTokens += sum([
                self.teller.getNumTokens(self.workingPrompt.getContent(i)) for i in range(self.workingPrompt.length())
            ])

            if self.currentPromptTokens > self.maxPromptTokens:
                await self.condense()

        return self

    async def delete(self, begin: int = -1, end: int = None) -> "Story":
        self.archivedPrompt.delete(begin, end)

        workingBegin = begin - self.archivedPrompt.length() if begin >= 0 else begin
        if workingBegin < - self.uncondensedMessages:
            self.condensingFromArchive = True
            await self.condense()
        else:
            workingEnd = end - self.archivedPrompt.length() if end and end >= 0 else end if end else 0
            self.workingPrompt.delete(workingBegin, workingEnd)
            self.uncondensedMessages -= max(0, workingEnd - workingBegin)
            self.currentPromptTokens = self.teller.getNumTokens(self.workingPrompt)

        return self

    async def generate(self, redo: bool = True) -> str:

        if redo and self.archivedPrompt.getRole(-1) == self.archivedPrompt.botRoleName:
            # Remove the last generated message
            await self.delete(-1)

        try:
            response = await self.teller.generate(self.workingPrompt, redo=redo)
        except Teller.TooManyTokensError:
            await self.condense()
            response = await self.teller.generate(self.workingPrompt, redo=redo)

        self.archivedPrompt.bot(response, redo)
        self.uncondensedMessages += 1
        self.currentPromptTokens += self.teller.getNumTokens(response)

        return response

    @abstractmethod
    async def condense(self):
        pass

    @abstractmethod
    def getStory(self) -> str:
        pass

    def save(self, fileName: str, **kwargs):

        properties = {
            "type": self.__class__.__name__,
            "teller": self.teller.getName(),
            "story": self.archivedPrompt.messages,
            "maxPromptTokens": self.maxPromptTokens,
            "userRoleName": self.workingPrompt.userRoleName,
            "botRoleName": self.workingPrompt.botRoleName,
            "systemRoleName": self.workingPrompt.systemRoleName,
        }
        properties.update(**kwargs)

        pretty = json.dumps(properties, indent=4)
        with open(fileName, "w") as fd:
            fd.write(pretty)

    async def _restore(self, properties: dict):
        self.maxPromptTokens = properties.get("maxPromptTokens", self.DEFAULT_MAX_PROMPT_TOKENS)
        self.archivedPrompt = self.teller.createPrompt().insert(properties.get("story", None))
        self.workingPrompt.insert(properties.get("story", None))
        self.uncondensedMessages = self.archivedPrompt.length()
        if self.teller.getNumTokens(self.workingPrompt) > self.maxPromptTokens:
            await self.condense()

    @abstractmethod
    def setCondensed(self, condensed: str) -> "Story":
        pass

    @abstractmethod
    def getCondensed(self) -> str | None:
        pass

    def show(self, working: bool = True):
        if working:
            self.workingPrompt.show()
        else:
            self.archivedPrompt.show()
