import re
from enum import Enum

from typing import List

from cjw.aistory.utilities import StringOps


class Utterance:
    NARRATOR = "NARRATOR"
    INSTRUCTION = "INSTRUCTION"

    class Creator(Enum):
        USER = 1
        AI = 2

    @classmethod
    def of(cls, s: str, creator: Creator = Creator.USER) -> List["Utterance"]:

        utterances = []

        for c in re.sub('\n+', '\n', s.strip()).split('\n'):
            # Speaker: Say something.
            m = re.match(r'([^:]+)\s*:\s*(.+)$', c)
            if m:
                utterances.append(Utterance(creator, m.group(1), m.group(2).strip()))
                continue

            # [Make up a conversation between Bob and Alice] And other narratives.
            after = c
            while after:
                before, quoted, after = StringOps.parse_first_top_level_parentheses(after, "[", "]")
                if before:
                    utterances.append(Utterance(creator, Utterance.NARRATOR, before.strip()))
                if quoted:
                    utterances.append(Utterance(creator, Utterance.INSTRUCTION, quoted.strip()[1:-1]))

        return utterances

    def __init__(self, creator: Creator, speaker: str, content: str):
        """
        Constructor
        :param creator: whether the content created by the user or responded by AI
        :param speaker: who spoke the content in the story (can be special values __NARRATOR or .__INSTRUCTION)
        :param content: the content being spoken.
        """
        self.creator = creator
        self.speaker = speaker
        self.content = content

    def isInstruction(self):
        return self.speaker == self.INSTRUCTION

    def isNarrator(self):
        return self.speaker == self.NARRATOR

    def isCharacter(self):
        return not self.isInstruction() and not self.isNarrator()

    def isByUser(self):
        return self.creator == self.Creator.USER

    def __str__(self):
        if self.isCharacter():
            return f"{self.speaker}: {self.content}"
        elif self.isInstruction():
            return f"[{self.content}]"
        else:
            return self.content
