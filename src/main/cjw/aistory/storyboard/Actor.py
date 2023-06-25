import logging
from typing import TypeVar

from cjw.aistory.bots.GptBot import GptBot
from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.storyboard.StoryFork import StoryFork


class Actor:
    """
    Class representing an actor in the story.
    """

    Stage = TypeVar("Stage")
    logger = logging.getLogger(__qualname__)

    DEFAULT_ALTERNATIVE_DELIMITER = '###'

    def __init__(self, **kwargs):
        """
        Initializes an Actor instance.

        Args:
            **kwargs: Additional keyword arguments
        """
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

        alternativePrompt = self.__alternativePrompt(
            self.alternatives, self.alternativeDelimiter, self.branchingAlternatives
        )
        if alternativePrompt:
            self.bot.addInstruction(alternativePrompt)

        if self.conversationEnd:
            self.bot.addInstruction(f"Use {', '.join(self.conversationEnd)} if you do not expect any more follow up dialogs.")

    def setStage(self, stage: Stage):
        """
        Sets the stage for the actor.

        Args:
            stage (Stage): The stage for the actor
        """
        self.stage = stage

    @classmethod
    def __alternativePrompt(cls, alternatives: int, alternativeDelimiter: str, branchingAlternatives: bool) -> str:
        """
        Generates an instruction for GPT to generate alternatives

        Args:
            alternatives (int): Number of alternatives
            alternativeDelimiter (str): Delimiter for separating alternatives
            branchingAlternatives (bool): Whether the alternatives branch the story into different scenarios

        Returns:
            str: The alternative prompt string
        """
        if alternatives:
            separation = f"Separated the options by '{alternativeDelimiter}' only.  Do NOT add any numbering such as 'Option 1:'"
            if branchingAlternatives:
                return f"Provide at most {alternatives} alternative responses with distinct intents if possible.  {separation}"
            else:
                return f"Rephrase your answer in {alternatives} ways.  {separation}"
        return ""

    def isConversationEnd(self, act: StoryFork) -> bool:
        """
        Checks if the given story fork represents a conversation end.

        Args:
            act (StoryFork): The story fork

        Returns:
            bool: True if the story fork represents a conversation end, False otherwise
        """
        return (
                (self.tagExtractor and any([t in act.tags for t in self.conversationEnd])) or
                (not self.tagExtractor and any([t in act.utterance.content for t in self.conversationEnd]))
        )

    async def continueStory(
            self,
            lastAct: StoryFork,
            **kwargs
    ) -> None:
        """
        Continues the story based on the last story fork.

        Args:
            lastAct (StoryFork): The last story fork
            **kwargs: Additional keyword arguments
        """
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
        self.logger.info(f"{self.name}'s story line:\n{prettyStory}")

        # Clean the bot's conversation history and insert the story line as the initial context
        self.bot.cleanConversation()
        self.bot.insertConversation(storyLine)

        # If requires alternative outputs, add such instruction to the prompt for GPT
        alternativePrompt = self.__alternativePrompt(alternatives, alternativeDelimiter, branchingAlternatives)
        if alternativePrompt:
            instructions.append(alternativePrompt)

        # Give the resulting instruction to the bot
        if instructions:
            instructionPrompt = '\n'.join([f'[{i}]' for i in instructions])
            self.bot.insertConversation(instructionPrompt)

        # Generate responses from the bot
        responses = await self.bot.respond(
            delimiter=alternativeDelimiter,
            narrating=narratingInResponse,
            updateConversation=False
        )

        branches = []
        if branchingAlternatives:
            # Handle branching alternatives
            for alt in responses:
                if not narratingInResponse:
                    # If we are not narrating the story, we assume the entire section is from the bot
                    alt.speaker = self.name
                    utteranceThread = [alt]
                else:
                    # The section may include dialogs and narrations.  Parse the content into a thread of Utterances.
                    utteranceThread = Utterance.of(alt.content, delimiter=self.responseDelimiter)

                # Get the next possible actors based on the last dialog in the utterance thread
                nextActors = self.stage.getNextActors(utteranceThread)

                # Create a new story line for the alternative
                branches.append(
                    StoryFork.of(utteranceThread, nextActors, previous=lastAct, tagExtractor=self.tagExtractor)
                )
        else:
            # Handle non-branching alternatives.  The alternatives are rephrasing of the same content.
            nextActors = self.stage.getNextActors([responses[0]])

            # Create the next story fork
            nextStory = StoryFork.of(responses[0], nextActors, previous=lastAct, tagExtractor=self.tagExtractor)
            nextStory.rephrases = [a.content for a in responses[1:]]
            branches.append(nextStory)

        # Add the branches to the last story fork
        lastAct.branches += branches
