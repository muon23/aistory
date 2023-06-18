from typing import List, Dict

from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.storyboard.Actor import Actor
from cjw.aistory.storyboard.StoryFork import StoryFork


class Stage:
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
                await self.actors[a].continueStory(s, a, **kwargs)
        return self

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

    def getStoryBoard(self):
        return self.story.serialize()

    def replaceStoryBoard(self, data: dict) -> "Stage":
        self.story = StoryFork.deserialize(data)
        return self
