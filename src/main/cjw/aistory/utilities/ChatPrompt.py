import bisect
import functools
import re
from dataclasses import dataclass, field
from typing import List, TypeVar, Dict, Callable


@functools.total_ordering
@dataclass
class Bookmark:
    name: str
    index: int
    of: "ChatPrompt"

    def __lt__(self, other: "Bookmark"):
        return self.index < other.index if isinstance(other, Bookmark) else False

    def toJSON(self) -> dict:
        return {
            "name": self.name,
            "index": self.index
        }

    @classmethod
    def fromJSON(cls, of: "ChatPrompt", properties: dict) -> "Bookmark":
        return Bookmark(
            name=properties.get("name"),
            index=properties.get("index"),
            of=of
        )


@dataclass
class Archive:
    name: str
    origin: "ChatPrompt"
    prompts: List["ChatPrompt"] = field(default_factory=lambda: [])

    def add(self, prompt: "ChatPrompt"):
        self.prompts.append(prompt)

    def toJSON(self) -> dict:
        return {
            "name": self.name,
            "prompts": [pmt.toJSON() for pmt in self.prompts]
        }

    @classmethod
    def fromJSON(cls, origin: "ChatPrompt", properties: dict) -> "Archive":
        return Archive(
            name=properties["name"],
            origin=origin,
            prompts=[ChatPrompt.fromJSON(pmt) for pmt in properties["prompts"]]
        )


class ChatPrompt:
    ChatPrompt = TypeVar("ChatPrompt")

    class InvalidRoleError(Exception):
        def __init__(self, message: str):
            super().__init__(message)

    DEFAULT_USER_ROLE_NAME = "user"
    DEFAULT_BOT_ROLE_NAME = "bot"
    DEFAULT_SYSTEM_ROLE_NAME = "system"

    def __init__(
            self,
            initial: List[dict] = None,
            system: str = DEFAULT_SYSTEM_ROLE_NAME,
            user: str = DEFAULT_USER_ROLE_NAME,
            bot: str = DEFAULT_BOT_ROLE_NAME
    ):
        self.messages: List[dict] = initial or []
        self.systemRoleName = system
        self.userRoleName = user
        self.botRoleName = bot
        self.bookmarks: List[Bookmark] = []
        self.archives: Dict[str, Archive] = dict()

        for m in self.messages:
            if m["role"] not in [self.systemRoleName, self.userRoleName, self.botRoleName]:
                raise self.InvalidRoleError(f"Invalid role: {m['role']}")

    def add(self, role: str, content: str, replace: bool = True) -> "ChatPrompt":
        if replace and self.messages and self.messages[-1]["role"] == role:
            self.replace(content)
        else:
            self.messages.append({"role": role, "content": content})
        return self

    def replace(self, content: str, index: int = -1) -> "ChatPrompt":
        if self.messages:
            self.messages[index]["content"] = content
            return self
        else:
            raise RuntimeError("Cannot replace empty messages")

    def insert(self, other: ChatPrompt | List[dict], at: int = None) -> "ChatPrompt":
        messages = other.messages if isinstance(other, ChatPrompt) else other

        if messages:
            if at is None:
                self.messages += messages
            else:
                self.messages = self.messages[:at] + messages + self.messages[at:]
        return self

    def delete(self, begin: int = -1, end: int = None) -> "ChatPrompt":
        front = self.messages[:begin] if begin else []
        back = self.messages[end:] if end else []
        self.messages = front + back
        return self

    def user(self, content: str, replace: bool = True) -> "ChatPrompt":
        return self.add(self.userRoleName, content, replace)

    def bot(self, content: str, replace: bool = True) -> "ChatPrompt":
        return self.add(self.botRoleName, content, replace)

    def system(self, content: str, replace: bool = True) -> "ChatPrompt":
        return self.add(self.systemRoleName, content, replace)

    def length(self) -> int:
        return len(self.messages)

    def getContents(self, condition: Callable[[dict], bool] = lambda m: True) -> List[str]:
        return [m["content"] for m in self.messages if condition(m)]

    def getContent(self, index: int) -> str | None:
        try:
            return self.messages[index]["content"]
        except IndexError:
            return None

    def getRole(self, index: int) -> str | None:
        try:
            return self.messages[index]["role"]
        except IndexError:
            return None

    def getUserContents(self) -> List[str]:
        return self.getContents(lambda m: m["role"] == self.userRoleName)

    def getBotContents(self) -> List[str]:
        return self.getContents(lambda m: m["role"] == self.botRoleName)

    def getSystemContents(self) -> List[str]:
        return self.getContents(lambda m: m["role"] == self.systemRoleName)

    def spawn(self, initial: List[dict] = None) -> "ChatPrompt":
        if initial:
            initial = initial.copy()
        return ChatPrompt(initial=initial, system=self.systemRoleName, user=self.userRoleName, bot=self.botRoleName)

    def bookmark(self, name: str, at: int = -1):
        if at < 0:
            at += self.length()
        if at < 0 or at >= self.length():
            raise IndexError(f"Index {at} out of range (length={self.length()}")

        bm = Bookmark(name=name, index=at, of=self)
        bisect.insort_right(self.bookmarks, bm)

    def slice(self, at: str | int) -> "ChatPrompt":
        if isinstance(at, int):
            cut, bookmark = at, self.bookmarks[at]
        else:
            try:
                cut, bookmark = next((i, bm) for i, bm in enumerate(self.bookmarks) if at == bm.name)
            except StopIteration:
                raise IndexError(f"Bookmark {at} not found")

        trailingMessages = self.messages[bookmark.index + 1:]
        self.messages = self.messages[:bookmark.index + 1]
        trailingBookmarks = self.bookmarks[cut + 1:]
        self.bookmarks = self.bookmarks[:cut + 1]

        sliced = self.spawn(initial=trailingMessages)
        for bm in trailingBookmarks:
            sliced.bookmark(bm.name, bm.index - bookmark.index - 1)
            if bm.name in self.archives:
                sliced.archives[bm.name] = self.archives.pop(bm.name)

        if bookmark.name not in self.archives:
            self.archives[bookmark.name] = Archive(bookmark.name, self)
        self.archives[bookmark.name].add(sliced)

        return sliced

    def toJSON(self):
        return {
            "messages": self.messages,
            "systemRoleName": self.systemRoleName,
            "userRoleName": self.userRoleName,
            "botRoleName": self.botRoleName,
            "bookmarks": [bm.toJSON() for bm in self.bookmarks],
            "archives": {name: self.archives[name].toJSON() for name in self.archives}
        }

    @classmethod
    def fromJSON(cls, properties: dict) -> "ChatPrompt":
        prompt = ChatPrompt(
            initial=properties["messages"],
            system=properties["systemRoleName"],
            user=properties["userRoleName"],
            bot=properties["botRoleName"],
        )

        for bm in properties["bookmarks"]:
            prompt.bookmarks.append(Bookmark.fromJSON(prompt, bm))

        for arch in properties["archives"]:
            prompt.archives[arch] = Archive.fromJSON(prompt, properties["archives"][arch])

        return prompt

    def show(self):
        SHOWN_CONTENT_LENGTH = 60

        for i, m in enumerate(self.messages):
            if len(m["content"]) <= SHOWN_CONTENT_LENGTH:
                head = re.sub(r"\s+", " ", m["content"])
                tail = ""
            else:
                head = re.sub(r"\s+", " ", m["content"].strip()[:SHOWN_CONTENT_LENGTH // 2]) + " ... "
                tail = re.sub(r"\s+", " ", m["content"].strip()[-SHOWN_CONTENT_LENGTH // 2:])
            print(f"{i:3d}: ({m['role'][0]}) {head}{tail}")
