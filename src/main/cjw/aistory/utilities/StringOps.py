from typing import Tuple, Optional, List


def parse_first_top_level_parentheses(s: str, left: str = "([{", right: str = ")]}") \
        -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Find the first top-level matching pair of parentheses.
    (The original code was written by GPT-4 with a bug, and was debugged by CJ Wang, demonstrating how AI and human shall work together. :) )
    :param s: A given string to parse
    :param left: Possible left parentheses.  Default "([{<".
    :param right: Possible matching right parentheses of the left ones.  Default ")]}>".
    The i-th character in "right" shall match the i-th character in "left".
    :return: A triplet of strings.  The first contains the string before the matched left parenthesis.
    The second contains the matched string in between the parentheses (including the parentheses).
    The third contains the string after the right parenthesis.
    It returns all Nones if nothing was matched
    """

    if len(left) != len(right):
        raise ValueError("Number of valid left parentheses does not match that of the right.")

    # Stack to store the positions of parentheses
    symbol_stack = []
    position_stack = []
    # Initialize result indices
    start = -1
    end = -1

    # Traverse the input string
    for i in range(len(s)):
        if s[i] in right:
            if symbol_stack:
                matching_left = left[right.index(s[i])]
                if matching_left in symbol_stack:  # Found a matching pair
                    while symbol_stack[-1] != matching_left:
                        symbol_stack.pop()
                        position_stack.pop()

                    symbol_stack.pop()
                    start = position_stack.pop()  # Include the opening parenthesis
                    end = i  # Include the closing parenthesis

                if not symbol_stack:  # We are at the top level
                    break

        if s[i] in left:
            symbol_stack.append(s[i])
            position_stack.append(i)

    # Check if there are valid parentheses
    if start == -1 or end == -1:
        return s, None, None

    # Return substrings: before, between, and after the longest valid parentheses
    before = s[:start]
    between = s[start:end + 1]
    after = s[end + 1:]

    return before, between, after


def join_with_conjunction(items: List[str], useAnd: bool = True) -> str:
    conjunction = "and" if useAnd else "or"
    if len(items) > 2:
        return ', '.join(items[:-1] + [f"and {items[-1]}"])
    elif len(items) > 1:
        return f"{items[0]} {conjunction} {items[1]}"
    elif items:
        return items[0]
    else:
        return ""
