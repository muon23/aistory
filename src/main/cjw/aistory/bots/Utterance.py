class Utterance:
    __NARRATOR = "NARRATOR"
    __INSTRUCTION = "INSTRUCTION"

    def __int__(self, speaker: str, utterance: str):
        self.speaker = speaker
        self.utterance = utterance

    def isInstruction(self):
        return self.speaker == self.__INSTRUCTION

    def isNarrator(self):
        return self.speaker == self.__NARRATOR

    def isCharacter(self):
        return not self.isInstruction() and not self.isNarrator()

    def __str__(self):
        if self.isCharacter():
            return f"{self.speaker}: {self.utterance}"
        elif self.isInstruction():
            return f"[{self.utterance}]"
        else:
            return self.utterance
