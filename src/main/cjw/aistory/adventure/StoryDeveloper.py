import json
from typing import TypeVar

from cjw.aistory.adventure.DevelopmentCondenser import DevelopmentCondenser
from cjw.aistory.adventure.Story import Story
from cjw.aistory.adventure.Teller import Teller
from cjw.aistory.utilities.ChatPrompt import ChatPrompt
from cjw.aistory.utilities.Protagonist import Protagonist


class StoryDeveloper(Story):
    StoryDeveloper = TypeVar("StoryDeveloper")

    DEFAULT_INSTRUCTION = """
    The {botRoleName} and the {userRoleName} will develop a story together.

    The {userRoleName} may ask the {botRoleName} for options of possible development of the story lines.  
    The {botRoleName} shall list these options in numbered items.  
    The {userRoleName} may critique the options, quoting the item number in square brackets like [1], or [2, 3], followed by teh critiques.  
    The {userRoleName} may add more instructions to steer the direction of the story.  
    The {botRoleName} shall iterate and add the {userRoleName}'s new instruction into consideration.  For example:

        {userRoleName}:
            Recommend scenarios where {name2} tried to setup a circumstance where {subjective2User} could be alone with {objectiveName1User}.

        {botRoleName}:
            1. {name2} could invite {objectiveName1Bot} to join {objective2Bot} on a project that requires intensive collaboration. 
               This could be a project that aligns with {possessiveName1Bot} interests and expertise, which would make {objective1Bot} more inclined to be a part of it. 
               The project would allow them to spend significant time together in a professional setting, but also allow for personal bonding.

            2. {name2}, knowing that {subjectiveName1Bot} is an animal lover, could arrange for them to volunteer at a local animal shelter together. 
               This would allow them to spend a whole day together, and have plenty of chances for private, one-on-one conversations as they take care of the animals.

            3. {name2} could organize a small work gathering at his house, perhaps a team barbecue or game night. 
               As the event draws to a close, {subjective2Bot} would offer to drive the others home, leaving {objectiveName1Bot} to be dropped off last, creating an opportunity for them to be alone.

        {userRoleName}:
            [3] Given {name2} was an introvert person, holding a party may be way out of his comfort zone.
            [2] This looks like a date, which {name2} would be nervous about.

            Let's develop on 1.  Make up the dialog where {name2} invites {objectiveName1User}.
            Note that {name2} is nervous speaking to {objectiveName1User}.

        {botRoleName}:
            "Hi, {name2}. What's up?" {subjectiveName1Bot} responds, {possessive1Bot} voice carries a lighthearted curiosity that makes {possessiveName2Bot} nervousness subtly ebb away.
            "Well, umm... I wanted to... eh," {name2} stammers, his racing heart interfering with his ability to construct a coherent sentence.
            {subjective2BotCap} takes another calming breath, attempting to organize his scattered thoughts. "I have a project," {subjective2Bot} begins, in a more assured tone.
            ....
    """

    DEFAULT_PRESERVED_FROM_CONDENSE = 3

    @classmethod
    def of(cls, **kwargs) -> "StoryDeveloper":
        return StoryDeveloper(**kwargs)

    def __init__(
            self,
            teller: Teller,
            protagonist2user=Protagonist.Perspective.THIRD,
            protagonist2bot=Protagonist.Perspective.THIRD,
            **kwargs
    ):
        self.protagonist2user = protagonist2user
        self.protagonist2bot = protagonist2bot
        super().__init__(teller, **kwargs)

        self.condenser = DevelopmentCondenser(teller)

    def _createInstruction(self, customized: str = None) -> str:
        p1 = Protagonist(
            "April", Protagonist.Gener.FEMALE,
            userPerspective=self.protagonist2user,
            botPerspective=self.protagonist2bot
        )

        p2 = Protagonist("Alex", Protagonist.Gener.MALE,)

        return customized or self.DEFAULT_INSTRUCTION.format(
            userRoleName=self.workingPrompt.userRoleName,
            botRoleName=self.workingPrompt.botRoleName,
            name2=p2.name,
            subjective2User=p2.getSubjective(Protagonist.View.USER),
            objectiveName1User=p1.getObjective(Protagonist.View.USER, useName=True),
            objective2Bot=p2.getObjective(Protagonist.View.BOT),
            possessiveName1Bot=p1.getPossessive(Protagonist.View.BOT, useName=True),
            objective1Bot=p1.getObjective(Protagonist.View.BOT),
            subjectiveName1Bot=p1.getSubjective(Protagonist.View.BOT, useName=True),
            subjective2Bot=p2.getSubjective(Protagonist.View.BOT),
            objectiveName1Bot=p1.getObjective(Protagonist.View.BOT, useName=True),
            possessive1Bot=p1.getPossessive(Protagonist.View.BOT),
            possessiveName2Bot=p2.getPossessive(Protagonist.View.BOT, useName=True),
            subjective2BotCap=p2.getSubjective(Protagonist.View.BOT, capitalize=True),
        )

    def _getStoryToCondense(self, prompt: ChatPrompt) -> str:
        return "\n\n".join(
            prompt.getContents(lambda m: m["role"] != prompt.systemRoleName)[:-self.preservedFromCondense]
        )

    def _getFirstUncondensedIndex(self, prompt: ChatPrompt) -> int:
        return 2 * -self.preservedFromCondense

    def getStory(self) -> str:
        return "\n\n".join(self.archivedPrompt.getContents())

    def save(self, fileName: str, **kwargs):
        properties = {
            "protagonist2user": self.protagonist2user.value,
            "protagonist2bot": self.protagonist2bot.value,
        }
        properties.update(**kwargs)

        super().save(fileName, **properties)

    @classmethod
    async def load(cls, fileName: str, engine: Teller | StoryDeveloper) -> "StoryDeveloper":
        if isinstance(engine, StoryDeveloper):
            engine = engine.teller

        with open(fileName, "r") as fd:
            properties = json.load(fd)

            cls._checkCompatibility(properties, engine)

            protagonist2user = properties.get("protagonist2user", Protagonist.Perspective.THIRD.value)
            protagonist2bot = properties.get("protagonist2bot", Protagonist.Perspective.THIRD.value)
            story = StoryDeveloper(
                engine,
                protagonist2user=Protagonist.Perspective(protagonist2user),
                protagonist2bot=Protagonist.Perspective(protagonist2bot),
            )
            await story._restore(properties)

            return story

    async def summarize(self) -> str:
        return await self.condenser.condense(self.archivedPrompt)
