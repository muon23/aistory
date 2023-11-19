import json
from typing import TypeVar

from cjw.aistory.adventure.Story import Story
from cjw.aistory.adventure.Teller import Teller
from cjw.aistory.utilities.ChatPrompt import ChatPrompt
from cjw.aistory.utilities.Protagonist import Protagonist


class PolishProgressStory(Story):
    PolishProgressStory = TypeVar("PolishProgressStory")

    DEFAULT_INSTRUCTION = """
    The {userRoleName} will outline the next segment of the story, using {userPerspective}-person perspective.  
    If the {userRoleName} has special instructions to the {botRoleName}, they will be enclosed in square brackets.

    Then, the {botRoleName} shall respond with the following steps:
     1. Elaborate upon the {userRoleName}'s outline but change it to the {botPerspective}-person perspective.  
        Describe more detail about the the scenery and the characters' actions, emotions and/or sensations.
     2. The {botRoleName} shall continue with the progression of the story, making up new situations for the {userRoleName}.
     
    The User may want the assistant to give a few alternative progresses of the story.  The instruction will be included in the square brackets.
    The Assistant shall list the alternatives in a numbered list.  Do NOT generate options unless they are asked.
    A subsequent answer from the user will contain the number of the choice in square brackets.
    The assistant shall flow that branch of process and continue.

    For example:
    {userRoleName}:
        {subjectiveUser} opened the door.  There was a big bed.
        In front of the bed was a French door open to a garden.
        [What would {subjectiveUser} do next?]
    
    {botRoleName}:
        As {nameBot} slowly swing the door open, the room reveals itself to {objectiveBot}. 
        Dominating the space is a grand, king-sized bed adorned with plush pillows and a finely embroidered bedspread. 
        Sunlight pours in through the open French doors at the foot of the bed, creating a warm and inviting ambiance. 
        Through the doors, a meticulously landscaped garden beckons, its vibrant colors and fragrant blossoms enticing {objectiveBot} to step outside and explore. 
        The room itself is tastefully decorated, with elegant furnishings and artwork adorning the walls, creating a tranquil and luxurious atmosphere.
    
    {userRoleName}:
        [Give me some options.]
        
    {botRoleName}
            1. {subjectiveBotCap} are mesmerized by the garden's allure, {subjectiveBot} step closer to the open French doors, allowing a gentle breeze to caress {possessiveBot} face as {subjectiveBot} take in the breathtaking view. The garden's vibrant flowers seem to beckon, inviting {objectiveBot} to wander through their fragrant pathways.

            2. {possessiveBotCap} eyes wander around the room, drawn to a small writing desk tucked away in one corner. {subjectiveBotCap} decide to approach it, intrigued by the possibility of leaving behind a handwritten note or journaling about {possessiveBot} experience in this enchanting place.

            3. Unable to resist the allure of the plush, inviting bed, {subjectiveBot} finally give in to temptation. {subjectiveBotCap} toss {reflexiveBot} onto the soft mattress, sinking into a sea of comfort and relaxation.

    {userRoleName}:
        [3] {subjectiveUser} fast fall asleep.  {subjectiveUser} dreamt of floating in the pond in the garden.

    {botRoleName}:
        After surrendering to the allure of the plush bed, {subjectiveBot} find {reflexiveBot} succumbing to the cozy embrace of its soft blankets and pillows. The day's adventures begin to fade, and {reflexiveBot} eyes grow heavy with the promise of slumber. Before {subjectiveBot} know it, {subjectiveBot} {auxVerbPpBot} drifted into a peaceful sleep.

        In {possessiveBot} dreams, {subjectiveBot} find {reflexiveBot} transported to the garden just beyond the open French doors. {subjectiveBotCap} {auxVerbPpBot} not walking, but floating gently above the tranquil pond, surrounded by the garden's vibrant blossoms. The water beneath {objectiveBot} is cool and soothing, cradling {objectiveBot} like a loving embrace. As {subjectiveBot} float, the garden's beauty envelops {objectiveBot}, creating a surreal and serene experience. It's a dream that seems to capture the very essence of the enchanting place {subjectiveBot} {auxVerbPpBot} discovered.
    """

    DEFAULT_PRESERVED_FROM_CONDENSE = 3

    @classmethod
    def of(cls, **kwargs) -> "PolishProgressStory":
        return PolishProgressStory(**kwargs)

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

    def _createInstruction(self, customized: str = None) -> str:
        exampleProtagonist = Protagonist(
            "April", Protagonist.Gener.FEMALE,
            userPerspective=self.protagonist2user,
            botPerspective=self.protagonist2bot
        )

        return customized or self.DEFAULT_INSTRUCTION.format(
            userRoleName=self.workingPrompt.userRoleName,
            botRoleName=self.workingPrompt.botRoleName,
            userPerspective=exampleProtagonist.getPerspective(Protagonist.View.USER),
            botPerspective=exampleProtagonist.getPerspective(Protagonist.View.BOT),
            subjectiveUser=exampleProtagonist.getSubjective(Protagonist.View.USER),
            nameBot=exampleProtagonist.getSubjective(Protagonist.View.BOT, useName=True),
            objectiveBot=exampleProtagonist.getObjective(Protagonist.View.BOT),
            subjectiveBotCap=exampleProtagonist.getSubjective(Protagonist.View.BOT, capitalize=True),
            subjectiveBot=exampleProtagonist.getSubjective(Protagonist.View.BOT, capitalize=True),
            possessiveBot=exampleProtagonist.getPossessive(Protagonist.View.BOT),
            possessiveBotCap=exampleProtagonist.getPossessive(Protagonist.View.BOT, capitalize=True),
            reflexiveBot=exampleProtagonist.getReflexive(Protagonist.View.BOT),
            auxVerbPpBot=exampleProtagonist.getAuxVerbPp(Protagonist.View.BOT),
        )

    def _getStoryToCondense(self, prompt: ChatPrompt) -> str:
        return "\n\n".join(prompt.getBotContents()[:-self.preservedFromCondense])

    def _getFirstUncondensedIndex(self, prompt: ChatPrompt) -> int:
        preservedIndex = 2 * -self.preservedFromCondense
        if prompt.getRole(preservedIndex) == prompt.botRoleName:
            preservedIndex -= 1
        return preservedIndex

    def getStory(self) -> str:
        return "/n/n".join(self.archivedPrompt.getBotContents())

    def save(self, fileName: str, **kwargs):
        properties = {
            "protagonist2user": self.protagonist2user.value,
            "protagonist2bot": self.protagonist2bot.value,
        }
        properties.update(**kwargs)

        super().save(fileName, **properties)

    @classmethod
    async def load(cls, fileName: str, engine: Teller | PolishProgressStory) -> "PolishProgressStory":
        if isinstance(engine, PolishProgressStory):
            engine = engine.teller

        with open(fileName, "r") as fd:
            properties = json.load(fd)

            cls._checkCompatibility(properties, engine)

            protagonist2user = properties.get("protagonist2user", Protagonist.Perspective.THIRD.value),
            protagonist2bot = properties.get("protagonist2bot", Protagonist.Perspective.THIRD.value),
            story = PolishProgressStory(
                engine,
                protagonist2user=Protagonist.Perspective(protagonist2user),
                protagonist2bot=Protagonist.Perspective(protagonist2bot),
            )
            await story._restore(properties)

            return story

    async def _restore(self, properties):
        await super()._restore(properties)
        self.preservedFromCondense = properties.get("preservedFromCondense", self.DEFAULT_PRESERVED_FROM_CONDENSE)


