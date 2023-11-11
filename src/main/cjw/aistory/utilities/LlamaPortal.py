from threading import Lock
from typing import List

import torch
import transformers
from transformers import AutoTokenizer


class LlamaPortal:
    @classmethod
    def of(cls, modelName: str, **kwargs) -> "LlamaPortal":
        return LlamaPortal(modelName, **kwargs)

    def __init__(self, modelName: str, **kwargs):
        self.mutex = Lock()

        self.key = kwargs.get("key", None)

        self.tokenizer = AutoTokenizer.from_pretrained(modelName, user_auth_token=self.key)
        self.pipeline = transformers.pipeline(
            task="text-generation",
            model=modelName,
            torch_dtype=torch.float16,
            device_map="auto",
        )

    async def completion(self, prompt: str, **kwargs) -> List[str]:
        self.mutex.acquire()
        sequences = self.pipeline(
            prompt,
            # do_sample=True,
            # top_k=10,
            # num_return_sequences=1,
            eos_token_id=self.tokenizer.eos_token_id,
            # max_length=200,
        )
        self.mutex.release()
        return sequences

    async def chatCompletion(self, messages: List[dict], **kwargs) -> List[dict]:
        pass

