import json
from typing import List, TypeVar

from cjw.aistory.adventure.Paraphraser import Paraphraser
from cjw.aistory.adventure.Story import Story
from cjw.aistory.adventure.Teller import Teller
from cjw.aistory.utilities.ChatPrompt import ChatPrompt
from cjw.aistory.utilities.Protagonist import Protagonist
from cjw.aistory.utilities.StringOps import join_with_conjunction


class InteractiveStory(Story):
    InteractiveStory = TypeVar("InteractiveStory")

    DEFAULT_INSTRUCTION = """
    The story shall look like being told by the {userRoleName}.
    The {userRoleName} will act as {actorNamesUser}{userPerspective}.  
    If the {userRoleName} has special instructions to the {botRoleName}, they will be enclosed in square brackets.
    {responseInstruction} 
    Dialogs of the characters shall be quoted in double quote (").
    The {botRoleName} shall not act on the {userRoleName}'s character{userActorPlural} unless being instructed to do so.
    For example:
    {userRoleName}:
        {subjective1User} opened the door.  There was a big bed.
        In front of the bed was a French door open to a garden.
        "Wow, this room looks great!" {subjective1User} said.
        [Make {name2User} open the French door for {objective1User}]
    {botRoleName}:
        {refineExample}
        "I am glad you like it," as {name2Bot} opens the French door, "Do you want to come see the outside?"
        {subjective2Bot} waves {possessive2Bot} hand to {objective1Bot}.
    """

    __REFINE_INSTRUCTION = """
    The {botRoleName} shall respond in two parts:
    First, the {botRoleName} shall elaborate and rewrite upon the {userRoleName}'s outline.
    Then, the {botRoleName} must act as {actorNamesBot} in response to {userRoleName}'s character{userActorPlural}{botPerspective},
    and make up the next situation for the {userRoleName} to respond.
    (The two parts shall flow fluidly; do not interrupt the parts with any notes or part numbers.)
    """

    __NO_REFINEMENT_INSTRUCTION = """
    The {botRoleName} shall act as {actorNamesBot} and respond to the {userRoleName}'s character{userActorPlural}{botPerspective},
    and make up the next situation for the {userRoleName} to respond.
    """

    __REFINE_EXAMPLE = """As {subjective1Bot} slowly swing the door open, the room reveals itself to {objective1Bot}. 
        Dominating the space is a grand, king-sized bed adorned with plush pillows and a finely embroidered bedspread. 
        Sunlight pours in through the open French doors at the foot of the bed, creating a warm and inviting ambiance. 
        Through the doors, a meticulously landscaped garden beckons, its vibrant colors and fragrant blossoms enticing {objective1Bot} to step outside and explore.
        """

    DEFAULT_PRESERVED_FROM_CONDENSE = 3

    @classmethod
    def of(cls, **kwargs) -> "InteractiveStory":
        return InteractiveStory(**kwargs)

    def __init__(
            self,
            teller: Teller,
            userCharacters: List[Protagonist] | Protagonist,
            botCharacters: List[Protagonist] | Protagonist,
            rewrite: bool = False,
            **kwargs
    ):
        self.userCharacters = [userCharacters] if isinstance(userCharacters, Protagonist) else userCharacters
        self.botCharacters = [botCharacters] if isinstance(botCharacters, Protagonist) else botCharacters
        self.rewrite = rewrite
        super().__init__(teller, **kwargs)

    def _createInstruction(self, customized: str = None) -> str:
        userPerspective = ""
        botPerspective = ""
        userActorPlural = ""

        if len(self.userCharacters) > 1:
            userActorPlural = "s"
        elif self.userCharacters[0].userPerspective.value <= 2:
            userPerspective = f", in the {self.userCharacters[0].getPerspective(Protagonist.View.USER)}-person perspective"
            botPerspective = f", but describe the actions from {self.userCharacters[0].name}'s perspective"

        userCharacters=join_with_conjunction([c.name for c in self.userCharacters])
        botCharacters=join_with_conjunction([c.name for c in self.botCharacters])

        responseInstruction = self.__REFINE_INSTRUCTION if self.rewrite else self.__NO_REFINEMENT_INSTRUCTION
        responseInstruction = responseInstruction.format(
            userRoleName=self.workingPrompt.userRoleName,
            botRoleName=self.workingPrompt.botRoleName,
            userActorPlural=userActorPlural,
            actorNamesBot=botCharacters,
            botPerspective=botPerspective,
        )

        refineExample = self.__REFINE_EXAMPLE.format(
            subjective1Bot=self.userCharacters[0].getSubjective(Protagonist.View.BOT),
            objective1Bot=self.userCharacters[0].getObjective(Protagonist.View.BOT),
        ) if self.rewrite else ""

        return customized or self.DEFAULT_INSTRUCTION.format(
            responseInstruction=responseInstruction,
            refineExample=refineExample,
            userRoleName=self.workingPrompt.userRoleName,
            botRoleName=self.workingPrompt.botRoleName,
            userPerspective=userPerspective,
            actorNamesUser=userCharacters,
            actorNamesBot=botCharacters,
            userActorPlural=userActorPlural,
            subjective1User=self.userCharacters[0].getSubjective(Protagonist.View.USER),
            objective1User=self.userCharacters[0].getObjective(Protagonist.View.USER),
            objective2User=self.botCharacters[0].getObjective(Protagonist.View.USER),
            name1User=self.userCharacters[0].name,
            name2User=self.botCharacters[0].name,
            name2Bot=self.botCharacters[0].name,
            possessive2Bot=self.botCharacters[0].getPossessive(Protagonist.View.BOT),
            objective1Bot=self.userCharacters[0].getObjective(Protagonist.View.BOT),
            subjective2Bot=self.botCharacters[0].getSubjective(Protagonist.View.BOT),
        )

    def _getStoryToCondense(self, prompt: ChatPrompt) -> str:
        if self.rewrite:
            return "\n\n".join(prompt.getBotContents()[:-self.preservedFromCondense])
        else:
            return "\n\n".join(
                prompt.getContents(lambda m: m["role"] != prompt.systemRoleName)[:-self.preservedFromCondense]
            )

    def _getFirstUncondensedIndex(self, prompt: ChatPrompt) -> int:
        preservedIndex = 2 * -self.preservedFromCondense
        if prompt.getRole(preservedIndex) == prompt.botRoleName:
            preservedIndex -= 1
        return preservedIndex

    def getStory(self) -> str:
        return "\n\n".join(self.archivedPrompt.getContents())

    def save(self, fileName: str, **kwargs):
        properties = {
            "userCharacters": [c.toJson() for c in self.userCharacters],
            "botCharacters": [c.toJson() for c in self.botCharacters],
            "rewrite": self.rewrite,
        }
        properties.update(**kwargs)

        super().save(fileName, **properties)

    @classmethod
    async def load(cls, fileName: str, engine: Teller | InteractiveStory) -> "InteractiveStory":
        if isinstance(engine, InteractiveStory):
            engine = engine.teller

        with open(fileName, "r") as fd:
            properties = json.load(fd)

            cls._checkCompatibility(properties, engine)

            story = InteractiveStory(
                engine,
                userCharacters=[Protagonist.fromJson(c) for c in properties["userCharacters"]],
                botCharacters=[Protagonist.fromJson(c) for c in properties["botCharacters"]],
                rewrite=properties.get("rewrite", False)
            )
            await story._restore(properties)

            return story

    async def rework(self, instruction: str) -> str:

        reworkRole = self.archivedPrompt.getRole(-1)
        if not self.rewrite or reworkRole != self.archivedPrompt.botRoleName:
            return await super().rework(instruction)

        userMessage = self.archivedPrompt.getContent(-2)
        botMessage = self.archivedPrompt.getContent(-1)
        worker = Paraphraser(self.teller, userMessage, botMessage)
        return await worker.rephrase(instruction=instruction)
