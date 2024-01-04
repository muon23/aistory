from cjw.aistory.adventure.Teller import Teller


class Condenser:

    DEFAULT_INSTRUCTION = "The {botRoleName} shall condense the story given by the {userRoleName}."
    DEFAULT_LENGTH_REQUIREMENT = "The length of the condensed result shall be at least {numWords} words."

    def __init__(self, teller: Teller, folds: int = 3, instruction: str = None):
        self.teller = teller
        self.folds = folds

        prompt = self.teller.createPrompt()
        self.instruction = instruction or self.DEFAULT_INSTRUCTION.format(
            botRoleName=prompt.botRoleName,
            userRoleName=prompt.userRoleName,
        )

    async def condense(self, story: str) -> str:
        lengthRequirement = "" if self.folds <= 0 else self.DEFAULT_LENGTH_REQUIREMENT.format(
            numWords=len(story.split()) // self.folds
        )

        prompt = self.teller.createPrompt()
        prompt.system("\n".join([self.instruction, lengthRequirement]))
        prompt.user(story)
        condensed = await self.teller.generate(prompt)

        return condensed if condensed else None
