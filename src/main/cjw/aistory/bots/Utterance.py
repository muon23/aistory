import copy
import enum
import re
from typing import List

from cjw.aistory.utilities import StringOps


class Utterance:
    NARRATOR = "NARRATOR"
    INSTRUCTION = "INSTRUCTION"

    class Creator(enum.Enum):
        USER = 1    # The content is created by the user
        AI = 2      # The content is created by the AI

    @classmethod
    def of(
            cls,
            contents: str | List[str] | "Utterance" | List["Utterance"],
            **kwargs
    ) -> List["Utterance"]:
        """
        Parses the contents and returns a list of Utterance objects.

        Args:
            contents (str | List[str] | "Utterance" | List["Utterance"]): Contents to parse
            **kwargs: Additional keyword arguments

        Returns:
            List["Utterance"]: List of Utterance objects
        """
        if contents is None:
            contents = ""

        creator = kwargs.get("creator", None)
        speaker = kwargs.get("speaker", None)

        if isinstance(contents, str):
            # If the contents is a string, parse it using __ofStr method
            if not creator:
                kwargs["creator"] = cls.Creator.USER
            return cls.__ofStr(contents, **kwargs)

        if isinstance(contents, Utterance):
            # If the contents is already an Utterance object, update creator and speaker if provided and return a list containing the object
            utterance = copy.copy(contents)

            # Override the creator and speaker
            if creator:
                utterance.creator = creator
            if speaker:
                utterance.speaker = speaker

            return [utterance]

        if isinstance(contents, list):
            # If the contents is a list, iterate over each item and recursively call Utterance.of to parse each item
            utterances = []
            for c in contents:
                utterances += Utterance.of(c, **kwargs)
            return utterances

        raise TypeError(f"Cannot convert {type(contents)} to Utterance")

    @classmethod
    def __ofStr(cls, contents: str, **kwargs) -> List["Utterance"]:
        """
        Parses a string and returns a list of Utterance objects.

        Args:
            contents (str): Contents to parse
            **kwargs: Additional keyword arguments

        Returns:
            List["Utterance"]: List of Utterance objects
        """
        creator = kwargs.get("creator", None)    # Content created by AI or USER

        # If the speaker is not indicated in the string (such as 'Alice: Hi!'), set the default speaker.
        defaultSpeaker = kwargs.get("speaker", None)
        if not defaultSpeaker:
            defaultSpeaker = Utterance.NARRATOR

        # The delimiter that split the string into multiple sections.  Default \n.
        delimiter = kwargs.get("delimiter", "\n")

        # Indicate whether to further parse multiple utterances between two delimiters
        parsing = kwargs.get("parsing", True)

        # Split the content by the given delimiter (default \n)
        splitContents = (
            [contents]
            if not delimiter
            else re.sub(f"({delimiter})+", delimiter, contents.strip()).split(delimiter)
        )

        utterances = []

        for c in splitContents:
            if not parsing:
                # Not to parse the text further. Deliver it as is.
                utterances.append(Utterance(creator, defaultSpeaker, c))
                continue

            # Check if it is 'Speaker: Say something or do something'.
            m = re.match(r"\s*([^:]+):(.+)\s*$", c)
            speaker, content = (m.group(1).strip(), m.group(2).strip()) if m else (defaultSpeaker, c)

            # '[]' pair are used to describe an instruction or the internal thought of a bot.
            # Here we parse them out into separate Utterances.  For example:
            # Alice: 'Not at all, please join me.' [He looks kind of cute.] 'My name is Alice, by the way'
            after = content
            while after:
                before, quoted, after = StringOps.parse_first_top_level_parentheses(after, "[", "]")
                if before:
                    utterances.append(Utterance(creator, speaker, before.strip()))
                if quoted:
                    if creator == cls.Creator.USER:
                        # If this is from a user, it is an instruction to the bot.
                        utterances.append(Utterance(creator, Utterance.INSTRUCTION, quoted.strip()[1:-1]))
                    else:
                        # If this is from AI, this is an internal thought or a non-observable actions from the bot.
                        utterances.append(
                            Utterance(creator, speaker, quoted.strip()[1:-1], private=True)
                        )

        return utterances

    def __init__(self, creator: Creator, speaker: str, content: str, private: bool = False):
        """
        Initializes an Utterance instance.

        Args:
            creator (Creator): Creator of the utterance (USER or AI)
            speaker (str): Speaker of the utterance (character name or special values NARRATOR or INSTRUCTION)
            content (str): Content of the utterance
            private (bool): Whether the utterance is private to the speaker (default: False)
        """
        self.creator = creator
        self.speaker = speaker
        self.content = content
        self.private = private

    def isInstruction(self):
        """
        Checks if the utterance is an instruction.

        Returns:
            bool: True if the utterance is an instruction, False otherwise
        """
        return self.speaker == self.INSTRUCTION

    def isNarrator(self):
        """
        Checks if the utterance is spoken by the narrator.

        Returns:
            bool: True if the utterance is spoken by the narrator, False otherwise
        """
        return self.speaker == self.NARRATOR

    def isCharacter(self):
        """
        Checks if the utterance is spoken by a character.

        Returns:
            bool: True if the utterance is spoken by a character, False otherwise
        """
        return not self.isInstruction() and not self.isNarrator()

    def isByUser(self):
        """
        Checks if the utterance is created by the user.

        Returns:
            bool: True if the utterance is created by the user, False otherwise
        """
        return self.creator == self.Creator.USER

    def __str__(self):
        """
        Returns a string representation of the utterance.

        Returns:
            str: String representation of the utterance
        """
        if self.isCharacter():
            return f"{self.speaker}: {self.content}"
        elif self.isInstruction():
            return f"[{self.content}]"
        else:
            return self.content

    def __eq__(self, other):
        """
        Compares two Utterance instances for equality.

        Args:
            other: The other Utterance instance to compare

        Returns:
            bool: True if the Utterance instances are equal, False otherwise
        """
        return (
                isinstance(other, Utterance)
                and self.creator == other.creator
                and self.speaker == other.speaker
                and self.content == other.content
                and self.private == other.private
        )
