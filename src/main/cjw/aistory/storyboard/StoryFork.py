import copy
from typing import List

from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.storyboard.TagExtractor import TagExtractor


class StoryFork:
    @classmethod
    def of(
            cls,
            contents: str | Utterance | List[str] | List[Utterance],
            nextActors: List[str],
            previous: "StoryFork" = None,
            tagExtractor: TagExtractor = None,
    ) -> "StoryFork":

        utterances = Utterance.of(contents)
        utterances.reverse()

        story = None
        branches = None

        for u in utterances:
            if tagExtractor:
                tags, tagsRemoved = tagExtractor.extract(u.content)
                u.content = tagsRemoved
            else:
                tags = {}

            story = StoryFork(u, nextActors=nextActors, branches=branches, previous=previous)
            story.tags = tags

            if branches:
                branches[0].previous = story
            branches = [story]
            nextActors = [u.speaker]

        return story

    def __init__(
            self,
            utterance: Utterance,
            nextActors: List[str] = None,
            branches: List["StoryFork"] = None,
            previous: "StoryFork" = None,
    ):
        self.utterance = utterance
        self.branches = branches if branches else []
        self.nextActors = nextActors if nextActors else []
        self.previous = previous
        self.rephrases = []
        self.tags = {}

    def __str__(self):
        return f"{self.utterance} {','.join(self.tags)}"

    def getPreviousStory(self):
        previously = []
        fork = self
        while fork:
            previously.append(fork)
            fork = fork.previous

        previously.reverse()
        return previously

    def getStoryLine(self, actor: str) -> List[Utterance]:
        storyLine = []
        fork = self
        while fork:
            if fork.utterance.speaker != actor and fork.utterance.private:
                continue

            utterance = copy.copy(fork.utterance)
            utterance.creator = Utterance.Creator.AI if utterance.speaker == actor else Utterance.Creator.USER
            storyLine.append(utterance)
            fork = fork.previous

        storyLine.reverse()
        return storyLine

    def getStoryLeads(self) -> List["StoryFork"]:
        leads = []
        queue = [self]

        while queue:
            fork = queue.pop(0)
            if fork.branches:
                queue += fork.branches
            else:
                leads.append(fork)

        return leads

    def prettyList(self, indent="    ", indentLevel=0) -> str:
        indentation = indent * indentLevel

        tags = f"{','.join(self.tags)} " if self.tags else ""
        output = [f"{indentation}{tags}{self.utterance}"]

        if self.rephrases:
            output += [f"{indentation}({r})" for r in self.rephrases]
        if self.branches:
            output += [b.prettyList(indent=indent, indentLevel=indentLevel + 1) for b in self.branches]

        return '\n'.join(output)
