import asyncio
import logging
import os
import unittest

from cjw.aistory.bots.GptBot import GptBot
from cjw.aistory.bots.Utterance import Utterance


class GptBotTest(unittest.TestCase):
    logging.basicConfig(level=logging.DEBUG)

    PROJECT = "aistory"
    projectDir = os.getcwd().split(PROJECT)
    projectDir = f"{projectDir[0]}{PROJECT}"

    def test_parseUtterance(self):
        utterances = Utterance.of(
            "Bob: This is good.\n\n"
            "Alice looked surprised, 'What do you mean by good?'\n"
            "Then she realized that he was just sarcastic."
            "[Make up Bob's response here] The light dimmed.\n"
        )
        for u in utterances:
            print(f">>{u}<<")
        self.assertEqual(utterances[0].content, "This is good.")
        self.assertEqual(utterances[0].speaker, "Bob")
        self.assertEqual(utterances[0].creator, Utterance.Creator.USER)
        self.assertEqual(str(utterances[1]), "Alice looked surprised, 'What do you mean by good?'")
        self.assertEqual(utterances[1].speaker, Utterance.NARRATOR)
        self.assertEqual(utterances[2].speaker, Utterance.NARRATOR)
        self.assertEqual(utterances[3].speaker, Utterance.INSTRUCTION)
        self.assertEqual(utterances[3].content, "Make up Bob's response here")
        self.assertEqual(str(utterances[3]), "[Make up Bob's response here]")
        self.assertEqual(utterances[4].speaker, Utterance.NARRATOR)
        self.assertEqual(utterances[4].content, "The light dimmed.")

    def aprilStory(self):
        april: GptBot = GptBot.of(
            name="April",
            personas="April: April is a Ph.D. candidate of applied mathematics.  She is shy but friendly.",
            instruction="You are to answer and act as April.\n\n"
                        "I'll write a brief outline of a section of the story with some key conversations. "
                        "You shall rewrite my content from April's perspective.  "
                        "For example: 'I ordered a cocktail and found a place to sit.'\n\n"
                        "Feel free to expand and add details and twists to the story or rephrase the conversations.\n"
                        "After you were done with the rewriting, make up April's responses.\n\n"
                        "Special instructions to you will be enclosed in square brackets.  "
                        "For example: [Make up a dialog for Max.]\n\n"
                        "In your answer, put April's thought or her actions that only could see in square brackets.  "
                        "For example: ['He is quite a gentleman', I thought]\n\n",
            background="You are in an evening networking event of an AI conference.",
            conversation="You ordered a cocktail, found an empty table, took a seat and opened up your laptop reading.  "
                         "A man approached you.\n"
                         "Man: 'Hello, my name is Max.  Mind if I join you?'"
        )

        # These are recorded GPT-4's responses to my instructions
        aprilResponses = [
            "I ordered a cocktail and found an empty table. Taking a seat, I opened up my laptop and began reading. A man approached me.\n"
            'Max: "Hello, my name is Max. Mind if I join you?"\n'
            "['He seems friendly enough', I thought.]\n\n"
            'April: "Hi, Max. I\'m April. Sure, please have a seat."',

            'Max: "You are here for the conference?" He asked as he pulled out a chair and sat down.\n'
            "['Oh, he's a speaker!', I noticed the nametag around his neck.]\n"
            "April: \"Yes, I am. I've been really looking forward to it. Are you a speaker at the conference?\"",

            'Max: "Oh, yes. I am going to present my paper about using AI to discover new things in astrophysics from old data."\n"'
            '"How about you? Any particular subjects that you are fancy to?" Max continued\n'
            'April: "That sounds fascinating! I\'m actually a Ph.D. candidate in applied mathematics. '
            'I\'m currently working on a project that combines AI and fractal analysis to predict and optimize traffic flow in urban areas. '
            'It\'s pretty intriguing how fractal geometry can help us understand complex systems like traffic patterns."',

            "Max's eyes sparkled with curiosity. \"Wow. Fractal in AI. How do they work together precisely?\""
            "April: \"Well, it's quite interesting. Fractal geometry allows us to model irregular and complex structures found in nature, like coastlines and traffic patterns. "
            "By incorporating AI, we can analyze these fractal models and predict how traffic might flow under various conditions. "
            "This helps us optimize traffic management systems and reduce congestion in urban areas.\"",

            "Max leaned forward with excitement. \"Did you use AI technique to find a fractal model, or did you use fractal to generate training dataset for AI?\""
            "['I must be getting tipsy from this cocktail', I realized, feeling less reserved.]"
            "April: \"Well, it's a bit of both, actually. We first used AI algorithms to analyze large datasets, looking for underlying fractal patterns. "
            "Once we identified the most suitable fractal models, we could generate large synthetic datasets using these fractals. "
            "Then, we trained our AI on these datasets to predict and optimize traffic flow. "
            "It was quite an intricate process, but the results have been really promising so far.\"",

            'Max smiled widely and continued to ask questions. '
            '"How did you make sure that there were no bias? I mean, you trained AI with data generated by AI. '
            'You might predict something, but was that prediction any good?"'
            "['Good question, but I've already considered this', I thought, wearing a proud smile on my face.]"
            "April: \"That's an excellent point, Max. We were aware of the potential for bias, so we validated our predictions by comparing them to real-world traffic data. "
            "By doing this, we were able to confirm that our AI-generated predictions were accurate and reliable. "
            "It's always important to validate AI predictions against real data to ensure they're performing as expected.",

            # This was GPT-4's last response to my instructions.  I stopped at this point.
            #
            # "Max nodded, looking at the ceiling. Then, he looked into my eyes. "
            # "\"When are you going to graduate? I am an assistant professor in MIT. We are needing a postdoc there. "
            # "I know you are not working on astrophysics, but I wonder if you would give us a consideration when you graduate.\""
            # "['What an amazing opportunity!', I thought, pleasantly surprised.]"
            # "April: \"I'm actually expecting to graduate within the next year. Thank you for considering me, that's a great honor! "
            # "I would definitely be interested in exploring opportunities at MIT. "
            # "It could be a fascinating cross-disciplinary experience to apply my knowledge in a new field like astrophysics.\"",
        ]

        # These are instructions that I gave to GPT-4 based it its last responses
        myInstructions = [
            "'You are here for the conference?' Max asked as he pulled out a chair and sit down.\n"
            "You noticed that he was wearing a speaker nametag on his neck.",

            "Max:'Oh, yes.  I am going to present my paper about using AI to discover new things in astrophysics from old data.'\n"
            "'How about you?  Any particular subjects that you are fancy to?'\n"
            "[Come out with an intriguing idea to impress Max]",

            "Sparkles in Max's eyes 'Wow.  Fractal in AI.  How do they work together precisely?'\n",

            "Max leaned forward with excitement.  "
            "'Did you use AI technique to find a fractal model, or did you use fractal to generate training dataset for AI?'\n\n"
            "[You felt tipsy from your cocktail.  You felt less reserved and started pouring out what you did in detail.]",

            "Max smile wildly and continue to ask questions.  "
            "'How did you make sure that there were no bias?  I meant, you trained AI with data generated by AI.  "
            "You might predict something, but was that prediction any good?'\n\n"
            "[You wear a proud smile on your face because you already considered this.]",

            "Max nodded, looking at the ceiling.  Then, he looked into your eyes."
            "'When are you going to graduated?  I am an assistant professor in MIT.  We are needing a postdoc there."
            "I know you are not working on astrophysics, but I wonder if you would give us a consideration when you graduate.'",

        ]

        for i in range(len(aprilResponses)):
            april.insertConversation(aprilResponses[i], creator=Utterance.Creator.AI)
            april.insertConversation(myInstructions[i])

        return april

    @classmethod
    async def aprilRespond(cls, april: GptBot):
        responses = await april.respond()
        for r in responses:
            print(r)

    def test_respond(self):
        april = self.aprilStory()
        file = f"{self.projectDir}/data/unit_test/{self.__class__.__name__}/april.json"
        april.save(file)

        april2: GptBot = GptBot.load(file)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.aprilRespond(april2))
        loop.close()


if __name__ == '__main__':
    unittest.main()
