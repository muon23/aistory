from cjw.aistory.adventure.Teller import Teller


class Paraphraser:
    def __init__(self, teller: Teller, original: str, firstDraft: str = None, setting: str = None):
        self.teller = teller
        self.original = original
        self.firstDraft = firstDraft
        self.setting = setting

    async def rephrase(self, instruction: str = None):
        prompt = self.teller.createPrompt()
        setting = f"""
        Story setting:
        {self.setting}
        """ if self.setting else ""

        original = f"""
        {setting}
        Rewrite and modify the text below with instructions given by the {prompt.userRoleName}.
        ===
        {self.original}
        """ if not self.firstDraft else f"""
        The first draft below was an expansion from the original outlines.
        Rewrite and modify the first draft considering the additional instructions given ny the {prompt.userRoleName}.
        
        {setting}
        
        Original outlines:
        {self.original}
        
        First Draft:
        {self.firstDraft}
        """
        prompt.system(original)

        if not instruction:
            instruction = "Please paraphrase."

        prompt.user(instruction)
        rephrased = await self.teller.generate(prompt)

        return rephrased if rephrased else None
