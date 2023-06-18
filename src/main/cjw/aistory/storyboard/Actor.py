import logging
from typing import TypeVar

from cjw.aistory.bots.Bot import Bot
from cjw.aistory.bots.GptBot import GptBot
from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.storyboard.StoryFork import StoryFork


class Actor:
    Stage = TypeVar("Stage")

    DEFAULT_ALTERNATIVE_DELIMITER = '###'

    @classmethod
    def of(cls, **kwargs) -> "Actor":

        bot = GptBot.of(**kwargs)
        if not bot:
            raise ValueError(f"Unsupported bot model {kwargs.get('model')}")

        return Actor(bot, **kwargs)

    def __init__(self, bot: Bot, **kwargs):
        self.stage = None
        self.bot = bot
        self.name = bot.name
        self.alternatives = kwargs.get("alternatives", 0)
        self.alternativeDelimiter = kwargs.get("alternativeDelimiter", self.DEFAULT_ALTERNATIVE_DELIMITER)
        self.alternativesBranch = kwargs.get("alternativesBranch", False)
        self.responseDelimiter = kwargs.get("responseDelimiter", '\n')
        self.conversationEnd = kwargs.get("conversationEnd", ["<end_conversation>"])
        self.narratingInResponse = kwargs.get("narratingInResponse", True)

        alternativePrompt = self.__alternativePrompt(self.alternatives, self.alternativeDelimiter, self.alternativesBranch)
        if alternativePrompt:
            self.bot.instruction += f"\n\n{alternativePrompt}"

        if self.conversationEnd:
            self.bot.instruction += f"\n\nUse {', '.join(self.conversationEnd)} if you do not expect any more follow up dialogs."

    def setStage(self, stage: Stage):
        self.stage = stage

    @classmethod
    def __alternativePrompt(cls, alternatives: int, alternativeDelimiter: str, alternativesBranch: bool) -> str:
        if alternatives:
            separation = f"Separated the options by '{alternativeDelimiter}' only.  Do NOT add any numbering such as 'Option 1:'"
            if alternativesBranch:
                return f"Provide at most {alternatives} alternative responses with distinct intents if possible.  {separation}"
            else:
                return f"Rephrase your answer in {alternatives} ways.  {separation}"
        return ""

    async def continueStory(
            self,
            lastAct: StoryFork,
            actor: str,
            **kwargs
    ) -> None:

        instruction = kwargs.get("instruction", "")
        alternatives = kwargs.get("alternatives", 0)
        alternativeDelimiter = kwargs.get("alternativeDelimiter", self.DEFAULT_ALTERNATIVE_DELIMITER)
        alternativesBranch = kwargs.get("alternativesBranch", False)

        if lastAct.utterance.content.lower() in self.conversationEnd:
            return

        storyLine = lastAct.getStoryLine(actor)

        prettyStory = '\n'.join([str(u) for u in storyLine])
        logging.info(f"{actor}'s story line:\n{prettyStory}")

        self.bot.cleanConversation()
        self.bot.insertConversation(storyLine)

        instruction = "\n\n".join([
            instruction,
            self.__alternativePrompt(alternatives, alternativeDelimiter, alternativesBranch)
        ])

        if instruction:
            self.bot.insertConversation(f"[{instruction}]")

        alternatives = await self.bot.respond(
            delimiter=self.alternativeDelimiter,
            narrating=self.narratingInResponse
        )

        branches = []
        if self.alternativesBranch:
            for alt in alternatives:
                if not self.narratingInResponse:
                    alt.speaker = self.name
                    utteranceThread = [alt]
                else:
                    utteranceThread = Utterance.of(alt.content, delimiter=self.responseDelimiter)

                nextActors = self.stage.getNextActors(utteranceThread)
                branches.append(StoryFork.of(utteranceThread, nextActors, previous=lastAct))
        else:
            nextActors = self.stage.getNextActors([alternatives[0]])
            nextStory = StoryFork.of(alternatives[0], nextActors, previous=lastAct)
            nextStory.rephrases = [a.content for a in alternatives[1:]]
            branches.append(nextStory)

        lastAct.branches += branches
