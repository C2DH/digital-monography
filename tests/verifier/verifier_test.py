import collections
import pathlib
from pprint import pprint

from src.verifier.html_verifier import HtmlVerifier
from src.verifier.html_verifier import MSG_PROBLEMS, HEADINGS, CAPTIONS, LINKS
from src.verifier.main import _fromtimestamp


class TestHeadingsLinksAndCaptionsBreakingVerificationRules:
    fp = pathlib.Path("tests") / "_fixtures" / "verify_h_a_cap.html"

    @classmethod
    def setup_class(cls):
        with open(cls.fp, "r") as f:
            cls.html = f.read()
        cls.warnings = collections.defaultdict(list)
        cls.verifer = HtmlVerifier()
        timestamp = _fromtimestamp("2024-06-26T09:53:49.380Z")
        result = cls.verifer.verify(cls.html, cls.fp, timestamp)
        cls.res_json = result.to_json()
        for war in cls.res_json:
            if HEADINGS in war["tags"]:
                cls.warnings[HEADINGS].append(war)
            if CAPTIONS in war["tags"]:
                cls.warnings[CAPTIONS].append(war)
            if LINKS in war["tags"]:
                cls.warnings[LINKS].append(war)

    # headings ########################################################################

    def test_check_h_no_h1_at_start(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if w["curr_elem"].startswith(
                "<p>The file should always start with Heading 1"
            )
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_no_h1_at_start"]
        )
        assert warning
        assert warning["fn"] == "verify_h_a_cap.html"

    def test_check_h_first_h_not_h1(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if w["curr_elem"].startswith("<h2>Oh no, the first Heading is level 2.")
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_first_h_not_h1"]
        )
        assert warning
        assert warning["fn"] == "verify_h_a_cap.html"

    def test_check_h_h1_after_start__1(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if "Heading 1 Should Be At The Beginning Of The File Only!"
            in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_h1_after_start"]
        )
        assert warning
        assert warning["fn"] == "verify_h_a_cap.html"

    def test_check_h_h1_after_start__2(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if "There Should Be Only One Heading 1" in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_h1_after_start"]
        )
        assert warning
        assert warning["fn"] == "verify_h_a_cap.html"

    def test_check_h_not_sequential__1(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if "Heading 4. Where is level 3?" in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_not_sequential"]
        )
        assert warning
        assert warning["fn"] == "verify_h_a_cap.html"

    def test_check_h_not_sequential__2(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if "Heading 6. Where 5?" in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_not_sequential"]
        )
        assert warning
        assert warning["fn"] == "verify_h_a_cap.html"

    def test_check_h_no_title_case(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if w["curr_elem"].startswith("<h2>Oh no, the first Heading is level 2")
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_no_title_case"]
        )
        assert warning["fn"] == "verify_h_a_cap.html"
        assert warning["next_elem"].startswith("<h4>Heading 4. Where is level 3?")
        assert warning["prev_elem"].startswith(
            "<p>The file should always start with Heading 1"
        )

    def test_check_h_with_trailing_dot(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if w["curr_elem"].endswith(".</h2>")
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_with_trailing_dot"]
        )
        assert warning["fn"] == "verify_h_a_cap.html"
        assert warning["prev_elem"].startswith(
            "<p>The file should always start with Heading 1.",
        )
        assert warning["next_elem"].startswith(
            "<h4>Heading 4. Where is level 3?",
        )

    def test_check_h_with_footnotes(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if "No Footnotes In Headings" in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_with_footnotes"]
        )
        assert warning
        assert warning["fn"] == "verify_h_a_cap.html"

    def test_check_h_if_gte_6(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if "Heading 6" in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_if_gte_6"]
        )
        assert warning
        assert warning["fn"] == "verify_h_a_cap.html"

    def test_check_h_for_duplicates(self):
        warning = next(
            w
            for w in self.warnings[HEADINGS]
            if "Heading 4" in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[HEADINGS]["check_h_for_duplicates"]
        )
        assert warning
        assert warning["fn"] == "verify_h_a_cap.html"

    # captions ########################################################################

    def test_check_cap_no_colon(self):
        warning = next(
            w
            for w in self.warnings[CAPTIONS]
            if "Figure VII second caption" in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[CAPTIONS]["check_cap_no_colon"]
        )
        assert warning
        assert warning["fn"] == "verify_h_a_cap.html"

    def test_check_cap_no_number(self):
        is_incorrect_warning = None
        is_correct_no_warning = None
        for w in self.warnings[CAPTIONS]:
            if (
                "Figure VII second caption" in w["curr_elem"]
                and w["problem"] == MSG_PROBLEMS[CAPTIONS]["check_cap_no_number"]
            ):
                is_incorrect_warning = w
            if (
                "Figure 3: Almost correct caption." in w["curr_elem"]
                and w["problem"] == MSG_PROBLEMS[CAPTIONS]["check_cap_no_number"]
            ):
                is_correct_no_warning = w
        assert is_incorrect_warning
        assert is_correct_no_warning is None

    def test_check_cap_no_bold(self):
        is_incorrect_warning = None
        is_correct_no_warning = None
        for w in self.warnings[CAPTIONS]:
            if (
                "Figure 3: Almost correct caption." in w["curr_elem"]
                and w["problem"] == MSG_PROBLEMS[CAPTIONS]["check_cap_no_bold"]
            ):
                is_incorrect_warning = w
            if (
                "Correct caption" in w["curr_elem"]
                and w["problem"] == MSG_PROBLEMS[CAPTIONS]["check_cap_no_bold"]
            ):
                is_correct_no_warning = w
        assert is_incorrect_warning
        assert is_correct_no_warning is None

    def test_check_cap_no_end_dot(self):
        warning = next(
            w
            for w in self.warnings[CAPTIONS]
            if "Figure VII second caption" in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[CAPTIONS]["check_cap_no_end_dot"]
        )
        assert warning
        assert warning["fn"] == "verify_h_a_cap.html"

    def test_check_cap_dupl_num(self):
        warning = next(
            w
            for w in self.warnings[CAPTIONS]
            if "Duplicated caption number" in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[CAPTIONS]["check_cap_dupl_num"]
        )
        assert warning

    def test_check_cap_nonsequantial_num(self):
        warning = next(
            w
            for w in self.warnings[CAPTIONS]
            if "Almost correct caption" in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[CAPTIONS]["check_cap_nonsequantial_num"]
        )
        assert warning
        warning = next(
            w
            for w in self.warnings[CAPTIONS]
            if "Duplicated caption number" in w["curr_elem"]
            and w["problem"] == MSG_PROBLEMS[CAPTIONS]["check_cap_nonsequantial_num"]
        )
        assert warning

    # links ###########################################################################

    def test_check_a_is_http(self):
        is_incorrect_warning = None
        is_correct_no_warning = None
        for w in self.warnings[LINKS]:
            if (
                "http://example.com/" in w["curr_elem"]
                and w["problem"] == MSG_PROBLEMS[LINKS]["check_a_is_http"]
            ):
                is_incorrect_warning = w
            if (
                "https://web.archive.org" in w["curr_elem"]
                and w["problem"] == MSG_PROBLEMS[LINKS]["check_a_is_http"]
            ):
                is_correct_no_warning = w
        assert is_incorrect_warning
        assert is_correct_no_warning is None

    def test_check_a_not_archived(self):
        is_incorrect_warning = None
        is_correct_no_warning = None
        for w in self.warnings[LINKS]:
            if (
                "http://example.com/" in w["curr_elem"]
                and w["problem"] == MSG_PROBLEMS[LINKS]["check_a_not_archived"]
            ):
                is_incorrect_warning = w
            if (
                "https://web.archive.org" in w["curr_elem"]
                and w["problem"] == MSG_PROBLEMS[LINKS]["check_a_not_archived"]
            ):
                is_correct_no_warning = w
        assert is_incorrect_warning
        assert is_correct_no_warning is None

    ###################################################################################


# class TestHeadingsLinksAndCaptionsBreakingVerificationRules:
#     fp = pathlib.Path("tests") / "_fixtures" / ""

#     @classmethod
#     def setup_class(cls):
#         with open(cls.fp, "r") as f:
#             cls.html = f.read()
#         cls.warnings = collections.defaultdict(list)
#         cls.verifer = HtmlVerifier()
#         timestamp = _fromtimestamp("2024-06-26T09:53:49.380Z")
#         result = cls.verifer.verify(cls.html, cls.fp, timestamp)
#         for war in result.to_json():
#             if HEADINGS in war["tags"]:
#                 cls.warnings[HEADINGS].append(war)
#             if CAPTIONS in war["tags"]:
#                 cls.warnings[CAPTIONS].append(war)
#             if LINKS in war["tags"]:
#                 cls.warnings[LINKS].append(war)

#     def test_testing(self):
#         print(self.html)
#         print("-" * 50)
#         for tag, warnings in self.warnings.items():
#             for w in warnings:
#                 print("tags \t\t", w["tags"])
#                 print("curr_elem \t", w["curr_elem"])
#                 print("problem \t", w["problem"])
#                 print("recommend \t", w["recommend"])
#                 print("-" * 50)
#         print("=" * 50)
#         pprint(self.verifer._tables)
#         assert 1 == 2
