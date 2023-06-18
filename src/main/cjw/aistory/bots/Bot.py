import json
import os
from abc import ABC, abstractmethod
from typing import List

from cjw.aistory.bots.Persona import Persona
from cjw.aistory.bots.Utterance import Utterance


class Bot(ABC):

    def __init__(self, **kwargs):
        self.name: str = kwargs.get("name", None)
        self.instruction: str = kwargs.get("instruction", "")
        self.background: str = kwargs.get("background", "")
        self.personas: List[Persona] = Persona.of(kwargs.get("personas", ""))
        self.scene: str = kwargs.get("scene", "")
        self.summaries: List[str] = kwargs.get("summaries", [])
        self.conversation: List[Utterance] = Utterance.of(kwargs.get("conversation", ""))
        self.initialConversationEnd = len(self.conversation)
        self.lastResponseEnd = -1

    @abstractmethod
    async def respond(self, **kwargs) -> List[Utterance]:
        """Make AI respond to the latest conversation"""
        pass

    @abstractmethod
    def getModelName(self) -> str:
        """Get the name of the AI model"""
        pass

    def insertConversation(
            self,
            contents: str | Utterance | List[str] | List[Utterance],
            index: int = -1,
            creator: Utterance.Creator = None
    ):
        """
        Insert a line to the narratives
        :param index: Position of the lines in the narrative to insert after
        :param contents: The line to add
        :param creator: Who created the content, USER or AI?
        :return: None
        """
        length = len(self.conversation)
        if index > length:
            index = length
        elif index < 0:
            index += length + 1
            if index < 0:
                index = 0

        self.conversation = self.conversation[:index] + Utterance.of(contents, creator=creator) + self.conversation[index:]

    def removeConversation(self, begin: int = -1, end: int = None) -> List[Utterance]:
        """
        Remove a line from the narratives
        :param begin: index of the first dialog to remove (default the last dialog)
        :param end: index of the first element NOT to remove (default the end of the conversation)
        :return: The line that was removed.  None if the index is out of range.
        """
        try:
            toRemove = self.conversation[begin:end]
            for c in toRemove:
                self.conversation.remove(c)
            self.lastResponseEnd -= len(toRemove)
            return toRemove

        except IndexError:
            return []

    def replaceConversation(
            self,
            contents: str | Utterance | List[str] | List[Utterance],
            begin: int = -1,
            end: int = None
    ):
        self.removeConversation(begin, end)
        self.insertConversation(contents, begin)

    def cleanConversation(self):
        self.removeConversation(begin=self.initialConversationEnd)

    def distilCleanConversation(self):
        self.removeConversation(begin=0)

    @classmethod
    def loadTo(cls, file: str, bot: "Bot"):
        with open(file, "r") as fd:
            data = json.load(fd)

        bot.deserializeFrom(data)

    def serialize(self):
        trivialFields = ["name", "instruction", "background", "scene", "summaries"]
        serialized = {f: self.__dict__[f] for f in trivialFields}
        serialized["personas"] = [p.serialize() for p in self.personas]
        serialized["conversation"] = [c.serialize() for c in self.conversation]
        return serialized

    def deserializeFrom(self, data: dict):
        trivialFields = ["name", "instruction", "background", "scene", "summaries"]
        for f in trivialFields:
            self.__dict__[f] = data[f]

        self.personas = [Persona.deserialize(p) for p in data["personas"]]
        self.conversation = [Utterance.deserialize(c) for c in data["conversation"]]

    def save(self, file: str):
        directory = os.path.dirname(file)
        if not os.path.exists(directory):
            os.makedirs(directory)

        prettyJson = json.dumps(self.serialize(), indent=4)
        with open(file, "w") as fd:
            fd.write(prettyJson)
