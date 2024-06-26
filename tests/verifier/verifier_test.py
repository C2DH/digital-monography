import collections
import pathlib

from src.verifier.html_verifier import HtmlVerifier
from src.verifier.html_verifier import MSG_PROBLEMS, HEADINGS
from src.verifier.main import _fromtimestamp


class TestFileBreakingVerificationRules:
    fp = pathlib.Path("tests") / "_fixtures" / "verification_breaks.html"

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "r") as f:
            html = f.read()
        cls.warnings = collections.defaultdict(list)
        verifer = HtmlVerifier()
        timestamp = _fromtimestamp("2024-06-26T09:53:49.380Z")
        result = verifer.verify(html, cls.fp, timestamp)
        cls.res_json = result.to_json()
        for war in cls.res_json:
            if HEADINGS in war["tags"]:
                cls.warnings[HEADINGS].append(war)

    def test_check_h_for_title_case(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if w["curr_elem"].startswith("<h2>Oh no, the first Heading is level 2")
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_for_title_case"]
        )
        assert warning["fn"] == "verification_breaks.html"
        assert warning["next_elem"].startswith("<h4>Heading 4. Where is level 3?")
        assert warning["prev_elem"].startswith(
            "<p>The file should always start with Heading 1"
        )

    def test_check_h_no_trailing_dot(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if w["curr_elem"].endswith(".</h2>")
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_no_trailing_dot"]
        )
        assert warning["fn"] == "verification_breaks.html"
        assert warning["prev_elem"].startswith(
            "<p>The file should always start with Heading 1.",
        )
        assert warning["next_elem"].startswith(
            "<h4>Heading 4. Where is level 3?",
        )
