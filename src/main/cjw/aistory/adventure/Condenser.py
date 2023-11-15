from cjw.aistory.adventure.Teller import Teller


class Condenser:

    def __init__(self, teller: Teller, folds: int):
        self.teller = teller
        self.folds = folds

    async def condense(self, story: str) -> str:

        prompt = self.teller.createPrompt()

        instruction = f"""
        The {prompt.botRoleName} shall condense the story given by the {prompt.userRoleName}.
        The length of the condensed result shall be at least {len(story.split()) // self.folds} words. 
        """
        prompt.system(instruction)
        prompt.user(story)
        condensed = await self.teller.generate(prompt)

        return condensed if condensed else None
