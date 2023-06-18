import copy
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
    def of(
            cls,
            contents: str | List[str] | "Utterance" | List["Utterance"],
            **kwargs
    ) -> List["Utterance"]:

        if contents is None:
            contents = ""

        creator = kwargs.get("creator", None)
        speaker = kwargs.get("speaker", None)

        if isinstance(contents, str):
            if not creator:
                kwargs["creator"] = cls.Creator.USER
            return cls.__ofStr(contents, **kwargs)

        if isinstance(contents, Utterance):
            utterance = copy.copy(contents)
            if creator:
                utterance.creator = creator
            if speaker:
                utterance.speaker = speaker
            return [utterance]

        if isinstance(contents, list):
            utterances = []
            for c in contents:
                utterances += Utterance.of(c, **kwargs)
            return utterances

        raise TypeError(f"Cannot convert {type(contents)} to Utterance")

    @classmethod
    def __ofStr(cls, contents: str, **kwargs) -> List["Utterance"]:

        creator = kwargs.get("creator", None)
        defaultSpeaker = kwargs.get("speaker", None)
        if not defaultSpeaker:
            defaultSpeaker = Utterance.NARRATOR
        delimiter = kwargs.get("delimiter", "\n")

        splitContents = [contents] if not delimiter else re.sub(f'({delimiter})+', delimiter, contents.strip()).split(delimiter)

        utterances = []

        for c in splitContents:
            # Check if it is 'Speaker: Say something or do something'.
            m = re.match(r'\s*([^:]+):(.+)\s*$', c)
            speaker, content = (m.group(1).strip(), m.group(2).strip()) if m else (defaultSpeaker, c)

            after = content
            while after:
                before, quoted, after = StringOps.parse_first_top_level_parentheses(after, "[", "]")
                if before:
                    utterances.append(Utterance(creator, speaker, before.strip()))
                if quoted:
                    if creator == Utterance.Creator.USER:
                        utterances.append(Utterance(creator, Utterance.INSTRUCTION, quoted.strip()[1:-1]))
                    else:
                        utterances.append(Utterance(creator, speaker, quoted.strip()[1:-1], private=True))

        return utterances

    def __init__(self, creator: Creator, speaker: str, content: str, private: bool = False):
        """
        Constructor
        :param creator: whether the content created by the user or responded by AI
        :param speaker: who spoke the content in the story (can be special values __NARRATOR or .__INSTRUCTION)
        :param content: the content being spoken.
        :param private: the content is only known to the speaker
        """
        self.creator = creator
        self.speaker = speaker
        self.content = content
        self.private = private

    def isInstruction(self):
        return self.speaker == self.INSTRUCTION

    def isNarrator(self):
        return self.speaker == self.NARRATOR

    def isCharacter(self):
        return not self.isInstruction() and not self.isNarrator()

    def isByUser(self):
        return self.creator == self.Creator.USER

    def serialize(self):
        return {
            "creator": self.creator.value,
            "speaker": self.speaker,
            "content": self.content,
            "private": self.private,
        }

    @classmethod
    def deserialize(cls, data: dict) -> "Utterance":
        return Utterance(
            Utterance.Creator(data["creator"]),
            data["speaker"],
            data["content"],
            private=data.get("private", None),
        )

    def __str__(self):
        if self.isCharacter():
            return f"{self.speaker}: {self.content}"
        elif self.isInstruction():
            return f"[{self.content}]"
        else:
            return self.content
