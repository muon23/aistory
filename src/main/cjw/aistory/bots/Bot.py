from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional

from cjw.aistory.bots.Utterance import Utterance


class Bot(ABC):

    class NarrativeType(Enum):
        """Types of narratives"""
        DIRECTIVE = 1
        BACKGROUND = 2
        PERSONAS = 3
        SCENE = 4
        SUMMARIES = 5
        CONVERSATION = 6

    def __init__(self, **kwargs):
        self.name: str = kwargs.get("name", None)
        self.directive: List[Utterance] = kwargs.get("directive", [])
        self.background: List[Utterance] = kwargs.get("background", [])
        self.personas: List[Utterance] = kwargs.get("personas", [])
        self.scene: List[Utterance] = kwargs.get("scene", [])
        self.summaries: List[Utterance] = kwargs.get("summaries", [])
        self.conversation: List[Utterance] = self.parseConversation(kwargs.get("conversation", []))

        self.narratives = {
            self.NarrativeType.DIRECTIVE: self.directive,
            self.NarrativeType.BACKGROUND: self.background,
            self.NarrativeType.PERSONAS: self.personas,
            self.NarrativeType.SCENE: self.scene,
            self.NarrativeType.SUMMARIES: self.summaries,
            self.NarrativeType.CONVERSATION: self.conversation,
        }

    @abstractmethod
    async def respond(self, **kwargs) -> List[Utterance]:
        """Make AI respond to the latest conversation"""
        pass

    @abstractmethod
    def getModelName(self) -> str:
        """Get the name of the AI model"""
        pass

    def insert(self, narrativeType: NarrativeType, index: int, line: str | Utterance):
        """
        Insert a line to the narratives
        :param narrativeType: What type of narratives to add (see :class:`Bot.NarrativeType`)
        :param index: Position of the lines in the narrative to insert after
        :param line: The line to add
        :return: None
        """
        narrative = self.narratives[narrativeType]

        if index > len(narrative):
            index = len(narrative)

        if isinstance(line, str):
            utterances = self.parseConversation([line])
        else:
            utterances = [line]

        self.narratives[narrativeType] = narrative[:index-1] + utterances + narrativeType[index:]

    def remove(self, narrativeType: NarrativeType, index: int) -> Optional[Utterance]:
        """
        Remove a line from the narratives
        :param narrativeType: What type of narratives to add (see :class:`Bot.NarrativeType`)
        :param index: Position of the lines in the narrative to remove
        :return: The line that was removed.  None if the index is out of range.
        """
        try:
            toRemove = self.narratives[narrativeType][index]
            self.narratives[narrativeType].remove(toRemove)
            return toRemove
        except IndexError:
            return None

    def replace(self, narrativeType: NarrativeType, index: int, line: str | Utterance):
        self.remove(narrativeType, index)
        self.insert(narrativeType, index, line)

    @classmethod
    @abstractmethod
    def load(cls, file: str):
        pass

    @abstractmethod
    def save(self, file: str):
        pass

    @abstractmethod
    def parseConversation(self, conversation: List[str]) -> List[Utterance]:
        """Convert a list of strings to a list of Utterances"""
        pass

    @abstractmethod
    def formatConversation(self) -> List[str]:
        """Convert a list of Utterances to a list of strings"""
        pass
