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

    def __init__(self, model: str, key: str, **kwargs):
        super().__init__(**kwargs)

        accessKey = key if key else os.environ.get("OPENAI_API_KEY")
        if not accessKey:
            raise RuntimeError("No access key was given")

        self.__model = model
        self.__portal = GptPortal.of(accessKey)

        self.__lastConversation = -1

    def __createSystemContent(self) -> str:
        content = ""

        if self.name:
            content += f"Your name is {self.name}.\n\n"

        persona = "\n".join([str(p) for p in self.personas])
        if persona:
            content += f"{persona}\n\n"

        if self.background:
            content += f"Story background:\n{self.background}\n\n"

        if self.directives:
            content += f"Instructions:\n{self.directives}\n\n"

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
        logging.basicConfig(level=logging.DEBUG)
        messages = self.__createPrompt()

        newConversation = messages if self.__lastConversation < 0 else messages[self.__lastConversation+1:]
        logging.info(f"Sending messages to OpenAI:")
        for c in newConversation:
            logging.info(f"role={c['role']}, content={c['content']}")

        responses = await self.__portal.chatCompletion(messages, temperature=0.9)

        logging.info(f"Received responses from OpenAI:")
        for r in responses:
            logging.info(f"role={r['role']}, content={r['content']}")

        utterances = []
        for r in responses:
            utterances += Utterance.of(r["content"], creator=self.__utteranceCreator(r["role"]))

        self.conversation += utterances
        self.__lastConversation = len(self.conversation)

        return utterances

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
