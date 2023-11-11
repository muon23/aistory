import asyncio
import os.path
import unittest
from unittest.mock import patch, AsyncMock

from cjw.aistory.adventure.GptTeller import GptTeller
from cjw.aistory.adventure.PolishProgressStory import PolishProgressStory
from cjw.aistory.adventure.Story import Story
from cjw.aistory.utilities.Protagonist import Protagonist


class StoryTest(unittest.TestCase):

    nextStep = 0

    @classmethod
    async def runStory(cls, story: Story, steps: int = 1):
        for i in range(steps):
            await story.add(f"user {i + cls.nextStep}")
            await story.generate()

        cls.nextStep += steps
        return story.workingPrompt

    def test_basic(self):
        patchIndex = 0

        MAX_PROMPT_TOKENS = 1000
        TEST_DIR = f"../../../../../data/test/{self.__class__.__name__}"

        async def mockGptResponse(messages, **kwargs):
            nonlocal patchIndex

            response = f"response {patchIndex} for [{messages[-1]['content'][:20]}]"
            patchIndex += 1
            return {
                "role:": "assistant",
                "content": response,
            }

        with patch(
                "cjw.aistory.utilities.GptPortal.GptPortal.chatCompletion",
                new_callable=AsyncMock
                ) as mockResponse:
            mockResponse.side_effect = mockGptResponse

            teller = GptTeller.of("abcdefg")
            story = PolishProgressStory(
                teller,
                protagonist2bot=Protagonist.Perspective.SECOND,
                protagonist2user=Protagonist.Perspective.FIRST,
                maxPromptTokens=MAX_PROMPT_TOKENS,
                preservedFromCondense=2
            )

            print(story.instruction)

            loop = asyncio.get_event_loop()
            prompt = loop.run_until_complete(self.runStory(story, steps=5))

            self.assertEqual(prompt.getContent(2), "response 0 for [user 0]")
            self.assertEqual(prompt.getContent(9), "user 4")

            promptTokens = story.teller.getNumTokens(story.workingPrompt)
            print(promptTokens)
            self.assertLess(promptTokens, MAX_PROMPT_TOKENS)

            mockResponse.reset_mock()
            prompt = loop.run_until_complete(self.runStory(story, steps=5))
            self.assertTrue(prompt.getContent(1).startswith("response 8"))  # Condensed summary
            self.assertEqual(prompt.getRole(1), "assistant")
            self.assertTrue("response 9" in prompt.getContent(7))  # No longer 'user 4'


            promptTokens = story.teller.getNumTokens(story.workingPrompt)
            print(promptTokens)
            self.assertLess(promptTokens, MAX_PROMPT_TOKENS)  # Proof still not exceed max tokens due to condensation

            # Test saving and loading
            file = f"{TEST_DIR}/test_basic.json"
            if not os.path.exists(TEST_DIR):
                os.makedirs(TEST_DIR)
            story.save(file)

            story2 = loop.run_until_complete(PolishProgressStory.load(file, teller))

            print(f"after load: {story2.currentPromptTokens} vs {story2.teller.getNumTokens(story2.workingPrompt)}")

            prompt = story2.workingPrompt
            self.assertTrue(prompt.getContent(1).startswith("response 11"))  # Condensed summary
            self.assertEqual(prompt.getRole(1), "assistant")
            self.assertTrue("response 10" in prompt.getContent(7))  # No longer 'user 4'

            self.assertTrue(all([
                m1["content"] == m2["content"]
                for m1, m2 in zip(story.archivedPrompt.messages, story2.archivedPrompt.messages)
            ]))

            # Test redo in generate()
            loop.run_until_complete(story2.generate())
            self.assertTrue("response 12" in prompt.getContent(7))  # replaced last response
            loop.run_until_complete(story2.generate(redo=False))
            self.assertTrue("response 13" in prompt.getContent(8))  # add response regardless

            print(f"after generate: {story2.currentPromptTokens} vs {story2.teller.getNumTokens(story2.workingPrompt)}")
            self.assertEqual(story2.currentPromptTokens, story2.teller.getNumTokens(story2.workingPrompt))

            # Test replace in add()
            loop.run_until_complete(story2.add("new 1"))
            loop.run_until_complete(story2.add("new 2"))
            self.assertEqual(prompt.getContent(9), "new 2")  # this shall replace previous
            loop.run_until_complete(story2.add("new 3", replace=False))
            self.assertEqual(prompt.getContent(10), "new 3")  # this shall add on top of last user message

            # Testing delete
            loop.run_until_complete(story.delete(-2))
            print(f"after delete(-2): {story.currentPromptTokens} vs {story.teller.getNumTokens(story.workingPrompt)}")
            self.assertEqual(story.workingPrompt.length(), 8)  # was 10, after deleted 2 last ones
            self.assertEqual(story.archivedPrompt.length(), 18)  # was 20, after deleted 2 last ones

            self.assertTrue("response 8" in story.workingPrompt.getContent(1))  # Old condensed text
            loop.run_until_complete(story.delete(3, 5))
            self.assertEqual(story.archivedPrompt.length(), 16)
            print(f"after delete(3,4): {story.currentPromptTokens} vs {story.teller.getNumTokens(story.workingPrompt)}")
            self.assertTrue("response 14" in story.workingPrompt.getContent(1))  # New condensed text

            self.assertEqual(story.currentPromptTokens, story.teller.getNumTokens(story.workingPrompt))

            # Test Insert
            newMessage = {"role": "test", "content": "test insert"}
            loop.run_until_complete(story.insert([newMessage]))
            self.assertEqual(story.archivedPrompt.length(), 17)
            self.assertEqual(story.archivedPrompt.getRole(-1), "test")
            self.assertEqual(story.workingPrompt.getRole(-1), "test")
            self.assertEqual(story.currentPromptTokens, story.teller.getNumTokens(story.workingPrompt))

            loop.run_until_complete(story.insert([newMessage, newMessage], 4))
            self.assertEqual(story.archivedPrompt.length(), 19)
            self.assertEqual(story.archivedPrompt.getRole(5), "test")
            self.assertTrue("response 16" in story.workingPrompt.getContent(1))  # Insert to a condensed text, re-condense triggered

            story.show()


if __name__ == '__main__':
    unittest.main()
