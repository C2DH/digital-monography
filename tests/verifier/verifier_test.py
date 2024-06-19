import collections
import pathlib

from src.verifier.verifier import HtmlVerifier
from src.verifier.verifier import MSG_PROBLEMS, HEADINGS


class TestFileBreakingVerificationRules:
    fp = pathlib.Path("tests") / "_fixtures" / "verification_breaks.html"

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "r") as f:
            md = f.read()
        # print(md)
        cls.warnings = collections.defaultdict(list)
        verifer = HtmlVerifier()
        cls.result = verifer.verify(md, cls.fp)
        cls.res_json = verifer.to_json()
        for war in cls.res_json:
            if HEADINGS in war["tags"]:
                cls.warnings[HEADINGS].append(war)

    def test_check_h_for_title_case(self):
        is_any = any(
            w
            for w in self.warnings[HEADINGS]
            if w["html"].startswith("<h2>Oh no, the first Heading is level 2")
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_for_title_case"]
        )
        assert is_any

    def test_check_h_no_trailing_dot(self):
        is_any = any(
            w
            for w in self.warnings[HEADINGS]
            if w["html"].endswith(".</h2>")
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_no_trailing_dot"]
        )
        assert is_any
