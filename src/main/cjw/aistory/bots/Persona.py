import re
from typing import List


class Persona(object):
    @classmethod
    def of(cls, description: str) -> List['Persona']:
        if not description:
            return []

        personas = []

        for c in re.sub('\n+', '\n', description.strip()).split('\n'):
            # Check if it is 'Someone: someone's persona.'
            m = re.match(r'([^:]+)\s*:\s*(.+)$', c)
            if m:
                personas.append(Persona(m.group(1), m.group(2)))

            # No column
            elif not personas:
                # First persona, but did not specify name
                personas.append(Persona(None, c))
            else:
                # Continue the persona of the last person
                personas[-1].add(c)

        return personas

    def __init__(self, name: str | None, persona: str):
        self.name = name
        self.persona = persona

    def __str__(self):
        whose = f"{self.name}'s" if self.name else "Your"
        return f"{whose} persona: {self.persona}"

    def __eq__(self, other):
        return (
            isinstance(other, Persona) and
            self.name == other.name and
            self.persona == other.persona
        )

    def add(self, description: str):
        self.persona += description

