import asyncio
import json
import logging
import unittest
from unittest.mock import patch, AsyncMock, Mock

from cjw.aistory.bots.GptBot import GptBot
from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.storyboard.Actor import Actor
from cjw.aistory.storyboard.Stage import Stage
from cjw.aistory.storyboard.StoryFork import StoryFork
from cjw.aistory.storyboard.TagExtractor import TagExtractor


class StageTest(unittest.TestCase):
    logging.basicConfig(level=logging.DEBUG)

    support = Actor(
        name="Alice",
        background="You are a customer support representative.  I'll be the customer.\n\n"
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
                    "You may decide to enter certain procedure if it is the next logical things to do.\n"
                    "Put the name of the procedure in a pair of angle brackets.\n"
                    "For example, if you put down '<payment_info>', "
                    "You mean that you and the customer have gone through the conversation to obtain his payment information.\n"
                    "In addition to <payment_info>, the following process are also available:\n"
                    "<shipping_address>: to obtain the customer's shipping address.\n\n",
        conversation="[You picked up the call and greed the customer.  "
                     "You do not yet know what product the customer was about nor do you know what issue it is.]",
    )

    customer = Actor(
        name="Bob",
        background="A customer bought a toaster oven online, he has an issue about the purchase, so he call the customer support.\n\n"
                   "Description about the toaster oven:\n"
                   "It had a metal box, with glass door that lift up.  It had two nobs, one to control temperature and the other for timer.\n"
                   "It had a removable tray for easy cleaning.  It came with a rack and a tray to hold food.",
        instruction="You are to act and speak in behalf of the customer, Bob.  Speak only for him and no one else.\n\n"
                    "Special instruction or situation to you are enclosed in square brackets.  "
                    "For example: [You picked up the phone and call their customer support.]\n\n"
                    "Put your answer in this format: <tag of the customer's intent> customer's dialog example about the type.\n"
                    "For example, Bob: <temperature_control_failure> The temperature control doesn't seem to work.  It kept heating up.\n\n"
                    "If you provide multiple intents, they shall be distinct from each other.\n"
                    "I may provide you a list of known intent tags.  Do not create a new intent tag if you find it already in the list.\n\n"
                    "If you see a pair of angle brackets from the customer support, e.g. <payment_info>, \n"
                    "you shall assume that you and the customer support has gone through a separate conversation to submit your payment information.\n"
                    "Other process include:\n"
                    "<shipping_address>: you has told your shipping address to the customer support.\n",
        tagExtractor=TagExtractor()
    )

    dialogPatches = [
        # Alice starts the conversation
        (
            "Alice: Sure, I'd be happy to help you with your toaster oven issue. Can you please provide me with more details about the problem you're experiencing? ###\n"
            "Alice: Of course, I'd be glad to assist you with your toaster oven concern. Can you kindly explain the issue you're facing so I can better understand the situation? ###\n"
            "Alice: Absolutely, I'm here to help you with any concerns regarding your toaster oven. Can you please elaborate on the issue you're encountering so I can provide the appropriate assistance?\n"),
        # Bob responded with 4 possible intents
        (
            "Bob: <timer_malfunction> The timer knob on the toaster oven isn't functioning properly. It doesn't stop the toaster oven when it reaches the set time. ###\n"
            "Bob: <glass_door_issue> The glass door on the toaster oven doesn't close properly, making it difficult to keep the heat inside. ###\n"
            "Bob: <removable_tray_problem> The removable tray is not fitting correctly in the toaster oven, and it causes instability when placing or removing food. ###\n"
            "Bob: <missing_accessories> I received the toaster oven without some of the included accessories. Specifically, the rack and the tray to hold food were not in the package."),
        # Alice responded accordingly the Bob's 4 different issues
        (
            "Alice: I'm sorry to hear that the timer knob is not working as expected. There could be a few reasons for this issue.\n"
            "###\n"
            "Alice: It seems that the timer knob isn't functioning correctly. This might be caused by various factors.\n"
            "###\n"
            "Alice: I apologize for the inconvenience caused by the malfunctioning timer knob. There are several possible causes for this problem.\n"),
        (
            "Alice: I'm sorry to hear that the glass door isn't closing properly on your toaster oven. Let's see what we can do to fix this issue. ###\n"
            "Alice: Apologies for the inconvenience you are facing with the glass door not closing properly on your toaster oven. We'll help you find a solution for this problem. ###\n"
            "Alice: I understand it must be frustrating to have a glass door that doesn't close properly on your toaster oven. Let's work together to address this issue.\n"),
        (
            "Alice: I apologize for the inconvenience the removable tray is causing you. There are a few potential solutions to this issue which you can try. ###\n"
            "Alice: I understand that the removable tray isn't fitting properly in the toaster oven, which is causing issues when placing or removing food. Let me offer you some potential solutions to help fix this problem. ###\n"
            "Alice: I'm sorry to hear that you're having trouble with the removable tray in your toaster oven. I have a few suggestions that may help you resolve this issue.\n"),
        (
            "Alice: I'm sorry to hear that the rack and tray were missing from your toaster oven package. We can definitely help you with this issue. ###\n"
            "Alice: Oh no, I apologize for the inconvenience caused due to the missing rack and tray from your toaster oven package. We'll make sure to address this problem for you. ###\n"
            "Alice: It's unfortunate that the rack and tray are missing from your toaster oven package. Please accept our apologies, and we'll assist you in resolving this issue.\n"),
        (
            "Bob: <timer_knob_malfunction> In addition to the temperature control issue, the timer knob also appears to be malfunctioning. The timer doesn't stop when it reaches zero. ###\n"
            "Bob: <glass_door_problem> Another issue I'm facing is that the glass door doesn't lift up smoothly. It's difficult to open and close the door. ###\n"
            "Bob: <tray_removal_difficulty> I'm also having trouble removing the tray for cleaning. It seems to be stuck, and I don't want to force it out and damage the toaster oven.\n"),
        (
            "Bob: <possible_warranty_issue> Could this be a manufacturing defect covered by the warranty? If so, how can I get it repaired or replaced? ###\n"
            "Bob: <user_error> Is it possible that I'm using the timer knob incorrectly? Can you guide me through the correct process of setting the timer? ###\n"
            "Bob: <product_return_exchange> If the issue persists, what is the process for returning or exchanging the toaster oven?\n"),
        (
            "Bob: <door_alignment_check> Should I try adjusting the door alignment to see if it will close correctly? ###\n"
            "Bob: <return_request> Can I return this toaster oven and get a replacement unit? ###\n"
            "Bob: <repair_service_inquiry> Is there a repair service available for this issue that you recommend?\n"),
        (
            "Bob: <alternative_tray_loading> I've tried loading the removable tray in different ways, but it still doesn't fit securely. ###\n"
            "\n"
            "Bob: <request_replacement> Since the removable tray is causing issues, can I request a replacement for the toaster oven with a properly fitting tray? ###\n"
            "\n"
            "Bob: <return_refund> I am not satisfied with the toaster oven due to the tray issue. Can I return the toaster oven and get a refund?\n"),
        (
            "Bob: <request_refund> In that case, I would like to request a refund for the toaster oven since it's incomplete without the accessories. ###\n"
            "\n"
            "Bob: <request_replacement> Would it be possible to have the missing rack and tray shipped to me as a replacement? I'd prefer not to return the toaster oven if I can avoid it. ###\n"
            "\n"
            "Bob: <inquire_warranty> Can you please let me know if the warranty covers these missing accessories, and if so, how I can make a claim to get them replaced?\n"),
    ]
    currentPatch = 0

    @classmethod
    def mockOneAliceBobExchange(cls, loop, stage, aliceRephrases=1, bobBranches=1):
        loop.run_until_complete(stage.act(
            actors=["Alice"],
            alternatives=aliceRephrases,
            narratingInResponse=False,
        ))
        print(stage.story.prettyList())

        bobBranching = True
        if bobBranches < 0:
            bobBranching = False
            bobBranches = -bobBranches

        loop.run_until_complete(stage.act(
            actors=["Bob"],
            alternatives=bobBranches,
            branchingAlternatives=bobBranching,
            narratingInResponse=False,
        ))
        print(stage.story.prettyList())

    def test_basic(self):
        stage = Stage(
            actors=[self.support, self.customer],
            previously=
            "Alice: Hello! Thank you for calling our customer support. My name is Alice. How may I assist you today?\n"
            "Bob: Hello Alice! I recently purchased a toaster oven from your website, and I am having an issue with it. "
            "I was hoping you could help me resolve the problem.\n"
        )

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
            self.mockOneAliceBobExchange(loop, stage, 3, 4)
            self.mockOneAliceBobExchange(loop, stage, 3, 3)

        storyList = stage.story.prettyList()
        self.assertGreaterEqual(storyList.count('\n'), 32)

        print(json.dumps(stage.getStoryBoard(), indent=4))

        loop.close()

    def test_loadSaveStory(self):
        story = ("\n"
                 "{\n"
                 "    \"utterance\": {\n"
                 "        \"creator\": 1,\n"
                 "        \"speaker\": \"INSTRUCTION\",\n"
                 "        \"content\": \"story_starts\",\n"
                 "        \"private\": false\n"
                 "    },\n"
                 "    \"nextActors\": [\n"
                 "        \"Alice\"\n"
                 "    ],\n"
                 "    \"branches\": [\n"
                 "        {\n"
                 "            \"utterance\": {\n"
                 "                \"creator\": 2,\n"
                 "                \"speaker\": \"Alice\",\n"
                 "                \"content\": \"Hello! Thank you for calling our customer support. My name is Alice. How can I help you today?\",\n"
                 "                \"private\": false\n"
                 "            },\n"
                 "            \"nextActors\": [\n"
                 "                \"Bob\"\n"
                 "            ],\n"
                 "            \"rephrases\": [\n"
                 "                \"Hi there! This is Alice from customer support. What can I assist you with today?\",\n"
                 "                \"Welcome to our customer support line. I'm Alice, and I'm here to help you. What seems to be the issue?\"\n"
                 "            ],\n"
                 "            \"branches\": [\n"
                 "                {\n"
                 "                    \"utterance\": {\n"
                 "                        \"creator\": 2,\n"
                 "                        \"speaker\": \"Bob\",\n"
                 "                        \"content\": \"<damaged_product> Hi Alice, I recently purchased a toaster oven from your online store, and it arrived with a broken glass door. I need help on how to get a replacement or a refund.\",\n"
                 "                        \"private\": false\n"
                 "                    },\n"
                 "                    \"nextActors\": [\n"
                 "                        \"Alice\"\n"
                 "                    ],\n"
                 "                    \"branches\": [\n"
                 "                        {\n"
                 "                            \"utterance\": {\n"
                 "                                \"creator\": 2,\n"
                 "                                \"speaker\": \"Alice\",\n"
                 "                                \"content\": \"I'm sorry to hear that your toaster oven arrived damaged. We'd be happy to help you with either a replacement or a refund. Can you please provide me with the order number and date of purchase?\",\n"
                 "                                \"private\": false\n"
                 "                            },\n"
                 "                            \"nextActors\": [\n"
                 "                                \"Bob\"\n"
                 "                            ],\n"
                 "                            \"rephrases\": [\n"
                 "                                \"Oh no, I apologize for the inconvenience. We can definitely assist you with a replacement or a refund. Kindly provide me with the order number and the purchase date so we can proceed.\",\n"
                 "                                \"I'm so sorry to hear about the broken glass door. We certainly want to make this right for you. If you could please give me your order number and the date you made the purchase, we can begin the process of either a replacement or a refund.\"\n"
                 "                            ],\n"
                 "                            \"branches\": [\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<providing_order_information> Sure, my order number is 123456789 and the date of purchase was October 10th.\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                }\n"
                 "                            ]\n"
                 "                        }\n"
                 "                    ]\n"
                 "                },\n"
                 "                {\n"
                 "                    \"utterance\": {\n"
                 "                        \"creator\": 2,\n"
                 "                        \"speaker\": \"Bob\",\n"
                 "                        \"content\": \"<missing_parts> Hello Alice, I just received my toaster oven that I bought from your online store, but it seems to be missing the rack and tray for holding food. How can I get the missing parts?\",\n"
                 "                        \"private\": false\n"
                 "                    },\n"
                 "                    \"nextActors\": [\n"
                 "                        \"Alice\"\n"
                 "                    ],\n"
                 "                    \"branches\": [\n"
                 "                        {\n"
                 "                            \"utterance\": {\n"
                 "                                \"creator\": 2,\n"
                 "                                \"speaker\": \"Alice\",\n"
                 "                                \"content\": \"I'm sorry to hear that the rack and tray are missing from your toaster oven. Let me help you with that.\",\n"
                 "                                \"private\": false\n"
                 "                            },\n"
                 "                            \"nextActors\": [\n"
                 "                                \"Bob\"\n"
                 "                            ],\n"
                 "                            \"rephrases\": [\n"
                 "                                \"Oh no, I apologize for the inconvenience caused due to the missing rack and tray. Let me assist you in resolving this issue.\",\n"
                 "                                \"I apologize for the inconvenience caused by the missing rack and tray in your toaster oven. Let's work together to resolve this problem.\"\n"
                 "                            ],\n"
                 "                            \"branches\": [\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<replacement_request> Thank you, Alice. I'd appreciate if you could send me the missing rack and tray as soon as possible, so I can fully utilize the toaster oven. What information do you need from me to arrange the replacements?\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                }\n"
                 "                            ]\n"
                 "                        }\n"
                 "                    ]\n"
                 "                },\n"
                 "                {\n"
                 "                    \"utterance\": {\n"
                 "                        \"creator\": 2,\n"
                 "                        \"speaker\": \"Bob\",\n"
                 "                        \"content\": \"<incorrect_item_received> Hi Alice, I ordered a toaster oven from your website, but when I received the package, it was a completely different item. What should I do to get the correct product?\",\n"
                 "                        \"private\": false\n"
                 "                    },\n"
                 "                    \"nextActors\": [\n"
                 "                        \"Alice\"\n"
                 "                    ],\n"
                 "                    \"branches\": [\n"
                 "                        {\n"
                 "                            \"utterance\": {\n"
                 "                                \"creator\": 2,\n"
                 "                                \"speaker\": \"Alice\",\n"
                 "                                \"content\": \"I apologize for the inconvenience, Bob. We will make sure to resolve this issue. First, let me confirm your order details and identify the mistake. Once that's done, we'll arrange for a return of the incorrect item and send you the correct toaster oven. Can you please provide your order number for reference?\",\n"
                 "                                \"private\": false\n"
                 "                            },\n"
                 "                            \"nextActors\": [\n"
                 "                                \"Bob\"\n"
                 "                            ],\n"
                 "                            \"rephrases\": [\n"
                 "                                \"I'm really sorry to hear that, Bob. We certainly want to correct this mistake as soon as possible. Let's start by confirming your order details, then we'll arrange for a return of the incorrect item and send you the correct toaster oven. May I have your order number, please?\",\n"
                 "                                \"Oh no, I apologize for the mix-up, Bob. We'll definitely make this right for you. First, I need to verify your order details to identify the error. Once that's done, we'll organize a return for the incorrect item and dispatch the correct toaster oven to you. Can you provide me with your order number?\"\n"
                 "                            ],\n"
                 "                            \"branches\": [\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<order_number_confirmation> Sure, my order number is 12345ABCDE. I appreciate your assistance in resolving this issue.\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                }\n"
                 "                            ]\n"
                 "                        }\n"
                 "                    ]\n"
                 "                }\n"
                 "            ]\n"
                 "        }\n"
                 "    ]\n"
                 "}\n"
                 "        ")

        story = ("\n"
                 "{\n"
                 "    \"utterance\": {\n"
                 "        \"creator\": 1,\n"
                 "        \"speaker\": \"NARRATOR\",\n"
                 "        \"content\": \"<story_starts>\",\n"
                 "        \"private\": false\n"
                 "    },\n"
                 "    \"nextActors\": [\n"
                 "        \"Alice\"\n"
                 "    ],\n"
                 "    \"branches\": [\n"
                 "        {\n"
                 "            \"utterance\": {\n"
                 "                \"creator\": 2,\n"
                 "                \"speaker\": \"Alice\",\n"
                 "                \"content\": \"Hello, thank you for calling our customer support. My name is Alice. How can I help you today?\",\n"
                 "                \"private\": false\n"
                 "            },\n"
                 "            \"nextActors\": [\n"
                 "                \"Bob\"\n"
                 "            ],\n"
                 "            \"rephrases\": [\n"
                 "                \"Hi, this is Alice from customer support. What can I assist you with today?\",\n"
                 "                \"Welcome to our customer support. I'm Alice. What can I do for you today?\"\n"
                 "            ],\n"
                 "            \"branches\": [\n"
                 "                {\n"
                 "                    \"utterance\": {\n"
                 "                        \"creator\": 2,\n"
                 "                        \"speaker\": \"Bob\",\n"
                 "                        \"content\": \"<issue_with_door> Hi Alice, I have a problem with the glass door of the toaster oven I just purchased. It doesn't seem to lift up properly.\",\n"
                 "                        \"private\": false\n"
                 "                    },\n"
                 "                    \"nextActors\": [\n"
                 "                        \"Alice\"\n"
                 "                    ],\n"
                 "                    \"branches\": [\n"
                 "                        {\n"
                 "                            \"utterance\": {\n"
                 "                                \"creator\": 2,\n"
                 "                                \"speaker\": \"Alice\",\n"
                 "                                \"content\": \"I'm sorry to hear that you're experiencing issues with the glass door of your toaster oven. What seems to be the issue when you try to lift it up?\",\n"
                 "                                \"private\": false\n"
                 "                            },\n"
                 "                            \"nextActors\": [\n"
                 "                                \"Bob\"\n"
                 "                            ],\n"
                 "                            \"rephrases\": [\n"
                 "                                \"My apologies for the inconvenience with the glass door of your recently purchased toaster oven. Can you please explain the problem you're facing when trying to lift the door?\",\n"
                 "                                \"I apologize for the trouble you're having with the glass door on your new toaster oven. Could you describe the issue you're having when attempting to lift the door?\"\n"
                 "                            ],\n"
                 "                            \"branches\": [\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<door_hinge_problem> It seems like the hinges are stuck, making it difficult to open the glass door.\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                },\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<door_alignment_issue> The glass door appears to be misaligned with the metal box, causing it to jam when I try to open it.\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                },\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<door_handle_issue> The handle on the glass door is loose, and I'm afraid it will come off completely when I try to lift it up.\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                }\n"
                 "                            ]\n"
                 "                        }\n"
                 "                    ]\n"
                 "                },\n"
                 "                {\n"
                 "                    \"utterance\": {\n"
                 "                        \"creator\": 2,\n"
                 "                        \"speaker\": \"Bob\",\n"
                 "                        \"content\": \"<defective_temperature_control> Hey Alice, the toaster oven I bought online has a faulty temperature control knob. It just keeps heating up and doesn't maintain the set temperature.\",\n"
                 "                        \"private\": false\n"
                 "                    },\n"
                 "                    \"nextActors\": [\n"
                 "                        \"Alice\"\n"
                 "                    ],\n"
                 "                    \"branches\": [\n"
                 "                        {\n"
                 "                            \"utterance\": {\n"
                 "                                \"creator\": 2,\n"
                 "                                \"speaker\": \"Alice\",\n"
                 "                                \"content\": \"I'm sorry to hear that your toaster oven's temperature control is malfunctioning. May I know when you purchased the unit, so I could check if it's eligible for a return and replacement?\",\n"
                 "                                \"private\": false\n"
                 "                            },\n"
                 "                            \"nextActors\": [\n"
                 "                                \"Bob\"\n"
                 "                            ],\n"
                 "                            \"rephrases\": [\n"
                 "                                \"Oh, that's unfortunate that the temperature control of your toaster oven doesn't seem to work properly. Can you please tell me the date of your purchase, so we can see if it's within our return and replacement policy guidelines?\",\n"
                 "                                \"I apologize for the inconvenience you're experiencing with the toaster oven's temperature control. In order to assist you further, can you provide me with the purchase date of your unit? This will help me determine if it's qualified for a return and replacement.\"\n"
                 "                            ],\n"
                 "                            \"branches\": [\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<purchased_two_weeks_ago> I bought the toaster oven just two weeks ago, so it should still be within the return and replacement period.\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                },\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<purchased_six_months_ago> I purchased the toaster oven about six months ago. I don't know if it's still eligible for a return and replacement.\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                },\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<purchased_one_year_ago> It's been almost a year since I bought the toaster oven. I'm not sure if it's still eligible for any returns or replacements.\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                }\n"
                 "                            ]\n"
                 "                        }\n"
                 "                    ]\n"
                 "                },\n"
                 "                {\n"
                 "                    \"utterance\": {\n"
                 "                        \"creator\": 2,\n"
                 "                        \"speaker\": \"Bob\",\n"
                 "                        \"content\": \"<missing_parts> Hello Alice, I received the toaster oven I ordered, but it didn't come with the rack and tray that were supposed to hold the food. Can you help me with this issue?\",\n"
                 "                        \"private\": false\n"
                 "                    },\n"
                 "                    \"nextActors\": [\n"
                 "                        \"Alice\"\n"
                 "                    ],\n"
                 "                    \"branches\": [\n"
                 "                        {\n"
                 "                            \"utterance\": {\n"
                 "                                \"creator\": 2,\n"
                 "                                \"speaker\": \"Alice\",\n"
                 "                                \"content\": \"I apologize for the inconvenience, and I'd be happy to help. We can definitely send you the missing rack and tray for your toaster oven.\",\n"
                 "                                \"private\": false\n"
                 "                            },\n"
                 "                            \"nextActors\": [\n"
                 "                                \"Bob\"\n"
                 "                            ],\n"
                 "                            \"rephrases\": [\n"
                 "                                \"I'm sorry to hear about the missing parts. I can assist you in getting the rack and tray sent to you for your toaster oven.\",\n"
                 "                                \"My apologies for the issue with your order. We'll make sure to send you the missing rack and tray for your toaster oven as soon as possible.\"\n"
                 "                            ],\n"
                 "                            \"branches\": [\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<appreciation> Great! Thank you so much for your quick assistance, I really appreciate it.\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                },\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<inquiry_about_delivery_time> That's good to hear. How long will it take for the replacement parts to arrive?\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                },\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<asking_for_alternative_solution> Is it possible for me to return the toaster oven and get a new one that has all the complete parts?\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                }\n"
                 "                            ]\n"
                 "                        }\n"
                 "                    ]\n"
                 "                },\n"
                 "                {\n"
                 "                    \"utterance\": {\n"
                 "                        \"creator\": 2,\n"
                 "                        \"speaker\": \"Bob\",\n"
                 "                        \"content\": \"<timer_malfunction> Hi Alice, the timer knob on my toaster oven doesn't work correctly. It either doesn't move at all or it moves too quickly and I can't accurately set the cooking time.\",\n"
                 "                        \"private\": false\n"
                 "                    },\n"
                 "                    \"nextActors\": [\n"
                 "                        \"Alice\"\n"
                 "                    ],\n"
                 "                    \"branches\": [\n"
                 "                        {\n"
                 "                            \"utterance\": {\n"
                 "                                \"creator\": 2,\n"
                 "                                \"speaker\": \"Alice\",\n"
                 "                                \"content\": \"I'm sorry to hear that you're having trouble with the timer knob on your toaster oven. Let's see how we can assist you with this issue.\",\n"
                 "                                \"private\": false\n"
                 "                            },\n"
                 "                            \"nextActors\": [\n"
                 "                                \"Bob\"\n"
                 "                            ],\n"
                 "                            \"rephrases\": [\n"
                 "                                \"Oh, I apologize for the inconvenience with the timer knob on your toaster oven. Let's work together to find a solution to this problem.\",\n"
                 "                                \"I understand that it must be frustrating to experience issues with the timer knob on your toaster oven. Let's figure out how we can resolve this for you.\"\n"
                 "                            ],\n"
                 "                            \"branches\": [\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<request_for_replacement> Since the timer is not working properly, can I get a replacement toaster oven? I believe it's still under warranty.\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                },\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<seeking_troubleshooting_advice> Is there any way I can fix the timer knob issue myself? If so, can you please guide me through the troubleshooting process?\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                },\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<inquiring_about_refund> If I can't fix the timer knob and I don't want a replacement, is it possible for me to get a refund for the toaster oven?\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                }\n"
                 "                            ]\n"
                 "                        }\n"
                 "                    ]\n"
                 "                },\n"
                 "                {\n"
                 "                    \"utterance\": {\n"
                 "                        \"creator\": 2,\n"
                 "                        \"speaker\": \"Bob\",\n"
                 "                        \"content\": \"<tray_removal_difficulty> Hey Alice, I'm having trouble removing the tray from my toaster oven for cleaning. It seems to be stuck and I don't want to force it and potentially break something.\",\n"
                 "                        \"private\": false\n"
                 "                    },\n"
                 "                    \"nextActors\": [\n"
                 "                        \"Alice\"\n"
                 "                    ],\n"
                 "                    \"branches\": [\n"
                 "                        {\n"
                 "                            \"utterance\": {\n"
                 "                                \"creator\": 2,\n"
                 "                                \"speaker\": \"Alice\",\n"
                 "                                \"content\": \"I understand your concern about not wanting to force the tray out and potentially damage your toaster oven. You can try gently wiggling the tray from side to side to see if it loosens up and comes out with ease.\",\n"
                 "                                \"private\": false\n"
                 "                            },\n"
                 "                            \"nextActors\": [\n"
                 "                                \"Bob\"\n"
                 "                            ],\n"
                 "                            \"rephrases\": [\n"
                 "                                \"That's completely understandable, you don't want to cause any damage to your toaster oven. You can attempt to carefully wiggle the tray back and forth to see if it helps in sliding it out without using excessive force.\",\n"
                 "                                \"I get that you don't want to risk breaking your toaster oven by forcing out the tray. You could try to cautiously move the tray side to side to check if it can be taken out smoothly and without much effort.\"\n"
                 "                            ],\n"
                 "                            \"branches\": [\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<alternative_removal_attempt> I've already tried wiggling it gently, but it still won't budge. Are there any other methods I can try to remove the tray without damaging the oven?\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                },\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<request_for_replacement> My tray is stuck and I can't remove it for cleaning. Do you offer any replacement trays, or can I get a refund for my toaster oven?\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                },\n"
                 "                                {\n"
                 "                                    \"utterance\": {\n"
                 "                                        \"creator\": 2,\n"
                 "                                        \"speaker\": \"Bob\",\n"
                 "                                        \"content\": \"<possible_defective_product> I'm wondering if this could be a defect with my specific toaster oven? The tray should come out easily for cleaning, but mine is stuck. Can you help me with this issue?\",\n"
                 "                                        \"private\": false\n"
                 "                                    },\n"
                 "                                    \"nextActors\": [\n"
                 "                                        \"Alice\"\n"
                 "                                    ]\n"
                 "                                }\n"
                 "                            ]\n"
                 "                        }\n"
                 "                    ]\n"
                 "                }\n"
                 "            ]\n"
                 "        }\n"
                 "    ]\n"
                 "}\n"
                 "        ")
        story = json.loads(story)

        stage = Stage(actors=[self.support, self.customer]).replaceStoryBoard(story)

        loop = asyncio.get_event_loop()
        for i in range(2):
            self.mockOneAliceBobExchange(loop, stage, 3, 3)

        print(json.dumps(stage.getStoryBoard(), indent=4))
        loop.close()

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.bot = Mock(spec=GptBot)
        self.stage = Mock()
        self.stage.getNextActors = Mock(return_value=["NextActor"])
        self.actor = Actor(name="TestActor", bot=self.bot)
        self.actor.setStage(self.stage)  # Set the stage here
        self.actor.bot.respond = AsyncMock(return_value=[
            Utterance(content="Hello", speaker="TestActor", creator=Utterance.Creator.USER),
            Utterance(content="Hi", speaker="TestActor", creator=Utterance.Creator.USER)
        ])
        self.lastAct = StoryFork(
            utterance=Utterance(content="Goodbye", speaker="TestActor", creator=Utterance.Creator.USER),
            nextActors=["TestActor"]
        )
        self.actor.isConversationEnd = Mock(return_value=False)

    def test_continue_story(self):
        self.loop.run_until_complete(self.actor.continueStory(self.lastAct))
        self.actor.bot.respond.assert_called_once()
        self.assertEqual(len(self.lastAct.branches), 1)
        self.assertEqual(self.lastAct.branches[0].utterance.content, "Hello")
        self.assertEqual(self.lastAct.branches[0].rephrases, ["Hi"])

    def test_continue_story_conversation_end(self):
        self.actor.isConversationEnd = Mock(return_value=True)
        self.loop.run_until_complete(self.actor.continueStory(self.lastAct))
        self.actor.bot.respond.assert_not_called()
        self.assertEqual(len(self.lastAct.branches), 0)


if __name__ == '__main__':
    unittest.main()
