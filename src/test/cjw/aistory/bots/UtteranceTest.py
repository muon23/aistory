import unittest

import jsonpickle

from cjw.aistory.bots.Persona import Persona
from cjw.aistory.bots.Utterance import Utterance


class UtteranceTest(unittest.TestCase):
    def test_nonstandardDelimiter(self):
        text = """
        
Option 1:
Bob: <within_30_days> I bought it three weeks ago.

Alice: In that case, you can return and get a refund for the toaster oven as you are still within the 30-day return period. To begin the return process, please provide your shipping address. [shipping address]

###

Option 2:
Bob: <within_1_year> I purchased it 9 months ago.

Alice: Thank you for providing the purchase date. Since it's within the 1-year warranty period, we can replace the broken unit for you. Please provide your shipping address to start the process. [shipping address]

###

Option 3:
Bob: <after_1_year> I bought it 13 months ago.

Alice: I'm sorry to hear that the issue occurred after the 1-year warranty period. Unfortunately, I cannot offer a return or replacement for the toaster oven. However, I recommend checking out our new models as they include improved features and design.

###

Option 4:
Bob: <unknown_purchase_date> I'm not sure when exactly I purchased it.

Alice: No problem, Bob. Let me check your purchase history. [find_purchase_date] It appears you bought the toaster oven 10 months ago. Since it's still within the 1-year warranty period, we can replace the broken unit for you. Please provide your shipping address, and we'll begin the process. [shipping address] [end conversation]

"""
        result = Utterance.of(text, delimiter='###', parsing=False)

        self.assertEqual(len(result), 4)

    def test_serializing(self):
        persona = Persona.of("Alice: Alice is in the wonderland.")
        sp = jsonpickle.encode(persona[0])
        print(sp)
        persona2 = jsonpickle.decode(sp)
        self.assertEqual(persona[0], persona2)

        dialog = """
        Alice: Where am I?
        Bob: Where are you?
        """
        utterances = Utterance.of(dialog)
        su = jsonpickle.encode(utterances)
        print(su)
        utterances2 = jsonpickle.decode(su)
        self.assertEqual(utterances, utterances2)


if __name__ == '__main__':
    unittest.main()
