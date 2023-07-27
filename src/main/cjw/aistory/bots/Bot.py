import os
from abc import ABC, abstractmethod
from typing import List

import jsonpickle

from cjw.aistory.bots.Persona import Persona
from cjw.aistory.bots.Utterance import Utterance


class Bot(ABC):
    """
    Abstract base class representing a bot.

    Attributes:
        name (str): Name of the bot
        instruction (str): Instruction for the bot
        background (str): Background information about the environment where the bot is interacting
        personas (List[Persona]): Personas for this bot and maybe other bots that it interacts with
        scene (str): Information for the current scene where the bot is
        summaries (List[str]): A list of summaries of the previous story line of the bot
        conversation (List[Utterance]): The conversation so far in the current scene between the bot and others
    """

    def __init__(self, **kwargs):
        """
        Initializes a bot instance.

        Args:
            **kwargs: Additional keyword arguments
        """
        self.name: str = kwargs.get("name", None)
        self.instruction: str = kwargs.get("instruction", "")
        self.background: str = kwargs.get("background", "")
        self.personas: List[Persona] = Persona.of(kwargs.get("personas", ""))
        self.scene: str = kwargs.get("scene", "")
        self.summaries: List[str] = kwargs.get("summaries", [])
        self.conversation: List[Utterance] = Utterance.of(kwargs.get("conversation", ""))

        self._initialConversationEnd = len(self.conversation)
        self._lastResponseEnd = -1

    def __eq__(self, other):
        """
        Compares two bot instances for equality.

        Args:
            other: The other bot instance to compare

        Returns:
            bool: True if the bot instances are equal, False otherwise
        """
        return (
                isinstance(other, Bot) and
                self.name == other.name and
                self.instruction == other.instruction and
                self.background == other.background and
                self.personas == other.personas and
                self.scene == other.scene and
                self.conversation == other.conversation and
                self._initialConversationEnd == other._initialConversationEnd
        )

    @abstractmethod
    async def respond(self, **kwargs) -> List[Utterance]:
        """
        Abstract method for making the bot respond to the latest conversation.

        Args:
            **kwargs: Additional keyword arguments

        Returns:
            List[Utterance]: List of utterances as the bot's response
        """
        pass

    @abstractmethod
    def getModelName(self) -> str:
        """
        Abstract method for getting the name of the AI model used by the bot.

        Returns:
            str: Name of the AI model
        """
        pass

    def addInstruction(self, instruction: str):
        """
        Adds an instruction to the bot.

        Args:
            instruction (str): Instruction to add
        """
        if self.instruction:
            self.instruction += f"\n\n{instruction}"
        else:
            self.instruction = instruction

    def insertConversation(
            self,
            contents: str | Utterance | List[str] | List[Utterance],
            index: int = -1,
            creator: Utterance.Creator = None
    ):
        """
        Inserts a line to the conversation.

        Args:
            contents (str | Utterance | List[str] | List[Utterance]): Content to add
            index (int): Position to insert the content after (default: -1)
            creator (Utterance.Creator): Creator of the content (default: None)
        """
        length = len(self.conversation)
        if index > length:
            index = length
        elif index < 0:
            index += length + 1
            if index < 0:
                index = 0

        self.conversation = (
                self.conversation[:index]
                + Utterance.of(contents, creator=creator)
                + self.conversation[index:]
        )

    def removeConversation(self, begin: int = -1, end: int = None) -> List[Utterance]:
        """
        Removes a line or a range of lines from the conversation.

        Args:
            begin (int): Index of the first dialog to remove (default: -1 for the last line of the conversation)
            end (int): Index of the first element NOT to remove (default: None for the end of the conversation)

        Returns:
            List[Utterance]: The removed lines
        """
        try:
            toRemove = self.conversation[begin:end]
            for c in toRemove:
                self.conversation.remove(c)
            self._lastResponseEnd -= len(toRemove)
            return toRemove

        except IndexError:
            return []

    def replaceConversation(
            self,
            contents: str | Utterance | List[str] | List[Utterance],
            begin: int = -1,
            end: int = None
    ):
        """
        Replaces a range of lines in the conversation with new content.

        Args:
            contents (str | Utterance | List[str] | List[Utterance]): New content to replace with
            begin (int): Index of the first dialog to replace (default: -1 for the last line of the conversation)
            end (int): Index of the first element NOT to replace (default: None for the end of the conversation)
        """
        self.removeConversation(begin, end)
        self.insertConversation(contents, begin)

    def cleanConversation(self):
        """
        Removes all lines added after the initial conversation.
        """
        self.removeConversation(begin=self._initialConversationEnd)

    def distilCleanConversation(self):
        """
        Removes all lines from the conversation.
        """
        self.removeConversation(begin=0)

    def save(self, file: str, indent=4):
        """
        Saves the bot instance to a file.

        Args:
            file (str): File path
            indent (int): Indentation level for JSON serialization (default: 4)
        """
        directory = os.path.dirname(file)
        if not os.path.exists(directory):
            os.makedirs(directory)

        pickled = jsonpickle.encode(self, indent=indent)
        with open(file, "w") as fd:
            fd.write(pickled)

    @classmethod
    def load(cls, file: str) -> "Bot":
        """
        Loads a bot instance from a file.

        Args:
            file (str): File path

        Returns:
            Bot: Loaded bot instance
        """
        with open(file, "r") as fd:
            data = fd.read()

        return jsonpickle.decode(data)
