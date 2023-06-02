import os
from typing import List, TypeVar

from cjw.aistory.bots.Bot import Bot
from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.utilities.GptPortal import GptPortal


class GptBot(Bot):
    GptBot = TypeVar("GptBot")

    __MODEL_TRANSLATION = {
        "gpt3": "text-davinci-003",
        "gpt3.5": "gpt-3.5-turbo",
        "gpt4": "gpt-4",
    }

    @classmethod
    def of(cls, model: str = None, key: str = None, **kwargs) -> GptBot | None:
        if model is None:
            return GptBot(model="default", key=key, **kwargs)
        elif model.lower() in cls.__MODEL_TRANSLATION:
            return GptBot(model=cls.__MODEL_TRANSLATION[model], key=key, **kwargs)
        elif model.lower() in cls.__MODEL_TRANSLATION.values():
            return GptBot(model=model, key=key, **kwargs)
        else:
            return None

    def __init__(self, model: str, key: str, **kwargs):
        super().__init__(**kwargs)

        accessKey = key if key else os.environ.get("OPENAI_API_KEY")
        if not accessKey:
            raise RuntimeError("No access key was given")

        self.__model = model
        self.__portal = GptPortal.of(accessKey)

    async def respond(self, **kwargs) -> List[Utterance]:
        # TODO: Implement this
        pass

    def getModelName(self) -> str:
        return self.__model

    @classmethod
    def load(cls, file: str) -> GptBot:
        # TODO: Implement this
        pass

    @classmethod
    def loadPlaygroundHistory(cls, file: str) -> GptBot:
        # TODO: Implement this
        pass

    def save(self, file: str):
        # TODO: Implement this
        pass

    def parseConversation(self, conversation: List[str]) -> List[Utterance]:
        # TODO: Implement this
        pass

    def formatConversation(self) -> List[str]:
        # TODO: Implement this
        pass

