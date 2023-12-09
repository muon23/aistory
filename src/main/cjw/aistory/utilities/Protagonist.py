from enum import Enum


class Protagonist:
    class Perspective(Enum):
        FIRST = 1
        SECOND = 2
        THIRD = 3

    class Gener(Enum):
        FEMALE = 0
        MALE = 1
        NONE = 2

    class View(Enum):
        USER = 0
        BOT = 1

    def __init__(
            self,
            name: str,
            gender: Gener | str,
            plurality: bool = False,
            userPerspective: Perspective | int = Perspective.THIRD,
            botPerspective: Perspective | int = Perspective.THIRD,
            persona: str = None
    ):
        if gender is None:
            gender = self.Gener.NONE
        elif isinstance(gender, str):
            if "female".startswith(gender.lower()):
                gender = self.Gener.FEMALE
            elif "male".startswith(gender.lower()):
                gender = self.Gener.MALE
            else:
                raise ValueError(f"Unknown gender specification {gender}")

        if isinstance(userPerspective, int):
            userPerspective = self.Perspective(userPerspective)
        if isinstance(botPerspective, int):
            botPerspective = self.Perspective(botPerspective)

        self.name = name
        self.gender: Protagonist.Gener = gender
        self.plurality = plurality
        self.userPerspective = userPerspective
        self.botPerspective = botPerspective
        self.persona = persona

    def getSubjective(self, view: View = View.USER, capitalize: bool = False, useName: bool = False) -> str:
        perspective = self.userPerspective if view == self.View.USER else self.botPerspective

        if self.plurality:
            pronoun = ["we", "you", "they"][perspective.value - 1]
        else:
            pronoun = [
                "I", "you", self.name if useName else ["she", "he", "it"][self.gender.value]
            ][perspective.value - 1]

        if capitalize:
            pronoun = pronoun.capitalize()
        return pronoun

    def getObjective(self, view: View = View.USER, capitalize: bool = False, useName: bool = False) -> str:
        perspective = self.userPerspective if view == self.View.USER else self.botPerspective

        if self.plurality:
            pronoun = ["us", "you", "them"][perspective.value - 1]
        else:
            pronoun = [
                "me", "you", self.name if useName else ["her", "him", "it"][self.gender.value]
            ][perspective.value - 1]

        if capitalize:
            pronoun = pronoun.capitalize()
        return pronoun

    def getPossessive(self, view: View = View.USER, capitalize: bool = False, useName: bool = False) -> str:
        perspective = self.userPerspective if view == self.View.USER else self.botPerspective

        if self.plurality:
            pronoun = ["our", "your", "their"][perspective.value - 1]
        else:
            pronoun = [
                "my", "your", f"{self.name}'s" if useName else ["hers", "his", "its"][self.gender.value]
            ][perspective.value - 1]

        if capitalize:
            pronoun = pronoun.capitalize()
        return pronoun

    def getReflexive(self, view: View = View.USER, capitalize: bool = False, useName: bool = False) -> str:
        perspective = self.userPerspective if view == self.View.USER else self.botPerspective

        if self.plurality:
            pronoun = ["ourselves", "yourselves", "themselves"][perspective.value - 1]
        else:
            pronoun = [
                "myself", "yourself",
                f"{self.name}'s self" if useName else ["herself", "himself", "itself"][self.gender.value]
            ][perspective.value - 1]

        if capitalize:
            pronoun = pronoun.capitalize()
        return pronoun

    def getAuxVerbPresent(self, view: View = View.USER, capitalize: bool = False) -> str:
        perspective = self.userPerspective if view == self.View.USER else self.botPerspective

        if self.plurality:
            verb = "are"
        else:
            verb = ["am", "are", "is"][perspective.value - 1]

        if capitalize:
            verb = verb.capitalize()
        return verb

    def getAuxVerbPp(self, view: View = View.USER, capitalize: bool = False) -> str:
        perspective = self.userPerspective if view == self.View.USER else self.botPerspective

        if self.plurality:
            verb = "have"
        else:
            verb = ["have", "have", "has"][perspective.value - 1]

        if capitalize:
            verb = verb.capitalize()
        return verb

    def getAuxVerbPt(self, view: View = View.USER, capitalize: bool = False) -> str:
        perspective = self.userPerspective if view == self.View.USER else self.botPerspective

        if self.plurality:
            verb = "were"
        else:
            verb = ["was", "were", "was"][perspective.value - 1]

        if capitalize:
            verb = verb.capitalize()
        return verb

    def getPerspective(self, view: View = View.USER, capitalize: bool = False) -> str:
        perspective = self.userPerspective.name if view == self.View.USER else self.botPerspective.name
        return perspective.capitalize() if capitalize else perspective.lower()

    def toJson(self) -> dict:
        return {
            "name": self.name,
            "gender": self.gender.value,
            "plurality": self.plurality,
            "userPerspective": self.userPerspective.value,
            "botPerspective": self.botPerspective.value,
            "persona": self.persona
        }

    @classmethod
    def fromJson(cls, properties: dict) -> "Protagonist":
        userPerspective = properties.get("userPerspective", cls.Perspective.THIRD.value)
        botPerspective = properties.get("botPerspective", cls.Perspective.THIRD.value)
        return Protagonist(
            properties["name"],
            cls.Gener(properties["gender"]),
            plurality=properties.get("plurality", False),
            userPerspective=cls.Perspective(userPerspective),
            botPerspective=cls.Perspective(botPerspective),
            persona=properties.get("persona", None)
        )


