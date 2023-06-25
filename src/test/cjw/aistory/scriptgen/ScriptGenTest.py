import asyncio
import copy
import logging
import unittest
from typing import List
from unittest.mock import patch, AsyncMock

from cjw.aistory.bots.Persona import Persona
from cjw.aistory.scriptgen.Customer import Customer
from cjw.aistory.scriptgen.Operator import Operator
from cjw.aistory.storyboard.Stage import Stage
from cjw.aistory.storyboard.StoryFork import StoryFork


class ScriptGenTest(unittest.TestCase):
    logging.basicConfig(level=logging.DEBUG)

    dialogPatches = [
        # Alice starts the conversation
        (
            "Alice: Sure, I'd be happy to help you with your toaster oven issue. Can you please provide me with more details about the problem you're experiencing? ###\n"
            "Alice: Of course, I'd be glad to assist you with your toaster oven concern. Can you kindly explain the issue you're facing so I can better understand the situation? ###\n"
            "Alice: Absolutely, I'm here to help you with any concerns regarding your toaster oven. Can you please elaborate on the issue you're encountering so I can provide the appropriate assistance?\n"),
        # Bob responded with 4 possible intents
        (
            "Bob: The timer knob on the toaster oven isn't functioning properly. It doesn't stop the toaster oven when it reaches the set time. <timer_malfunction> ###\n"
            "Bob: The glass door on the toaster oven doesn't close properly, making it difficult to keep the heat inside. <glass_door_issue> ###\n"
            "Bob: The removable tray is not fitting correctly in the toaster oven, and it causes instability when placing or removing food. <removable_tray_problem> ###\n"
            "Bob: I received the toaster oven without some of the included accessories. Specifically, the rack and the tray to hold food were not in the package. <missing_accessories>"),
        # Alice responded accordingly the Bob's 4 different issues
        (
            # <timer_malfunction>
            "Alice: I'm sorry to hear that the timer knob is not working as expected. There could be a few reasons for this issue.\n"
            "###\n"
            "Alice: It seems that the timer knob isn't functioning correctly. This might be caused by various factors.\n"
            "###\n"
            "Alice: I apologize for the inconvenience caused by the malfunctioning timer knob. There are several possible causes for this problem.\n"),
        (
            # <glass_door_issue>
            "Alice: I'm sorry to hear that the glass door isn't closing properly on your toaster oven. Let's see what we can do to fix this issue. ###\n"
            "Alice: Apologies for the inconvenience you are facing with the glass door not closing properly on your toaster oven. We'll help you find a solution for this problem. ###\n"
            "Alice: I understand it must be frustrating to have a glass door that doesn't close properly on your toaster oven. Let's work together to address this issue.\n"),
        (
            # <removable_tray_problem>
            "Alice: I apologize for the inconvenience the removable tray is causing you. There are a few potential solutions to this issue which you can try. ###\n"
            "Alice: I understand that the removable tray isn't fitting properly in the toaster oven, which is causing issues when placing or removing food. Let me offer you some potential solutions to help fix this problem. ###\n"
            "Alice: I'm sorry to hear that you're having trouble with the removable tray in your toaster oven. I have a few suggestions that may help you resolve this issue.\n"),
        (
            # <missing_accessories>
            "Alice: I'm sorry to hear that the rack and tray were missing from your toaster oven package. We can definitely help you with this issue. ###\n"
            "Alice: Oh no, I apologize for the inconvenience caused due to the missing rack and tray from your toaster oven package. We'll make sure to address this problem for you. ###\n"
            "Alice: It's unfortunate that the rack and tray are missing from your toaster oven package. Please accept our apologies, and we'll assist you in resolving this issue.\n"),
        (
            # <timer_malfunction>
            "Bob: I also noticed that the toaster oven doesn't heat up evenly. I have to rotate my food halfway through the cooking time so that it doesn't burn on one side. <uneven_heating> ###\n"
            "Bob: The exterior of the toaster oven gets extremely hot while in use, making it difficult to touch without the risk of getting burned. <exterior_too_hot> ###\n"
            "Bob: The oven's display is flickering and sometimes becomes very dim, making it hard to read the remaining cooking time. <display_issue>\n"),
        (
            # <glass_door_issue>
            "Bob: I think the hinges on the door might be misaligned. Could that be a potential cause? <door_hinge_misalignment>\n"
            "###\n"
            "Bob: The latch that keeps the door closed seems to be broken. How can I fix this? <broken_latch>\n"
            "###\n"
            "Bob: There might be an object stuck in the door, preventing it from closing. What should I do in this case? <object_blocking_door>\n"),
        (
            # <removable_tray_problem>
            "Bob: I have already tried adjusting the tray in multiple ways, but it still doesn't fit properly. What should I do next? <seeking_alternative_solution>\n"
            "###\n"
            "Bob: I don't think there's any easy fix for this issue. Can I request a replacement for the defective removable tray? <request_replacement>\n"
            "###\n"
            "Bob: Is it possible to purchase a new tray separately, in case I can't fix the issue with the current one? <inquiry_about_additional_purchase>\n"),
        (
            # <missing_accessories>
            "Bob: Thanks for helping me. I'd like to request a replacement for the missing rack and tray, since they're essential for using the toaster oven. <request_replacement> \n"
            "###\n"
            "Bob: Aside from sending me the missing rack and tray, can you recommend an alternative solution on how to use the toaster oven without these accessories? <seeking_alternative_solution> \n"
            "###\n"
            "Bob: That's unfortunate. Can you tell me if I can purchase the rack and tray separately instead of requesting for a replacement? <inquiry_about_additional_purchase>\n"),
    ]

    currentPatch = 0

    toaster = "A customer has an issue with a toaster oven that he bought.\n\n"
    "The toaster oven had a metal box, with glass door that lift up.\n"
    "It had two nobs, one to control temperature and the other for timer.\n"
    "It came with a rack and a tray to hold food.\n"
    "It had a removable bottom tray for easy cleaning.\n\n"
    "The customer called the customer support.\n\n"

    alice = Operator.of(
        name="Alice",
        background=toaster,
        role="customer support",
        conversation=(
            "[You picked up the call and greed the customer.  "
            "You do not yet know what product it is nor do you know what issue there is.]"
        ),
        protocols=[
            "<confirm_evidences_of_purchase>",
            "<obtain_payment_method>",
            "<obtain_shipment_address>",
        ]
    )

    bob = Customer.of(name="Bob", background=toaster)

    def test_basic(self):

        stage = Stage(actors=[self.alice, self.bob])

        async def mockGptResponse(messages, **kwargs):
            response = [{
                "role": "assistant",
                "content": self.dialogPatches[self.currentPatch]
            }]
            self.currentPatch += 1
            return response

        loop = asyncio.get_event_loop()

        with patch("cjw.aistory.utilities.GptPortal.GptPortal.chatCompletion", new_callable=AsyncMock) as mockResponse:
            mockResponse.side_effect = mockGptResponse

            loop.run_until_complete(stage.act(
                actors=["Alice"],
                alternatives=3,
                narratingInResponse=False,
            ))
            print(stage.story.prettyList())

            loop.run_until_complete(stage.act(
                actors=["Bob"],
                alternatives=4,
                branchingAlternatives=True,
                narratingInResponse=False,
            ))
            print(stage.story.prettyList())
            print(f"Intents: {','.join(self.bob.knownIntents)}")

            loop.run_until_complete(stage.act(
                actors=["Alice"],
                alternatives=3,
                narratingInResponse=False,
            ))
            print(stage.story.prettyList())

            loop.run_until_complete(stage.act(
                actors=["Bob"],
                alternatives=3,
                # branchingAlternatives=True,
                narratingInResponse=False,
            ))
            print(stage.story.prettyList())
            print(f"Intents: {','.join(self.bob.knownIntents)}")

        thread: List[StoryFork] = loop.run_until_complete(stage.randomThread(10))
        for t in thread:
            print(str(t))

        loop.close()

    def test_persona(self):

        alice = copy.copy(self.alice)
        alice.bot.personas = Persona.of(
            # "Alice: Sarcastic.  Alice hates her job and likes to tell mean jokes."
            # "Alice: Alice likes to speak in rhymes."
            "Alice: Alice likes to speak puns."
        )

        stage = Stage(actors=[alice, self.bob])

        loop = asyncio.get_event_loop()
        loop.run_until_complete(stage.act(actors=["Alice"]))
        thread: List[StoryFork] = loop.run_until_complete(stage.randomThread(10))
        for t in thread:
            print(str(t))

        loop.close()


if __name__ == '__main__':
    unittest.main()
