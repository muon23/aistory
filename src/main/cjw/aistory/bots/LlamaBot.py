import logging
import os
from typing import List, TypeVar

from cjw.aistory.bots.Bot import Bot
from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.utilities.LlamaPortal import LlamaPortal


class LlamaBot(Bot):
    LlamaBot = TypeVar("LlamaBot")

    logger = logging.getLogger(__qualname__)

    __MODEL_TRANSLATION = {
        "llama2-7b": "meta-llama/Llama-2-7b-chat-hf",
        "llama2-13b": "meta-llama/Llama-2-13b-chat-hf",
        "llama2-70b": "meta-llama/Llama-2-70b-chat-hf",
    }

    @classmethod
    def of(cls, model: str = None, key: str = None, **kwargs: object) -> LlamaBot:
        if model is None:
            return LlamaBot(model="default", **kwargs).withKey(key)
        elif model.lower() in cls.__MODEL_TRANSLATION:
            return LlamaBot(model=cls.__MODEL_TRANSLATION[model], **kwargs).withKey(key)
        elif model.lower() in cls.__MODEL_TRANSLATION.values():
            return LlamaBot(model=model, **kwargs).withKey(key)
        else:
            return None

    def __init__(self, model: str | None, **kwargs):
        super().__init__(**kwargs)

        self.__model = model
        self.__portal = None

    def __eq__(self, other):
        return (
                isinstance(other, LlamaBot) and
                super().__eq__(other) and
                self.__model == other.__model
        )

    def withKey(self, key: str = None) -> "LlamaBot":
        accessKey = key if key else os.environ.get("HUGGINGFACEHUB_API_TOKEN")
        self.__portal = LlamaPortal.of(accessKey)
        return self

    def __createPrompt(self) -> List[dict]:
        # TODO: Implement this
        pass

    def __utteranceCreator(self, creator: str) -> str:
        # TODO: Implement this
        pass

    async def respond(self, **kwargs) -> List[Utterance]:
        # TODO: Refine this
        if not self.__portal:
            self.withKey()

        messages = self.__createPrompt()

        delimiter = kwargs.get("delimiter", "\n")
        narrating = kwargs.get("narrating", True)
        updateConversation = kwargs.get("updateConversation", True)

        # For displaying in the logger for troubleshooting
        newConversation = messages if self._lastResponseEnd < 0 else messages[self._lastResponseEnd + 1:]
        self.logger.info(f"Sending messages to OpenAI:")
        for c in newConversation:
            self.logger.info(f"role={c['role']}, content={c['content']}")

        responses = await self.__portal.chatCompletion(messages, temperature=0.9)

        self.logger.info(f"Received responses from OpenAI:")
        for r in responses:
            self.logger.info(f"role={r['role']}, content={r['content']}")

        utterances = []
        for r in responses:
            utterances += Utterance.of(
                r["content"],
                creator=self.__utteranceCreator(r["role"]),
                delimiter=delimiter,
                speaker=None if narrating else self.name
            )

        if updateConversation:
            self.conversation += utterances
            self.lastResponseEnd = len(self.conversation)

        return utterances

    def getModelName(self) -> str:
        return self.__model

    @classmethod
    def load(cls, file: str) -> LlamaBot:
        return super().load(file)

    def __getstate__(self):
        """Clear GptPortal so we do not reveal OpenAI API key when serialized with pickle or jsonpickle"""
        state = self.__dict__.copy()
        state["_GptBot__portal"] = None
        return state

    @classmethod
    def loadPlaygroundHistory(cls, file: str) -> LlamaBot:
        # TODO: Implement this
        pass



