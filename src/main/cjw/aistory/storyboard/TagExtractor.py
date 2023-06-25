from typing import List, Tuple

from cjw.aistory.utilities import StringOps


class TagExtractor:
    """
    The TagExtractor class extracts tags from a string.
    """

    LEFT = "<"
    RIGHT = ">"

    @classmethod
    def extract(cls, line: str) -> Tuple[List[str], str]:
        """
        Extract tags from a line and return the tags and the line with tags removed.

        Args:
            line: The input line.

        Returns:
            Tuple[List[str], str]: The extracted tags and the line with tags removed.
        """
        tags = []
        tagRemoved = ""
        after = line
        while after:
            before, tag, after = StringOps.parse_first_top_level_parentheses(after, cls.LEFT, cls.RIGHT)
            tagRemoved += before
            if tag:
                tags.append(tag)

        return tags, tagRemoved.strip()
