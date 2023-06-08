from abc import ABC, abstractmethod
from typing import List, Optional

from cjw.aistory.bots.Persona import Persona
from cjw.aistory.bots.Utterance import Utterance


class Bot(ABC):

    def __init__(self, **kwargs):
        self.name: str = kwargs.get("name", None)
        self.directives: str = kwargs.get("directives", "")
        self.background: str = kwargs.get("background", "")
        self.personas: List[Persona] = Persona.of(kwargs.get("personas", ""))
        self.scene: str = kwargs.get("scene", "")
        self.summaries: List[str] = kwargs.get("summaries", [])
        self.conversation: List[Utterance] = Utterance.of(kwargs.get("conversation", ""))

    @abstractmethod
    async def respond(self, **kwargs) -> List[Utterance]:
        """Make AI respond to the latest conversation"""
        pass

    @abstractmethod
    def getModelName(self) -> str:
        """Get the name of the AI model"""
        pass

    def insertConversation(self, line: str | Utterance, index: int = -1, creator: Utterance.Creator = Utterance.Creator.USER):
        """
        Insert a line to the narratives
        :param index: Position of the lines in the narrative to insert after
        :param line: The line to add
        :param creator: Who created the content, USER or AI?
        :return: None
        """
        lenConversation = len(self.conversation)
        if index > lenConversation:
            index = lenConversation
        elif index < 0:
            index = lenConversation + 1 + index
        if index < 0:
            index = 0

        if isinstance(line, str):
            utterances = Utterance.of(line, creator=creator)
        elif isinstance(line, Utterance):
            utterances = [line]
        else:
            raise ValueError(f"Unsupported data type {type(line)}")

        self.conversation = self.conversation[:index] + utterances + self.conversation[index:]

    def removeConversation(self, index: int = -1) -> Optional[Utterance]:
        """
        Remove a line from the narratives
        :param index: Position of the lines in the narrative to remove
        :return: The line that was removed.  None if the index is out of range.
        """
        try:
            toRemove = self.conversation[index]
            self.conversation.remove(toRemove)
            return toRemove
        except IndexError:
            return None

    def replaceConversation(self, line: str | Utterance, index: int = -1):
        self.removeConversation(index)
        self.insertConversation(line, index)

    @classmethod
    @abstractmethod
    def load(cls, file: str):
        pass

    @abstractmethod
    def save(self, file: str):
        pass
