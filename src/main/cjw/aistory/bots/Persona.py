import re
from typing import List


class Persona(object):
    """
    Class representing a persona of a bot
    """

    @classmethod
    def of(cls, description: str) -> List['Persona']:
        """
        Parses a description string and returns a list of persona objects.

        It can be a simple description for the bot, e.g., 'You are a sarcastic customer support agent.'

        To describe multiple personas, put the bots' names in front of the description.
        For example: 'Alice: Alice is shy.\nBob: Bob is an accountant.'

        Args:
            description (str): Description string

        Returns:
            List['Persona']: List of persona objects
        """
        if not description:
            return []

        personas = []

        for c in re.sub('\n+', '\n', description.strip()).split('\n'):
            # Check if it is 'Someone: someone's persona.'
            m = re.match(r'([^:]+)\s*:\s*(.+)$', c)
            if m:
                personas.append(Persona(m.group(1), m.group(2)))

            # No colon
            elif not personas:
                # First persona, but did not specify name
                personas.append(Persona(None, c))
            else:
                # Continue the persona of the last person
                personas[-1].add(c)

        return personas

    def __init__(self, name: str | None, persona: str):
        """
        Initializes a persona instance.

        Args:
            name (str | None): Name of the bot
            persona (str): Persona description
        """
        self.name = name
        self.persona = persona

    def __str__(self):
        """
        Returns a string representation of the persona.

        Returns:
            str: String representation of the persona
        """
        whose = f"{self.name}'s" if self.name else "Your"
        return f"{whose} persona: {self.persona}"

    def __eq__(self, other):
        """
        Compares two persona instances for equality.

        Args:
            other: The other persona instance to compare

        Returns:
            bool: True if the persona instances are equal, False otherwise
        """
        return (
                isinstance(other, Persona) and
                self.name == other.name and
                self.persona == other.persona
        )

    def add(self, description: str):
        """
        Adds additional description to the persona.

        Args:
            description (str): Additional description
        """
        self.persona += description
