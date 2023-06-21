import logging
import time
from typing import List, Dict, Callable

import aiohttp
import openai
from transformers import GPT2TokenizerFast


class GptPortal:
    class AuthenticationError(Exception):
        pass

    class ServiceNotAvailableError(Exception):
        pass

    class TooManyTokensError(Exception):
        pass

    class InvalidRequest(Exception):
        pass

    __instances: Dict[str, "GptPortal"] = dict()
    __tokenizer = None

    __DEFAULT_MODELS = {
        "completion": "text-davinci-003",
        "chatCompletion": "gpt-4",
    }

    __RETRY_INTERVAL = 1  # sec
    __SLOW_RETRY_INTERVAL = 5  # sec

    @classmethod
    def of(cls, key: str, organization: str = None) -> "GptPortal":
        if key not in cls.__instances:
            cls.__instances[key] = GptPortal(key, organization)

        return cls.__instances[key]

    def __init__(self, key: str, organization=None, access="openai"):
        self.key = key
        self.organization = organization
        self.access = access

    async def __usingOpenAI(self, function: Callable, request: dict, retries: int = 1) -> dict:

        openai.api_key = self.key
        response = None
        tries = 0

        while not response:
            try:
                return await function(**request)

            except (
                    openai.error.Timeout,
                    openai.error.ServiceUnavailableError,
                    openai.error.APIError,
                    openai.error.APIConnectionError,
            ) as e:
                logging.warning(f"Server connection error: {e}.  Retry {tries + 1}")

            except openai.error.AuthenticationError as e:
                message = f"Authentication failed: Unauthorized. {e}"
                logging.error(message)
                raise self.AuthenticationError(f"{message} (incorrect or missing API keys).")

            except openai.error.InvalidRequestError as e:
                message = f"Incorrect API request: {e}"
                logging.error(message)
                raise self.InvalidRequest(message)

            except openai.error.RateLimitError as e:
                logging.warning(f"OpenAI rate exceeds limit.  Slowing down retries. {e}")
                time.sleep(self.__SLOW_RETRY_INTERVAL - self.__RETRY_INTERVAL)

            tries += 1
            if tries > retries:
                raise self.ServiceNotAvailableError(f"OpenAI accesses failed after {tries} tries.  Please try later")

            logging.warning(f"OpenAI access failure (try {tries}).")
            time.sleep(self.__RETRY_INTERVAL)

    async def __usingHttp(self, function: str, request: dict, retries: int = 1) -> dict:

        url = f"https://api.openai.com/v1/{function}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}"
        }

        response = None
        tries = 0

        while not response:
            try:
                async with aiohttp.ClientSession() as session:
                    logging.info(f"Sending OpenAI API POST {request}")
                    async with session.post(url, headers=headers, json=request) as response:
                        results = await response.json()

                        if response.status == 200:  # Successful response
                            logging.info(f"Got response {results}")
                            return results

                        elif response.status == 400:  # Incorrect request
                            logging.error(f"Incorrect API request: {results['message']}")
                            raise self.InvalidRequest(results['message'])

                        elif response.status == 401:  # Unauthorized
                            logging.error("Authentication failed: Unauthorized")
                            raise self.AuthenticationError(
                                f"OpenAI authentication failed (incorrect or missing API keys)."
                            )

                        elif response.status == 403:  # Forbidden
                            logging.error("Authentication failed: Forbidden")
                            raise self.AuthenticationError(f"OpenAI operation not allowed.")

                        elif response.status == 429:
                            if "rate limit" in response.reason:
                                logging.warning(f"OpenAI rate exceeds limit.  Slowing down retries.")
                                time.sleep(self.__SLOW_RETRY_INTERVAL - self.__RETRY_INTERVAL)

                            else:
                                # Quota exceeded or the server is not available.
                                reason = response.reason.lower()
                                raise self.ServiceNotAvailableError(reason)

                        else:
                            logging.warning(
                                f"Unexpected error: {response.status} - {response.reason}.  Retry {tries + 1}"
                            )

            except (
                    aiohttp.ClientError,
                    aiohttp.ServerConnectionError
            ) as e:
                logging.warning(f"Server connection error: {e}.  Retry {tries + 1}")

            tries += 1
            if tries > retries:
                raise self.ServiceNotAvailableError(f"GPT-3 access failed after {tries - 1} tries.  Please try later")

            logging.warning(f"GPT-3 access failure (try {tries}).")
            time.sleep(1)

    async def completion(self, prompt: str, retries: int = 1, **kwargs) -> List[str]:

        if kwargs.get("model", "default") == "default":
            kwargs["model"] = self.__DEFAULT_MODELS["chatCompletion"]

        access = kwargs.pop("access", self.access)

        request = {
            "prompt": prompt,
            **kwargs
        }

        if access == "http":
            response = await self.__usingHttp("completions", request, retries=retries)
        elif access == "openai":
            response = await self.__usingOpenAI(openai.Completion.acreate, request, retries=retries)
        else:
            message = f"Unknown access {access}"
            logging.error(message)
            raise self.InvalidRequest(message)

        results = [r["text"].strip() for r in response["choices"]]
        return results

    async def chatCompletion(self, messages: List[dict], retries: int = 1, **kwargs) -> List[dict]:

        if kwargs.get("model", "default") == "default":
            kwargs["model"] = self.__DEFAULT_MODELS["chatCompletion"]

        access = kwargs.pop("access", self.access)

        request = {
            "messages": messages,
            **kwargs
        }

        if access == "http":
            response = await self.__usingHttp("chatCompletions", request, retries=retries)
        elif access == "openai":
            response = await self.__usingOpenAI(openai.ChatCompletion.acreate, request, retries=retries)
        else:
            message = f"Unknown access {access}"
            logging.error(message)
            raise self.InvalidRequest(message)

        results = [r["message"] for r in response["choices"]]
        results = [{"role": r.role, "content": r.content} for r in results]
        return results

    @classmethod
    def estimateTokens(cls, text: str) -> int:
        if not text:
            return 0
        if not cls.__tokenizer:
            cls.__tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

        return len(cls.__tokenizer(text)["input_ids"])
