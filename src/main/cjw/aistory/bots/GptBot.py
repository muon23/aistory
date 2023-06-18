import logging
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
    def of(cls, model: str = None, key: str = None, **kwargs: object) -> GptBot:
        if model is None:
            return GptBot(model="default", key=key, **kwargs)
        elif model.lower() in cls.__MODEL_TRANSLATION:
            return GptBot(model=cls.__MODEL_TRANSLATION[model], key=key, **kwargs)
        elif model.lower() in cls.__MODEL_TRANSLATION.values():
            return GptBot(model=model, key=key, **kwargs)
        else:
            return None

    def __init__(self, model: str | None, key: str | None = None, **kwargs):
        super().__init__(**kwargs)

        self.__model = model
        self.__portal = None

        if model:
            # If model is None, this object is created by the load() function
            self.withKey(key)

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

        persona = "\n".join([str(p) for p in self.personas])
        if persona:
            content += f"{persona}\n\n"

        if self.background:
            content += f"Story background:\n{self.background}\n\n"

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
        logging.info(f"Sending messages to OpenAI:")
        for c in newConversation:
            logging.info(f"role={c['role']}, content={c['content']}")

        responses = await self.__portal.chatCompletion(messages, temperature=0.9)

        logging.info(f"Received responses from OpenAI:")
        for r in responses:
            logging.info(f"role={r['role']}, content={r['content']}")

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
        bot = GptBot(None)

        super().loadTo(file, bot)
        return bot

    def serialize(self):
        serialized = super().serialize()
        serialized["__model"] = self.__model
        return serialized

    def deserializeFrom(self, data: dict) :
        super().deserializeFrom(data)
        self.__model = data["__model"]

    @classmethod
    def loadPlaygroundHistory(cls, file: str) -> GptBot:
        # TODO: Implement this
        pass

