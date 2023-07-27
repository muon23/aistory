import copy
import logging
import time
from typing import List, Dict, Callable

import aiohttp
import openai
from transformers import GPT2TokenizerFast


class GptPortal:
    logger = logging.getLogger(__qualname__)  # Logger for logging messages

    class AuthenticationError(Exception):  # Custom exception for authentication errors
        pass

    class ServiceNotAvailableError(Exception):  # Custom exception for service availability errors
        pass

    class TooManyTokensError(Exception):  # Custom exception for exceeding token limit errors
        pass

    class InvalidRequest(Exception):  # Custom exception for invalid API requests
        pass

    __instances: Dict[str, "GptPortal"] = dict()  # Dictionary to store instances of GptPortal
    __tokenizer = None  # Tokenizer instance

    __DEFAULT_MODELS = {  # Dictionary of default models
        "completion": "text-davinci-003",
        "chatCompletion": "gpt-4",
    }

    __RETRY_INTERVAL = 1  # Retry interval in seconds
    __SLOW_RETRY_INTERVAL = 5  # Slow retry interval in seconds

    @classmethod
    def of(cls, key: str, organization: str = None) -> "GptPortal":
        """
        Returns an instance of GptPortal based on the provided key and organization.
        If an instance with the same key already exists, returns the existing instance.

        Args:
            key (str): API key
            organization (str): Organization (optional)

        Returns:
            GptPortal: Instance of GptPortal
        """
        if key not in cls.__instances:
            cls.__instances[key] = GptPortal(key, organization)

        return cls.__instances[key]

    def __init__(self, key: str, organization=None, access="openai"):
        """
        Initializes an instance of GptPortal.

        Args:
            key (str): API key
            organization (str): Organization (optional)
            access (str): Access mode (openai or http)
        """
        self.key = key
        self.organization = organization
        self.access = access

    async def __usingOpenAI(self, function: Callable, request: dict, retries: int = 1) -> dict:
        """
        Makes an API request using the OpenAI library.

        Args:
            function (Callable): OpenAI function to call
            request (dict): API request payload
            retries (int): Number of retries (default: 1)

        Returns:
            dict: API response
        """
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
                self.logger.warning(f"Server connection error: {e}. Retry {tries + 1}")

            except openai.error.AuthenticationError as e:
                message = f"Authentication failed: Unauthorized. {e}"
                self.logger.error(message)
                raise self.AuthenticationError(f"{message} (incorrect or missing API keys).")

            except openai.error.InvalidRequestError as e:
                message = f"Incorrect API request: {e}"
                self.logger.error(message)
                raise self.InvalidRequest(message)

            except openai.error.RateLimitError as e:
                self.logger.warning(f"OpenAI rate exceeds limit. Slowing down retries. {e}")
                time.sleep(self.__SLOW_RETRY_INTERVAL - self.__RETRY_INTERVAL)

            tries += 1
            if tries > retries:
                raise self.ServiceNotAvailableError(f"OpenAI accesses failed after {tries} tries. Please try later")

            self.logger.warning(f"OpenAI access failure (try {tries}).")
            time.sleep(self.__RETRY_INTERVAL)

    async def __usingHttp(self, function: str, request: dict, retries: int = 1) -> dict:
        """
        Makes an API request using HTTP.

        Args:
            function (str): API function to call
            request (dict): API request payload
            retries (int): Number of retries (default: 1)

        Returns:
            dict: API response
        """
        url = f"https://api.openai.com/v1/{function}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}",
        }

        response = None
        tries = 0

        while not response:
            try:
                async with aiohttp.ClientSession() as session:
                    self.logger.info(f"Sending OpenAI API POST {request}")
                    async with session.post(url, headers=headers, json=request) as response:
                        results = await response.json()

                        if response.status == 200:  # Successful response
                            self.logger.info(f"Got response {results}")
                            return results

                        elif response.status == 400:  # Incorrect request
                            self.logger.error(f"Incorrect API request: {results['message']}")
                            raise self.InvalidRequest(results["message"])

                        elif response.status == 401:  # Unauthorized
                            self.logger.error("Authentication failed: Unauthorized")
                            raise self.AuthenticationError(
                                f"OpenAI authentication failed (incorrect or missing API keys)."
                            )

                        elif response.status == 403:  # Forbidden
                            self.logger.error("Authentication failed: Forbidden")
                            raise self.AuthenticationError(f"OpenAI operation not allowed.")

                        elif response.status == 429:
                            if "rate limit" in response.reason:
                                self.logger.warning(f"OpenAI rate exceeds limit. Slowing down retries.")
                                time.sleep(self.__SLOW_RETRY_INTERVAL - self.__RETRY_INTERVAL)
                            else:
                                # Quota exceeded or the server is not available.
                                reason = response.reason.lower()
                                raise self.ServiceNotAvailableError(reason)

                        else:
                            self.logger.warning(
                                f"Unexpected error: {response.status} - {response.reason}. Retry {tries + 1}"
                            )

            except (aiohttp.ClientError, aiohttp.ServerConnectionError) as e:
                self.logger.warning(f"Server connection error: {e}. Retry {tries + 1}")

            tries += 1
            if tries > retries:
                raise self.ServiceNotAvailableError(f"GPT-3 access failed after {tries - 1} tries. Please try later")

            self.logger.warning(f"GPT-3 access failure (try {tries}).")
            time.sleep(1)

    async def completion(self, prompt: str, retries: int = 1, **kwargs) -> List[str]:
        """
        Performs text completion using GPT-3.

        Args:
            prompt (str): Input prompt
            retries (int): Number of retries (default: 1)
            **kwargs: Additional keyword arguments

        Returns:
            List[str]: List of completion results
        """
        if kwargs.get("model", "default") == "default":
            kwargs["model"] = self.__DEFAULT_MODELS["chatCompletion"]

        multiple = "n" in kwargs

        access = kwargs.pop("access", self.access)

        request = {
            "prompt": prompt,
            **kwargs,
        }

        if access == "http":
            response = await self.__usingHttp("completions", request, retries=retries)
        elif access == "openai":
            response = await self.__usingOpenAI(openai.Completion.acreate, request, retries=retries)
        else:
            message = f"Unknown access {access}"
            self.logger.error(message)
            raise self.InvalidRequest(message)

        results = [r["text"].strip() for r in response["choices"]]
        return results if multiple else results[0]

    async def chatCompletion(
            self,
            messages: List[dict],
            retries: int = 1,
            maxCompletion: int = 5,
            **kwargs
    ) -> List[dict]:
        """
        Performs chat-based text completion using GPT-3.5 or -4.
        If GPT returns an incomplete response, repeat invoking until it is complete.

        Args:
            messages (List[dict]): List of messages in chat conversation
            retries (int): Number of retries (default: 1)
            maxCompletion (int): If GPT responds incompletely due to length, try at most this to complete (default: 5)
            **kwargs: Additional keyword arguments

        Returns:
            List[dict]: List of completion results as messages
        """
        if kwargs.get("model", "default") == "default":
            kwargs["model"] = self.__DEFAULT_MODELS["chatCompletion"]

        multiple = "n" in kwargs

        async def invokeChatComplete(_messages, forceSingle=False):
            completionArgs = copy.copy(kwargs)
            access = completionArgs.pop("access", self.access)

            if forceSingle:
                completionArgs.pop("n", 1)  # Discard 'n' for the default is 1

            request = {
                "messages": _messages,
                **completionArgs,
            }

            if access == "http":
                return await self.__usingHttp("chatCompletions", request, retries=retries)
            elif access == "openai":
                return await self.__usingOpenAI(openai.ChatCompletion.acreate, request, retries=retries)
            else:
                errorMsg = f"Unknown access {access}"
                self.logger.error(errorMsg)
                raise self.InvalidRequest(errorMsg)

        response = await invokeChatComplete(messages)

        completions = [{
            "role": r["message"].role,
            "content": r["message"].content,
            "finish_reason": r["finish_reason"]
        } for r in response["choices"]]

        # Go through all the completions and see if any of them are not completed.  If so, call GPT again to complete them.
        for completion in completions:
            pieces = 1
            while completion['finish_reason'] == "length":
                conversation = messages + [
                    {"role": "assistant", "content": completion["content"]},
                    {"role": "user", "content": "[continue, but with limits]"},
                ]

                # Make the subsequent API call to continue the conversation.
                response = await invokeChatComplete(conversation, forceSingle=True)
                noChoice = response["choices"][0]
                completion["finish_reason"] = noChoice["finish_reason"]
                completion["content"] += ' ' + noChoice["message"].content

                pieces += 1
                if pieces > maxCompletion:
                    break

        return completions if multiple else completions[0]

    @classmethod
    def estimateTokens(cls, text: str) -> int:
        """
        Estimates the number of tokens in a given text.

        Args:
            text (str): Input text

        Returns:
            int: Number of tokens
        """
        if not text:
            return 0
        if not cls.__tokenizer:
            cls.__tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

        return len(cls.__tokenizer(text)["input_ids"])
