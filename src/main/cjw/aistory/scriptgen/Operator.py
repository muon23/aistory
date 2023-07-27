from cjw.aistory.storyboard.Actor import Actor


class Operator(Actor):
    @classmethod
    def of(cls, name: str = "Operator", **kwargs) -> "Operator":
        role = kwargs.get("role", "operator")
        company = kwargs.get("company", "ABC")

        instruction = kwargs.pop("instruction", None)
        if not instruction:
            instruction = (
                "We are to make up the conversation between the operator and the customer. "
                f"You will be a {role} of {company}, {name}.  I'll be the customer.  You shall only speak for {name}.\n\n"
                "Special instruction or situation to you are enclosed in square brackets.  "
                "For example: [You picked up the call and greed the customer.]\n\n"
            )

        protocols = kwargs.get("protocols", [])
        if protocols:
            instruction += (
                "When appropriate, you may proceed into a certain protocols with the customer.  "
                "Put down the protocol name in angle brackets.  "
                f"For example, '{name}: <obtain_payment_method>  What else I can do for you?'\n"
                "This means that you and the customer has gone over the payment method conversation at that place.  "
                "You shall skip that section of conversation and move forward as if it has already happened.\n"
                f"These are the available protocols: {', '.join(protocols)}\n\n"
            )

        return Operator(name=name, instruction=instruction, narratingInResponse=False, **kwargs)
