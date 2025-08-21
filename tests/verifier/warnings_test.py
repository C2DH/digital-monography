import bs4
import random

from src.verifier.main import _fromtimestamp
from src.verifier.rules_v1 import HtmlVerifier
from src.verifier.verif_warnings import (
    FileVerificationMessage,
    GeneralVerificationMessage,
)


# class TestHtmlElementsInWarnings:
#     @classmethod
#     def setup_class(cls):
#         cls.verifier = HtmlVerifier()
#         slug = "examples"
#         timestamp = _fromtimestamp("2024-06-26T09:53:49.380Z")
#         fp = pathlib.Path("tests") / "_fixtures" / "index.html"
#         html = '<p id="p1">See </p><a id="p2"><a id="a" href="http://example.com/">a link</a></p><p id="p3">.</p>'
#         result = cls.verifier.verify(html, fp, slug, timestamp)
#         cls.res_json = result.to_json()
#         cls.link_warning = next(
#             w
#             for w in cls.res_json
#             if w["problem"] == MSG_PROBLEMS[LINKS]["check_a_not_archived"]
#         )

#     def test_href_prev_elem(self):
#         # print(self.res_json)
#         assert 1 == 54

#     def test_href_curr_elem(self):
#         # print(self.res_json)
#         curr_elem = str(self.link_warning["curr_elem"])
#         assert curr_elem == '<a href="http://example.com/" id="a">a link</a>'
#         assert 1 == 55

#     def test_href_next_elem(self):
#         print(self.res_json)
#         assert 1 == 56


class TestSortingWarnings:
    @classmethod
    def setup_class(cls):
        cls.verifier = HtmlVerifier()
        timestamp = _fromtimestamp("2024-06-26T09:53:49.380Z")
        soup = bs4.BeautifulSoup(
            '<p id="a">a</p><p id="b">b</p><p id="c">c</p>', "html.parser"
        )
        msg = FileVerificationMessage(
            problem="",
            recommend="",
            prev_elem=soup.find(id="a"),
            elem=soup.find(id="b"),
            next_elem=soup.find(id="c"),
            timestamp=timestamp,
            fn="example.html",
            tags=[],
        )
        msg_general = GeneralVerificationMessage(
            problem="",
            recommend="",
            timestamp=timestamp,
            tags=[],
        )
        msg_0_1 = msg.copy()
        msg_0_1.line, msg_0_1.pos = 0, 1
        msg_0_2 = msg.copy()
        msg_0_2.line, msg_0_2.pos = 0, 2
        msg_1_1 = msg.copy()
        msg_1_1.line, msg_1_1.pos = 1, 1
        msg_1_0 = msg.copy()
        msg_1_0.line, msg_1_0.pos = 1, 0
        msg_2_4 = msg.copy()
        msg_2_4.line, msg_2_4.pos = 2, 4
        _messages = [
            msg_1_0,
            msg_2_4,
            msg_0_2,
            msg_1_1,
            msg_0_1,
            msg_general,
        ]
        random.shuffle(_messages)
        cls.verifier._messages = _messages

    def test_sort(self):
        self.verifier.sort()
        assert self.verifier._messages[1].line == 0
        assert self.verifier._messages[1].pos == 1
        assert self.verifier._messages[2].line == 0
        assert self.verifier._messages[2].pos == 2
        assert self.verifier._messages[3].line == 1
        assert self.verifier._messages[3].pos == 0
        assert self.verifier._messages[4].line == 1
        assert self.verifier._messages[4].pos == 1
        assert self.verifier._messages[5].line == 2
        assert self.verifier._messages[5].pos == 4
        assert len(self.verifier._messages) == 6
