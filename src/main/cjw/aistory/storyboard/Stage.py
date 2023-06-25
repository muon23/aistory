import logging
import os
import random
from typing import List, Dict

import jsonpickle

from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.storyboard.Actor import Actor
from cjw.aistory.storyboard.StoryFork import StoryFork


class Stage:
    """
    The Stage class represents a stage where actors engage in a conversation.
    """
    logger = logging.getLogger(__qualname__)

    def __init__(
            self,
            actors: List[Actor],
            previously: str | Utterance | List[str] | List[Utterance] = None,
            firstActor: str = None,
            **kwargs
    ):
        """
        Constructor for the Stage class.

        Args:
            actors (List[Actor]): The list of actors in the stage.
            previously (str | Utterance | List[str] | List[Utterance], optional):
                The previous conversation that sets the context. Defaults to None.
            firstActor (str, optional): The name of the actor to start the conversation.
                Defaults to None, which means the next actor based on the previous dialog, or the first actor in the list of the actors.
            **kwargs: Additional keyword arguments.
        """
        # Create a dictionary of actors with their names as keys
        self.actors: Dict[str, Actor] = {a.name: a for a in actors}

        # Set the stage for each actor
        for a in actors:
            a.setStage(self)

        # Create the initial story fork
        if not previously:
            previously = "<story_starts>"
        self.story: StoryFork = StoryFork.of(previously, [firstActor if firstActor else actors[0].name])

        # Set the policy for selecting the next actor
        self.nextActorPolicy = kwargs.get("nextSpeakerPolicy", "round robin")

        # Set the names and indices of the actors for fast access to the actors
        self.actorNames = kwargs.get("actorNames", [str(k) for k in self.actors.keys()])
        self.actorIndices = {n: i for i, n in enumerate(self.actorNames)}

    async def act(self, **kwargs) -> "Stage":
        """
        Acts in the stage, continuing the story for each actor.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            Stage: The updated stage.
        """
        actors = kwargs.get("actors", self.actorNames)

        for s in self.story.getStoryLeads():
            for a in [actor for actor in s.nextActors if actor in actors]:
                await self.actors[a].continueStory(s, **kwargs)
        return self

    async def randomThread(self, maxDepth: int, start: StoryFork = None, **kwargs) -> List[StoryFork]:
        """
        Generates a story line by randomly selecting a branch and following it along

        Args:
            maxDepth (int): The maximum depth of the random thread.
            start (StoryFork): The starting story fork. If None, uses the stage's initial story fork.
            **kwargs: Additional keyword arguments.

        Returns:
            List[StoryFork]: The random thread of conversation.
        """
        if not start:
            start = self.story

        lead: StoryFork = random.choice(start.getStoryLeads())
        storyLine = lead.getPreviousStory()
        for i in range(maxDepth):
            actor: str = random.choice(lead.nextActors)
            self.logger.debug(f"{actor} to respond to '{lead}'")

            await self.actors[actor].continueStory(lead, **kwargs)
            if not lead.branches:
                break

            while lead.branches:
                lead = random.choice(lead.branches)
                storyLine.append(lead)

        return storyLine

    def getNextActors(self, responses: List[Utterance]) -> List[str]:
        """
        Determines the next actors based on the responses and the actor selection policy.

        Args:
            responses (List[Utterance]): The list of responses.

        Returns:
            List[str]: The list of next actors.
        """
        if self.nextActorPolicy == "round robin":
            for r in reversed(responses):
                if r.speaker in self.actorNames:
                    lastActorIndex = self.actorIndices[r.speaker]
                    nextActor = self.actorNames[(lastActorIndex + 1) % len(self.actorNames)]
                    return [nextActor]

            # Can't find any valid speakers, so everyone got a chance to talk
            return self.actorNames

        raise NotImplementedError(f"Unsupported next speaker policy '{self.nextActorPolicy}'")

    def getStoryBoard(self, indent=4):
        """
        Returns the serialized story board.

        Args:
            indent (int): The number of spaces for indentation.

        Returns:
            str: The serialized story board.
        """
        return jsonpickle.encode(self.story, indent=indent)

    def replaceStoryBoard(self, data: dict) -> "Stage":
        """
        Replaces the story board with the given data.

        Args:
            data (dict): The data representing the story board.

        Returns:
            Stage: The updated stage.
        """
        self.story = jsonpickle.decode(data)
        return self

    def save(self, file: str, indent=4):
        """
        Saves the stage to a file.

        Args:
            file (str): The file path.
            indent (int): The number of spaces for indentation.
        """
        directory = os.path.dirname(file)
        if not os.path.exists(directory):
            os.makedirs(directory)

        pickled = jsonpickle.encode(self, indent=indent)
        with open(file, "w") as fd:
            fd.write(pickled)

    @classmethod
    def load(cls, file: str) -> "Stage":
        """
        Loads a stage from a file.

        Args:
            file (str): The file path.

        Returns:
            Stage: The loaded stage.
        """
        with open(file, "r") as fd:
            data = fd.read()

        return jsonpickle.decode(data)
