from typing import Tuple, List

from cjw.aistory.storyboard.Actor import Actor
from cjw.aistory.storyboard.StoryFork import StoryFork
from cjw.aistory.storyboard.TagExtractor import TagExtractor


class Customer(Actor):
    knownIntents = set()

    class IntentExtractor(TagExtractor):
        @classmethod
        def extract(cls, line: str) -> Tuple[List[str], str]:
            tags, dialog = super().extract(line)
            Customer.knownIntents.update(set(tags))
            return tags, dialog

    @classmethod
    def of(cls, name: str = "Customer", **kwargs) -> "Customer":
        instruction = kwargs.get("instruction", None)
        if not instruction:
            instruction = (
                "We are to make up the conversation between the operator and the customer. "
                f"You will act and speak in behalf of the customer, {name}.  I'll be the operator.  You shall only speak for {name}.\n\n"
                "Special instruction or situation to you are enclosed in square brackets.  "
                "For example: [You picked up the phone and call their customer support.]\n\n"
                "Put your answer in this format: Your response to the operator. <intent tag> \n"
                "The intent tag indicate the intent of your response.  "
                "For example, Bob: The temperature control doesn't seem to work.  It kept heating up. <temperature_control_failure>\n\n"
                "I may provide a list of known intent tags.  Respond to the operator first."
                "Then, see if any intent tags matches the intent of your response.  If not, create a new one.\n\n"
            )
        withProtocols = kwargs.get("withProtocols", True)
        if withProtocols:
            instruction += (
                "You may see a 'protocol tag' from the operator, e.g. <obtain_payment_method>. "
                "When you see that, assume that you and the operator has gone through the process and your conversation shall continue from there.  "
                "(In the example, the operator has put your payment method into the system.)\n"
            )

        return Customer(name=name, instruction=instruction, **kwargs)

    async def continueStory(
            self,
            lastAct: StoryFork,
            **kwargs
    ) -> None:
        instructions = kwargs.pop("instruction", [])
        if self.knownIntents:
            instructions.append(f"Known intent tags: {','.join(self.knownIntents)}")

        return await super().continueStory(
            lastAct,
            instructions=instructions,
            **kwargs
        )

