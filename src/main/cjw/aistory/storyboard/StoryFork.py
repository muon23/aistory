import copy
from typing import List

from cjw.aistory.bots.Utterance import Utterance
from cjw.aistory.storyboard.TagExtractor import TagExtractor


class StoryFork:
    """
    The StoryFork class represents a fork in the conversation's story.

    Attributes:
        utterance (Utterance): The utterance at this fork.
        branches (List[StoryFork]): The branches that stem from this fork.
        nextActors (List[str]): The actors who can continue the conversation from this fork.
        previous (StoryFork): The previous fork in the conversation.
        rephrases (List[str]): Rephrases of the utterance.
        tags (dict): Tags associated with the utterance.
    """

    @classmethod
    def of(
            cls,
            contents: str | Utterance | List[str] | List[Utterance],
            nextActors: List[str],
            previous: "StoryFork" = None,
            tagExtractor: TagExtractor = None,
    ) -> "StoryFork":
        """
        Create a StoryFork instance from contents and next actors.

        Args:
            contents: The contents of the story fork (utterance or list of utterances).
            nextActors: The actors who can continue the conversation from this fork.
            previous: The previous fork in the conversation. Defaults to None.
            tagExtractor: The tag extractor to extract tags from the contents. Defaults to None.

        Returns:
            StoryFork: The created StoryFork instance.
        """
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
        """
        Initialize the StoryFork instance.

        Args:
            utterance: The utterance at this fork.
            nextActors: The actors who can continue the conversation from this fork. Defaults to None.
            branches: The branches that stem from this fork. Defaults to None.
            previous: The previous fork in the conversation. Defaults to None.
        """
        self.utterance = utterance
        self.branches = branches if branches else []
        self.nextActors = nextActors if nextActors else []
        self.previous = previous
        self.rephrases = []
        self.tags = {}

    def __str__(self):
        return f"{self.utterance} {','.join(self.tags)}"

    def getPreviousStory(self):
        """
        Get the previous forks in the story.

        Returns:
            List[StoryFork]: The list of previous forks in reverse order.
        """
        previously = []
        fork = self
        while fork:
            previously.append(fork)
            fork = fork.previous

        previously.reverse()
        return previously

    def getStoryLine(self, actor: str) -> List[Utterance]:
        """
        Get the story line for a specific actor.

        Args:
            actor: The name of the actor.

        Returns:
            List[Utterance]: The list of utterances in the story line for the given actor.
        """
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
        """
        Get the leads (forks with no branches) in the story.

        Returns:
            List[StoryFork]: The list of leads in the story.
        """
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
        """
        Generate a pretty-printed list of the story forks.

        Args:
            indent: The string used for indentation. Defaults to four spaces.
            indentLevel: The current indentation level. Defaults to 0.

        Returns:
            str: The pretty-printed list of story forks.
        """
        indentation = indent * indentLevel

        tags = f"{','.join(self.tags)} " if self.tags else ""
        output = [f"{indentation}{tags}{self.utterance}"]

        if self.rephrases:
            output += [f"{indentation}({r})" for r in self.rephrases]
        if self.branches:
            output += [b.prettyList(indent=indent, indentLevel=indentLevel + 1) for b in self.branches]

        return '\n'.join(output)
