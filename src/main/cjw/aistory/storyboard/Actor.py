import logging
from typing import TypeVar

from cjw.aistory.bots.GptBot import GptBot
from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.storyboard.StoryFork import StoryFork


class Actor:
    Stage = TypeVar("Stage")

    DEFAULT_ALTERNATIVE_DELIMITER = '###'

    def __init__(self, **kwargs):

        self.name = kwargs.get("name")

        persona = kwargs.pop("persona", None)
        if persona:
            personas = '\n'.join([kwargs.get("personas", ""), f"{self.name}: {persona}"])
            kwargs["personas"] = personas

        bot = GptBot.of(**kwargs)
        if not bot:
            raise ValueError(f"Unsupported bot model {kwargs.get('model')}")

        self.bot = bot
        self.stage = None
        self.alternatives = kwargs.get("alternatives", 0)
        self.alternativeDelimiter = kwargs.get("alternativeDelimiter", self.DEFAULT_ALTERNATIVE_DELIMITER)
        self.branchingAlternatives = kwargs.get("branchingAlternatives", False)
        self.responseDelimiter = kwargs.get("responseDelimiter", '\n')
        self.conversationEnd = kwargs.get("conversationEnd", ["<end_conversation>"])
        self.narratingInResponse = kwargs.get("narratingInResponse", True)
        self.tagExtractor = kwargs.get("tagExtractor", None)

        alternativePrompt = self.__alternativePrompt(self.alternatives, self.alternativeDelimiter, self.branchingAlternatives)
        if alternativePrompt:
            self.bot.addInstruction(alternativePrompt)

        if self.conversationEnd:
            self.bot.addInstruction(f"Use {', '.join(self.conversationEnd)} if you do not expect any more follow up dialogs.")

    def setStage(self, stage: Stage):
        self.stage = stage

    @classmethod
    def __alternativePrompt(cls, alternatives: int, alternativeDelimiter: str, branchingAlternatives: bool) -> str:
        if alternatives:
            separation = f"Separated the options by '{alternativeDelimiter}' only.  Do NOT add any numbering such as 'Option 1:'"
            if branchingAlternatives:
                return f"Provide at most {alternatives} alternative responses with distinct intents if possible.  {separation}"
            else:
                return f"Rephrase your answer in {alternatives} ways.  {separation}"
        return ""

    def isConversationEnd(self, act: StoryFork) -> bool:
        return (
                (self.tagExtractor and any([t in act.tags for t in self.conversationEnd])) or
                (not self.tagExtractor and any([t in act.utterance.content for t in self.conversationEnd]))
        )

    async def continueStory(
            self,
            lastAct: StoryFork,
            **kwargs
    ) -> None:

        instructions = kwargs.get("instructions", [])
        if isinstance(instructions, str):
            instructions = [instructions]

        alternatives = kwargs.get("alternatives", self.alternatives)
        alternativeDelimiter = kwargs.get("alternativeDelimiter", self.alternativeDelimiter)
        branchingAlternatives = kwargs.get("branchingAlternatives", self.branchingAlternatives)
        narratingInResponse = kwargs.get("narratingInResponse", self.narratingInResponse)

        if self.isConversationEnd(lastAct):
            return

        storyLine = lastAct.getStoryLine(self.name)

        prettyStory = '\n'.join([str(u) for u in storyLine])
        logging.info(f"{self.name}'s story line:\n{prettyStory}")

        self.bot.cleanConversation()
        self.bot.insertConversation(storyLine)

        alternativePrompt = self.__alternativePrompt(alternatives, alternativeDelimiter, branchingAlternatives)
        if alternativePrompt:
            instructions.append(alternativePrompt)

        if instructions:
            instructionPrompt = '\n'.join([f'[{i}]' for i in instructions])
            self.bot.insertConversation(instructionPrompt)

        responses = await self.bot.respond(
            delimiter=alternativeDelimiter,
            narrating=narratingInResponse,
            updateConversation=False
        )

        branches = []
        if branchingAlternatives:
            for alt in responses:
                if not narratingInResponse:
                    alt.speaker = self.name
                    utteranceThread = [alt]
                else:
                    utteranceThread = Utterance.of(alt.content, delimiter=self.responseDelimiter)

                nextActors = self.stage.getNextActors(utteranceThread)
                branches.append(
                    StoryFork.of(utteranceThread, nextActors, previous=lastAct, tagExtractor=self.tagExtractor)
                )
        else:
            nextActors = self.stage.getNextActors([responses[0]])
            nextStory = StoryFork.of(responses[0], nextActors, previous=lastAct, tagExtractor=self.tagExtractor)
            nextStory.rephrases = [a.content for a in responses[1:]]
            branches.append(nextStory)

        lastAct.branches += branches
