import json
from abc import ABC, abstractmethod
from typing import List

from cjw.aistory.adventure.Condenser import Condenser
from cjw.aistory.adventure.Paraphraser import Paraphraser
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
    DEFAULT_PRESERVED_FROM_CONDENSE = 3

    def __init__(
            self,
            teller: Teller,
            instruction: str = None,
            setting: str = None,
            maxPromptTokens: int = DEFAULT_MAX_PROMPT_TOKENS,
            condenseFolds: int = 3,
            preservedFromCondense=DEFAULT_PRESERVED_FROM_CONDENSE,
            condenseReview: bool = False,
    ):
        self.teller = teller
        self.condenser = Condenser(teller, condenseFolds)
        self.maxPromptTokens = maxPromptTokens

        self.preservedFromCondense = preservedFromCondense
        self.condenseReview = condenseReview

        self.workingPrompt = self.teller.createPrompt()
        self.archivedPrompt = self.teller.createPrompt()

        self.workingPrompt.system(self._createInstruction(instruction))
        self.currentPromptTokens = self.teller.getNumTokens(self.workingPrompt)

        self.instruction = self._createInstruction(instruction)
        self.workingPrompt.system(self.instruction)

        self.setting = setting
        if self.setting:
            self.workingPrompt.system(setting, replace=False)

        self.condensingFromArchive = True
        self.uncondensedMessages = 0
        self.currentPromptTokens = self.teller.getNumTokens(self.workingPrompt)

    @abstractmethod
    def _createInstruction(self, customized: str = None) -> str:
        pass

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

        workingBegin = begin - self.archivedPrompt.length() if begin >= 0 else begin
        if workingBegin < - self.uncondensedMessages:
            self.condensingFromArchive = True
            await self.condense()
        else:
            workingEnd = end - self.archivedPrompt.length() if end and end >= 0 else end if end else 0
            self.workingPrompt.delete(workingBegin, workingEnd)
            self.uncondensedMessages -= max(0, workingEnd - workingBegin)
            self.currentPromptTokens = self.teller.getNumTokens(self.workingPrompt)

        self.archivedPrompt.delete(begin, end)
        return self

    async def generate(self, redo: bool = True, generated: str = None) -> str:

        if redo and self.archivedPrompt.getRole(-1) == self.archivedPrompt.botRoleName:
            # Remove the last generated message
            await self.delete(-1)

        if not generated:
            try:
                response = await self.teller.generate(self.workingPrompt, redo=redo)
            except Teller.TooManyTokensError:
                await self.condense()
                response = await self.teller.generate(self.workingPrompt, redo=redo)
        else:
            response = generated
            self.workingPrompt.bot(response, redo)

        self.archivedPrompt.bot(response, redo)
        self.uncondensedMessages += 1
        self.currentPromptTokens += self.teller.getNumTokens(response)

        if self.currentPromptTokens > self.maxPromptTokens:
            await self.condense()

        return response

    @abstractmethod
    def _getStoryToCondense(self, prompt: ChatPrompt) -> str:
        pass

    @abstractmethod
    def _getFirstUncondensedIndex(self, prompt: ChatPrompt) -> int:
        pass

    @abstractmethod
    def getStory(self) -> str:
        pass

    def save(self, fileName: str, **kwargs):

        properties = {
            "type": self.__class__.__name__,
            "teller": self.teller.getName(),
            "story": self.archivedPrompt.messages,
            "uncondensedMessages": self.uncondensedMessages,
            "condensedFromArchive": self.condensingFromArchive,
            "maxPromptTokens": self.maxPromptTokens,
            "userRoleName": self.workingPrompt.userRoleName,
            "botRoleName": self.workingPrompt.botRoleName,
            "systemRoleName": self.workingPrompt.systemRoleName,
            "instruction": self.instruction,
            "setting": self.setting,
            "preservedFromCondense": self.preservedFromCondense,
        }

        condensed = self.getCondensed()
        if condensed:
            properties["condensed"] = condensed

        properties.update(**kwargs)

        pretty = json.dumps(properties, indent=4)
        with open(fileName, "w") as fd:
            fd.write(pretty)

    @classmethod
    def _checkCompatibility(cls, properties: dict, engine: Teller):
        storyType = properties.get("type", "??")
        if storyType != cls.__name__:
            raise cls.IncompatibleStoryTypeError(cls.__name__, storyType)

        tellerType = properties.get("teller", "??")
        if not engine.isCompatible(tellerType):
            raise cls.IncompatibleTellerTypeError(engine.getName(), tellerType)

    async def _restore(self, properties: dict):
        self.instruction = properties.get("instruction", None)
        self.setting = properties.get("setting", None)
        self.maxPromptTokens = properties.get("maxPromptTokens", self.DEFAULT_MAX_PROMPT_TOKENS)

        self.archivedPrompt = self.teller.createPrompt()
        self.workingPrompt = self.teller.createPrompt()

        self.workingPrompt.system(self.instruction)
        if self.setting:
            self.workingPrompt.system(self.setting, replace=False)

        self.condensingFromArchive = properties.get("condensingFromArchive", True)
        self.uncondensedMessages = properties.get("uncondensedMessages", 0)

        story = properties.get("story", [])

        condensed = properties.get("condensed", None)
        if condensed:
            # Condensed text exists, so add it and continued with uncondensed trailing messages
            self.archivedPrompt.insert(story)
            self.setCondensed(condensed)
            uncondensed = story[-self.uncondensedMessages:]
            self.workingPrompt.insert(uncondensed)
            self.currentPromptTokens = self.teller.getNumTokens(self.workingPrompt)

        else:
            # Condensed text does not exist, so add from archive one by one.
            self.currentPromptTokens = self.teller.getNumTokens(self.workingPrompt)

            for m in story:
                if m["role"] == self.archivedPrompt.userRoleName:
                    await self.add(m["content"], replace=False)
                elif m["role"] == self.archivedPrompt.botRoleName:
                    await self.generate(generated=m["content"])
                else:
                    self.archivedPrompt.system(m["content"], replace=False)
                    self.workingPrompt.system(m["content"], replace=False)

    async def condense(self):
        prompt = self.archivedPrompt if self.condensingFromArchive else self.workingPrompt
        story = self._getStoryToCondense(prompt)

        try:
            condensed = await self.condenser.condense(story)
        except Teller.TooManyTokensError as e:
            if not self.condensingFromArchive:
                # Too many tokens even condensing from condensed.
                raise Teller.TooManyTokensError(
                    f"{e}\nConsider decreasing number of messages not to condense"
                    f" (currently preservedFromCondense={self.preservedFromCondense})"
                )

            # From now on condense from the working version
            self.condensingFromArchive = False
            story = self._getStoryToCondense(self.workingPrompt)
            condensed = await self.condenser.condense(story)

        preservedIndex = self._getFirstUncondensedIndex(prompt)

        self.workingPrompt = self.teller.createPrompt()
        self.workingPrompt.system(self.instruction)
        if self.setting:
            self.workingPrompt.system(self.setting, replace=False)
        self.workingPrompt.bot(condensed)
        if self.condenseReview:
            print(condensed)

        self.workingPrompt.insert(prompt.messages[preservedIndex:])
        self.currentPromptTokens = self.teller.getNumTokens(self.workingPrompt)
        self.uncondensedMessages = -preservedIndex

    def setCondensed(self, condensed: str):
        index = 2 if self.setting else 1

        if self.uncondensedMessages >= self.workingPrompt.length() - index:
            condensed = {"role": self.workingPrompt.botRoleName, "content": condensed}
            self.workingPrompt.insert([condensed], index)
        else:
            self.workingPrompt.replace(condensed, index)

    def getCondensed(self) -> str | None:
        index = 2 if self.setting else 1
        if self.uncondensedMessages >= self.workingPrompt.length() - index:
            return None
        else:
            return self.workingPrompt.getContent(index)

    async def rework(self, instruction: str) -> str:
        message = self.archivedPrompt.getContent(-1)
        worker = Paraphraser(self.teller, message, setting=self.setting)
        return await worker.rephrase(instruction=instruction)

    def show(self, working: bool = True):
        if working:
            self.workingPrompt.show()
        else:
            self.archivedPrompt.show()
