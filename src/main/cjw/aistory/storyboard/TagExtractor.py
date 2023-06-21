from typing import List, Tuple

from cjw.aistory.utilities import StringOps


class TagExtractor:
    LEFT = "<"
    RIGHT = ">"

    @classmethod
    def extract(cls, line: str) -> Tuple[List[str], str]:
        tags = []
        tagRemoved = ""
        after = line
        while after:
            before, tag, after = StringOps.parse_first_top_level_parentheses(after, cls.LEFT, cls.RIGHT)
            tagRemoved += before
            if tag:
                tags.append(tag)

        return tags, tagRemoved.strip()

