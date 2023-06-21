import logging
import random
from typing import List, Dict

import jsonpickle

from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.storyboard.Actor import Actor
from cjw.aistory.storyboard.StoryFork import StoryFork


class Stage:
    logger = logging.getLogger(__name__)

    def __init__(
            self,
            actors: List[Actor],
            previously: str | Utterance | List[str] | List[Utterance] = None,
            firstActor: str = None,
            **kwargs
    ):
        self.actors: Dict[str, Actor] = {a.name: a for a in actors}
        for a in actors:
            a.setStage(self)

        if not previously:
            previously = "<story_starts>"
        self.story: StoryFork = StoryFork.of(previously, [firstActor if firstActor else actors[0].name])

        self.nextActorPolicy = kwargs.get("nextSpeakerPolicy", "round robin")
        self.actorNames = kwargs.get("actorNames", [str(k) for k in self.actors.keys()])
        self.actorIndices = {n: i for i, n in enumerate(self.actorNames)}

    async def act(self, **kwargs) -> "Stage":
        actors = kwargs.get("actors", self.actorNames)

        for s in self.story.getStoryLeads():
            for a in [actor for actor in s.nextActors if actor in actors]:
                await self.actors[a].continueStory(s, **kwargs)
        return self

    async def randomThread(self, maxDepth: int, start: StoryFork = None, **kwargs) -> List[Utterance]:
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
        return jsonpickle.encode(self.story, indent=indent)

    def replaceStoryBoard(self, data: dict) -> "Stage":
        self.story = jsonpickle.decode(data)
        return self

