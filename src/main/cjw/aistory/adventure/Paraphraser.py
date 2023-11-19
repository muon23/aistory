from cjw.aistory.adventure.Teller import Teller


class Paraphraser:
    def __init__(self, teller: Teller, original: str):
        self.teller = teller
        self.original = original

    async def rephrase(self, instruction: str = None):
        prompt = self.teller.createPrompt()

        original = f"""
        Rewrite and modify the text below with instructions given by the {prompt.userRoleName}.
        ===
        {self.original}
        """
        prompt.system(original)

        if not instruction:
            instruction = "Please paraphrase."

        prompt.user(instruction)
        rephrased = await self.teller.generate(prompt)

        return rephrased if rephrased else None
