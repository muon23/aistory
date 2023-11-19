import bisect
import itertools
import json
import unittest

from cjw.aistory.utilities.ChatPrompt import ChatPrompt, Bookmark


class ChatPromptTest(unittest.TestCase):
    def test_basic(self):
        prompt = ChatPrompt(bot="assistant")
        prompt.system("system content")
        prompt.user("user content")
        prompt.user("user content 1")
        prompt.bot("bot content 2")
        self.assertEqual(prompt.getContent(2), "bot content 2")
        self.assertEqual(prompt.getRole(2), "assistant")
        self.assertEqual(prompt.getUserContents(), ["user content 1"])

        prompt.user("user content 3").bot("bot content 4")
        prompt.user("user content 5").bot("bot content 6")
        prompt.user("user content 7").bot("bot content 8")
        self.assertEqual(prompt.length(), 9)

        prompt.replace("bot content 6-1", 6)
        self.assertEqual(prompt.getContent(6), "bot content 6-1")

        prompt2 = ChatPrompt().user("user extra")
        prompt.insert(prompt2)
        prompt.insert(prompt2, 0)
        prompt.insert(prompt2, -1)
        self.assertEqual(prompt.length(), 12)
        self.assertEqual(prompt.getContent(11), "user extra")
        self.assertEqual(prompt.getContent(10), "user extra")
        self.assertEqual(prompt.getContent(0), "user extra")

        prompt.delete(10, 11)
        prompt.delete(0)
        self.assertNotIn("user content", prompt.getContents())

    def test_bookmarks(self):
        messages = list(itertools.chain(*[[
            {"role": "user", "content": f"user {2 * i}"},
            {"role": "bot", "content": f"bot {2 * i + 1}"},
        ] for i in range(10)]))
        prompt = ChatPrompt(initial=messages)
        prompt.bookmark("bm15", 15)

        sliced1 = prompt.slice("bm15")

        print("=== Before 15 ===")
        prompt.show()
        print("=== After 15 ===")
        sliced1.show()

        prompt.bookmark("a_bm5", 5)
        prompt.bookmark("b_bm9", 9)
        prompt.bookmark("c_bm8", 8)
        prompt.slice("c_bm8")

        self.assertEqual(len(prompt.bookmarks), 2)  # a_bm5, c_bm8
        self.assertEqual(len(prompt.archives), 1)   # c_bm8

        promptJson = prompt.toJSON()
        promptJsonStr = json.dumps(promptJson, indent=4)
        print(promptJsonStr)
        promptJsonBack = json.loads(promptJsonStr)
        promptBack = ChatPrompt.fromJSON(promptJsonBack)

        self.assertEqual(prompt.length(), promptBack.length())
        self.assertEqual(len(prompt.archives), len(promptBack.archives))

        print("done")

    def test_bookmark_ordering(self):
        prompt = ChatPrompt()
        bookmarks = [
            Bookmark(name="zzz", index=1, of=prompt),
            Bookmark(name="aaa", index=3, of=prompt),
            Bookmark(name="yyy", index=5, of=prompt),
            Bookmark(name="bbb", index=7, of=prompt),
        ]

        bisect.insort_right(bookmarks, Bookmark(name="ppp", index=4, of=prompt))

        self.assertEqual(bookmarks[2].name, "ppp")


if __name__ == '__main__':
    unittest.main()
