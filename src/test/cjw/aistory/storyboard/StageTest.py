import asyncio
import json
import logging
import unittest

from cjw.aistory.storyboard.Actor import Actor
from cjw.aistory.storyboard.Stage import Stage


class StageTest(unittest.TestCase):
    logging.basicConfig(level=logging.DEBUG)

    support = Actor.of(
        name="Alice",
        background="You are a customer support representative.\n\n"
                   "One of the product that you support is a toaster oven.\n"
                   "It had a metal box, with glass door that lift up.\n"
                   "It had two nobs, one to control temperature and the other for timer.\n"
                   "It had a removable tray for easy cleaning.  It came with a rack and a tray to hold food.\n\n",
        instruction="Resolutions that you are allowed to take:\n"
                    "- Return and refund if it was bought within 30 days\n"
                    "- Return and replace a broken unit if it was defected and under 1 year warranty\n"
                    "- If it was your company's mistake in the process, offer to give a coupon of less than 10% of the purchase price for the company's products."
                    "- If none of the above, say sorry to the customer and recommend a new model.\n\n"
                    "Special instruction or situation to you are enclosed in square brackets.  "
                    "For example: [You picked up the call and greed the customer.]\n\n"
                    "You may decide to enter certain protocols if they are the next logical things to do.\n"
                    "Put the name of the protocol in a pair of angle brackets.  For example: '<payment_info>'\n"
                    "The following protocols are available:\n"
                    "- payment_info: a process to collect the customer's payment information.\n"
                    "- shipping_address: a process to collect the customer's address for shipments.\n\n"
                    "You shall only speak for Alice.",
        conversation="[You picked up the call and greed the customer.  "
                     "You do not yet know what product the customer was about nor do you know what issue it is.]",
        alternatives=3,
        narratingInResponse=False,
    )

    customer = Actor.of(
        name="Bob",
        background="A customer bought a toaster oven online, he has an issue about the purchase, so he call the customer support.\n\n"
                   "Description about the toaster oven:\n"
                   "It had a metal box, with glass door that lift up.  It had two nobs, one to control temperature and the other for timer.\n"
                   "It had a removable tray for easy cleaning.  It came with a rack and a tray to hold food.",
        instruction="You are to act and speak in behalf of the customer, Bob.  Speak only for him and no one else.\n\n"
                    "Special instruction or situation to you are enclosed in square brackets.  "
                    "For example: [You picked up the phone and call their customer support.]\n\n"
                    "Put your answer in this format: <name of the customer's intent> customer's dialog example about the type.\n"
                    "For example, Bob: <temperature_control_failure> The temperature control doesn't seem to work.  It kept heating up.\n\n"
                    "If you provide multiple intents, they shall be distinct from each other."
        ,
        alternatives=3,
        alternativesBranch=True,
        narratingInResponse=False,
    )

    def test_basic(self):

        stage = Stage(
            actors=[self.support, self.customer]
        )
        # stage.previously(
        #     "Alice: Hello! Thank you for calling our customer support. My name is Alice. How may I assist you today?\n"
        #     "Bob: Hello Alice! I recently purchased a toaster oven from your website, and I am having an issue with it. I was hoping you could help me resolve the problem.\n"
        #     "Alice: I'm sorry to hear that you're experiencing an issue with your toaster oven. I'll be more than happy to help you resolve the problem. Can you please provide more details about the issue you're facing?\n"
        # )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(stage.act())
        print(stage.story.prettyList())
        loop.run_until_complete(stage.act())
        print(stage.story.prettyList())
        loop.run_until_complete(stage.act())
        print(stage.story.prettyList())
        loop.run_until_complete(stage.act())
        print(stage.story.prettyList())
        print(json.dumps(stage.getStoryBoard(), indent=4))
        loop.close()

    def test_loadSaveStory(self):
        story = """
{
    "utterance": {
        "creator": 1,
        "speaker": "INSTRUCTION",
        "content": "story_starts",
        "private": false
    },
    "nextActors": [
        "Alice"
    ],
    "branches": [
        {
            "utterance": {
                "creator": 2,
                "speaker": "Alice",
                "content": "Hello! Thank you for calling our customer support. My name is Alice. How can I help you today?",
                "private": false
            },
            "nextActors": [
                "Bob"
            ],
            "rephrases": [
                "Hi there! This is Alice from customer support. What can I assist you with today?",
                "Welcome to our customer support line. I'm Alice, and I'm here to help you. What seems to be the issue?"
            ],
            "branches": [
                {
                    "utterance": {
                        "creator": 2,
                        "speaker": "Bob",
                        "content": "<damaged_product> Hi Alice, I recently purchased a toaster oven from your online store, and it arrived with a broken glass door. I need help on how to get a replacement or a refund.",
                        "private": false
                    },
                    "nextActors": [
                        "Alice"
                    ],
                    "branches": [
                        {
                            "utterance": {
                                "creator": 2,
                                "speaker": "Alice",
                                "content": "I'm sorry to hear that your toaster oven arrived damaged. We'd be happy to help you with either a replacement or a refund. Can you please provide me with the order number and date of purchase?",
                                "private": false
                            },
                            "nextActors": [
                                "Bob"
                            ],
                            "rephrases": [
                                "Oh no, I apologize for the inconvenience. We can definitely assist you with a replacement or a refund. Kindly provide me with the order number and the purchase date so we can proceed.",
                                "I'm so sorry to hear about the broken glass door. We certainly want to make this right for you. If you could please give me your order number and the date you made the purchase, we can begin the process of either a replacement or a refund."
                            ],
                            "branches": [
                                {
                                    "utterance": {
                                        "creator": 2,
                                        "speaker": "Bob",
                                        "content": "<providing_order_information> Sure, my order number is 123456789 and the date of purchase was October 10th.",
                                        "private": false
                                    },
                                    "nextActors": [
                                        "Alice"
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "utterance": {
                        "creator": 2,
                        "speaker": "Bob",
                        "content": "<missing_parts> Hello Alice, I just received my toaster oven that I bought from your online store, but it seems to be missing the rack and tray for holding food. How can I get the missing parts?",
                        "private": false
                    },
                    "nextActors": [
                        "Alice"
                    ],
                    "branches": [
                        {
                            "utterance": {
                                "creator": 2,
                                "speaker": "Alice",
                                "content": "I'm sorry to hear that the rack and tray are missing from your toaster oven. Let me help you with that.",
                                "private": false
                            },
                            "nextActors": [
                                "Bob"
                            ],
                            "rephrases": [
                                "Oh no, I apologize for the inconvenience caused due to the missing rack and tray. Let me assist you in resolving this issue.",
                                "I apologize for the inconvenience caused by the missing rack and tray in your toaster oven. Let's work together to resolve this problem."
                            ],
                            "branches": [
                                {
                                    "utterance": {
                                        "creator": 2,
                                        "speaker": "Bob",
                                        "content": "<replacement_request> Thank you, Alice. I'd appreciate if you could send me the missing rack and tray as soon as possible, so I can fully utilize the toaster oven. What information do you need from me to arrange the replacements?",
                                        "private": false
                                    },
                                    "nextActors": [
                                        "Alice"
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "utterance": {
                        "creator": 2,
                        "speaker": "Bob",
                        "content": "<incorrect_item_received> Hi Alice, I ordered a toaster oven from your website, but when I received the package, it was a completely different item. What should I do to get the correct product?",
                        "private": false
                    },
                    "nextActors": [
                        "Alice"
                    ],
                    "branches": [
                        {
                            "utterance": {
                                "creator": 2,
                                "speaker": "Alice",
                                "content": "I apologize for the inconvenience, Bob. We will make sure to resolve this issue. First, let me confirm your order details and identify the mistake. Once that's done, we'll arrange for a return of the incorrect item and send you the correct toaster oven. Can you please provide your order number for reference?",
                                "private": false
                            },
                            "nextActors": [
                                "Bob"
                            ],
                            "rephrases": [
                                "I'm really sorry to hear that, Bob. We certainly want to correct this mistake as soon as possible. Let's start by confirming your order details, then we'll arrange for a return of the incorrect item and send you the correct toaster oven. May I have your order number, please?",
                                "Oh no, I apologize for the mix-up, Bob. We'll definitely make this right for you. First, I need to verify your order details to identify the error. Once that's done, we'll organize a return for the incorrect item and dispatch the correct toaster oven to you. Can you provide me with your order number?"
                            ],
                            "branches": [
                                {
                                    "utterance": {
                                        "creator": 2,
                                        "speaker": "Bob",
                                        "content": "<order_number_confirmation> Sure, my order number is 12345ABCDE. I appreciate your assistance in resolving this issue.",
                                        "private": false
                                    },
                                    "nextActors": [
                                        "Alice"
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}
        """
        story = json.loads(story)

        stage = Stage(actors=[self.support, self.customer]).replaceStoryBoard(story)

        loop = asyncio.get_event_loop()
        for i in range(4):
            loop.run_until_complete(stage.act())
            print(stage.story.prettyList())

        print(json.dumps(stage.getStoryBoard(), indent=4))
        loop.close()


if __name__ == '__main__':
    unittest.main()
