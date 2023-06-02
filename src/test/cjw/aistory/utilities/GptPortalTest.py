import asyncio
import json
import os
import unittest

import requests

from cjw.aistory.utilities.GptPortal import GptPortal


class GptPortalTest(unittest.TestCase):
    testText = """
The exploration:  The Mayflower is on a multi-generation human exploration to the exoplanet Luytan b.  It had been 260 years since the ship left the Earth.  The skeleton voyaging crew consists of all females with stable personalities, who gave birth to each others’ clones every 10 years.  When they reached the Luytan system 17 years ago, they started to breed embryos with the explorer traits every year.  It took that long to slow down and enter the orbit of Luytan b.  The explorers would land on the planet and establish bases for basic food and material productions, before the next generation of humans of both sexes can be produced and populate the planet.
The planet: Luytan b is a twin planet with its large moon b1.  They are mutually tidal locked to each other.  Its sun, Luytan, is an orange colored red dwarf.  The atmosphere has a higher concentration of oxygen and carbon dioxide, and less of nitrogen.  The gravity is 1.3 times of the Earth.  The area facing the moon is cold and dry due to the moon’s partial blockage of the sun.  The biomes are icelands, desert, and grasslands in a concentric circle facing the moon.  The opposite side from the moon is covered in thick water clouds.  Therefore, besides knowing that there is a big body of water at the far side from the moon, everything below the clouds is shrouded in mystery from the orbit.  However, there were colonies of balloon-like plants floating to the top of the clouds and somehow anchor to the ground, allowing them to photosynthesis.  
The Kagas: Kaga is an intelligent species who lived on Luytan b.  A Kaga looks like a ball of pink tentacles covered by a half dome of hard shell.  A grownup Kaga is the size of a car.   The Kaga society is in an early iron age compared to the Earth.  Kaga villages are built on the colonies of balloon plants.  Kagas use some hollow chambers of the balloon plant as houses and farm on the top of the balloon colonies.  Kagas need to maintain the buoyancy of the balloons.  They need to encourage the growth of more vacuum chambers and patch up broken ones when the population on top of the colonies grows.  All Kagas are female at birth.  When a Kaga is grown up, she joins a caravan of young Kagas who trade amongst the villages.  When she gets old, she settles in one of her favorite balloon villages, shed her hard shell, picks up farming, and becomes a male.  If a village is prosperous, young female Kagas will love to leave their eggs in the village.  The male Kagas will then pick the eggs that they like and fertilize them and the cycle continues.
    """

    async def __summarize(self, key, access="http"):
        print(f"summarizing with {key}")
        gpt = GptPortal.of(key)
        prompt = f"{self.testText}\n\n===\nSummarize the text above."
        response = await gpt.completion(prompt=prompt, retries=2, temperature=0.7, max_tokens=500, access=access)
        print(response)

    async def __summarizeN(self, n, keys, access="http"):
        if not isinstance(keys, list):
            keys = [keys]

        tasks = [
            asyncio.create_task(self.__summarize(key, access=access)) for _ in range(n) for key in keys
        ]
        await asyncio.wait(tasks)

    def test_basic(self):
        key = os.environ['OPENAI_KEY']
        print(f"Using key {key}")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__summarizeN(2, key, access="openai"))
        loop.close()

    def test_2keys(self):
        key1 = os.environ['OPENAI_KEY']
        key2 = os.environ['OPENAI_KEY2']
        print(f"Using {key1} and {key2}")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__summarizeN(2,  [key1, key2]))
        loop.close()

    def test_estimateTokens(self):
        text2test = self.testText
        n = GptPortal.estimateTokens(text2test)
        print(n)
        self.assertGreater(n, 500)

    async def runChatCompletion(self):
        messages = [
            {
                "role": "system",
                "content": """Your persona:
                - You are Max, an assistant professor in astrophysics.
                - You are outgoing and eager to share what you know.
                """,
            },
            {
                "role": "user",
                "content": """Max was in an evening networking event of an AI conference.  
                He ordered some cocktails and grab some snacks.  He saw a young lady sitting alone at a table.  
                He approaches and introduce himself.
                """,
                "name": "NARRATOR",
            },
        ]

        key = os.environ['OPENAI_KEY']
        print(f"Using key {key}")
        gpt = GptPortal.of(key)

        responses = await gpt.chatCompletion(messages, temperature=0.8)
        print(responses)

    def test_chatCompletion(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.runChatCompletion())
        loop.close()

    def test_httpAccess(self):
        url = "https://api.openai.com/v1/chat/completions"
        key = os.environ['OPENAI_KEY']
        print(f"using {key}")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello!"}]
        }

        response = requests.post(url, headers=headers, json=data)
        print(json.dumps(response.json(), indent=4))

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "What is 3+4"}]
        }

        response = requests.post(url, headers=headers, json=data)
        print(json.dumps(response.json(), indent=4))


if __name__ == '__main__':
    unittest.main()
