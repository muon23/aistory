import logging
import os
from typing import List, TypeVar

from cjw.aistory.bots.Bot import Bot
from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.utilities.GptPortal import GptPortal


class GptBot(Bot):
    GptBot = TypeVar("GptBot")

    logger = logging.getLogger(__name__)

    __MODEL_TRANSLATION = {
        "gpt3": "text-davinci-003",
        "gpt3.5": "gpt-3.5-turbo",
        "gpt4": "gpt-4",
    }

    @classmethod
    def of(cls, model: str = None, key: str = None, **kwargs: object) -> GptBot:
        if model is None:
            return GptBot(model="default", **kwargs).withKey(key)
        elif model.lower() in cls.__MODEL_TRANSLATION:
            return GptBot(model=cls.__MODEL_TRANSLATION[model], **kwargs).withKey(key)
        elif model.lower() in cls.__MODEL_TRANSLATION.values():
            return GptBot(model=model, **kwargs).withKey(key)
        else:
            return None

    def __init__(self, model: str | None, **kwargs):
        super().__init__(**kwargs)

        self.__model = model
        self.__portal = None

    def __eq__(self, other):
        return (
            isinstance(other, GptBot) and
            super().__eq__(other) and
            self.__model == other.__model
        )

    def withKey(self, key: str = None) -> "GptBot":
        accessKey = key if key else os.environ.get("OPENAI_API_KEY")
        if not accessKey:
            raise RuntimeError("No access key was given")
        self.__portal = GptPortal.of(accessKey)
        return self

    def __createSystemContent(self) -> str:
        content = ""

        if self.name:
            content += f"Your name is {self.name}.\n\n"

        personas = "\n".join([str(p) for p in self.personas])
        if personas:
            content += f"{personas}\n\n"

        if self.background:
            content += f"Background:\n{self.background}\n\n"

        if self.instruction:
            content += f"Instructions:\n{self.instruction}\n\n"

        summaries = "\n".join(self.summaries)
        if summaries:
            content += f"Previously:\n{summaries}\n\n"

        if self.scene:
            content += f"Scene:\n{self.scene}\n\n"

        return content

    def __createPrompt(self) -> List[dict]:

        lastRole = "system"
        content = self.__createSystemContent()
        prompt = []

        for c in self.conversation:
            role = "user" if c.isByUser() else "assistant"

            if role != lastRole:
                prompt.append({
                    "role": lastRole,
                    "content": content
                })

                content = str(c)
                lastRole = role
            else:
                content += f"\n\n{c}"

        prompt.append({
            "role": lastRole,
            "content": content
        })

        return prompt

    @classmethod
    def __utteranceCreator(cls, creator: str):
        return Utterance.Creator.USER if creator == "user" else Utterance.Creator.AI

    async def respond(self, **kwargs) -> List[Utterance]:
        if not self.__portal:
            self.withKey()

        messages = self.__createPrompt()

        delimiter = kwargs.get("delimiter", "\n")
        narrating = kwargs.get("narrating", True)
        updateConversation = kwargs.get("updateConversation", True)

        # For displaying in the logger for troubleshooting
        newConversation = messages if self.lastResponseEnd < 0 else messages[self.lastResponseEnd + 1:]
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
    def load(cls, file: str) -> GptBot:
        return super().load(file)

    def __getstate__(self):
        """Clear GptPortal so we do not reveal OpenAI API key when serialized with pickle or jsonpickle"""
        state = self.__dict__.copy()
        state["_GptBot__portal"] = None
        return state

    @classmethod
    def loadPlaygroundHistory(cls, file: str) -> GptBot:
        # TODO: Implement this
        pass



