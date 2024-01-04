from cjw.aistory.adventure.Condenser import Condenser
from cjw.aistory.adventure.Teller import Teller
from cjw.aistory.utilities.ChatPrompt import ChatPrompt


class DevelopmentCondenser(Condenser):
    DEFAULT_REQUIREMENT_INSTRUCTION = """
    So the user and the assistant can continue their storyline discussion, list the requirements of the story so far.
    The requirements shall base on the feedbacks from the {userRoleName} to the {botRoleName}'s suggestions,
    and exclude those that have been included in the summary above.
    """

    DEFAULT_SUMMARIZE_INSTRUCTION = """
    Summarize the story development so far.
    """

    def __init__(self, teller: Teller, requirementInstruction: str = None, summarizeInstruction: str = None):
        super().__init__(teller)

        prompt = self.teller.createPrompt()
        self.requirementInstruction = requirementInstruction or self.DEFAULT_REQUIREMENT_INSTRUCTION.format(
            botRoleName=prompt.botRoleName,
            userRoleName=prompt.userRoleName,
        )
        self.instruction = summarizeInstruction or self.DEFAULT_SUMMARIZE_INSTRUCTION.format(
            botRoleName=prompt.botRoleName,
            userRoleName=prompt.userRoleName,
        )

    async def condense(self, story: str | ChatPrompt) -> str:

        prompt = self.teller.createPrompt()

        if isinstance(story, str):
            prompt.user(story)
        else:
            prompt.insert(story)

        prompt.system(self.instruction)
        summary = await self.teller.generate(prompt)

        if summary:
            result = f"Summary of story thus far:\n\n{summary}"
            prompt.delete(-2)
            prompt.system(result)
        else:
            result = ""
            prompt.delete(-1)

        prompt.system(self.requirementInstruction, replace=False)
        condensed = await self.teller.generate(prompt)

        result += f"Requirements for storyline development:\n\n{condensed}" if condensed else ""

        return result
