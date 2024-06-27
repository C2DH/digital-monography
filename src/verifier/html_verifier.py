import datetime
import pathlib
import uuid
import bs4
import re
import logging
import typing as t


try:
    from .constants import IS_DEBUG
except Exception as e:
    from constants import IS_DEBUG


IS_HEADING_TITLE_CASED_REQUIRED = True
HEADINGS = "headings"
FOOTNOTES = "footnotes"
MSG_PROBLEMS = {
    HEADINGS: {
        "check_h_for_title_case": "All headings should be title cased.",
        "check_h_no_trailing_dot": "Headings should not end with a trailing dot.",
        "check_h_no_footnotes": "Headings must not contain any footnotes.",
        "check_h_for_duplicates": "Duplicate headings found.",
    }
}


if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}.log")
    log_target.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_target,
        encoding="utf-8",
        level=logging.DEBUG,
        format="%(asctime)s::%(name)s::%(levelname)s::%(message)s",
    )
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class VerifierMessageJson(t.TypedDict):
    problem: str
    action: str
    fn: str
    line: int
    pos: int


class VerifierMessage:
    def __init__(
        self,
        problem: str,
        recommend: str,
        elem: bs4.element.Tag,
        timestamp: datetime.datetime,
        fn: str,
        tags: list[str],
    ) -> None:
        self.id = uuid.uuid4().hex[:8]
        self.problem = problem
        self.recommend = recommend
        self.prev_elem = self._find_prev_elem(elem)
        self.curr_elem = elem
        self.next_elem = self._find_next_elem(elem)
        self.timestamp = timestamp
        self.fn = fn
        self.tags = tags
        self.line = elem.sourceline
        self.pos = elem.sourcepos

    def _find_prev_elem(
        self, elem: bs4.element.Tag
    ) -> t.Optional[bs4.element.PageElement]:
        """
        Find previous_sibling, ommiting empty ones.
        """
        prev = elem.previous_sibling
        for i in range(5):  # don't look for more than 5 siblings
            if hasattr(prev, "text") and prev.text.isspace():
                prev = prev.previous_sibling
            else:
                break
        return prev

    def _find_next_elem(
        self, elem: bs4.element.Tag
    ) -> t.Optional[bs4.element.PageElement]:
        """
        Find next_sibling, ommiting empty ones.
        """
        next = elem.next_sibling
        for i in range(5):  # don't look for more than 5 siblings
            if hasattr(next, "text") and next.text.isspace():
                next = next.next_sibling
            else:
                break
        return next

    def to_json(self) -> VerifierMessageJson:
        return {
            "id": self.id,
            "problem": self.problem,
            "recommend": self.recommend,
            "fn": self.fn,
            "prev_elem": str(self.prev_elem),
            "curr_elem": str(self.curr_elem),
            "next_elem": str(self.next_elem),
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "line": self.line,
            "pos": self.pos,
        }


class VerifierMessages:
    def __init__(self):
        self._messages = []

    def add_msg(
        self,
        problem: str,
        recommend: str,
        elem: bs4.element.Tag,
        fn: str,
        timestamp: datetime.datetime,
        tags: list[str],
    ) -> None:
        self._messages.append(
            VerifierMessage(
                problem=problem,
                recommend=recommend,
                elem=elem,
                timestamp=timestamp,
                fn=fn,
                tags=tags,
            )
        )

    def to_json(self) -> list[VerifierMessageJson]:
        return [msg.to_json() for msg in self._messages]


class HtmlVerifier:
    def __init__(self) -> None:
        self._atags = []
        self._captions = []
        self._headings = []
        self._tables = []
        self._messages = VerifierMessages()

    def summary(self):
        pass

    def stats(self):
        pass

    def verify(
        self, html: str, fp: pathlib.Path, timestamp: datetime.datetime
    ) -> VerifierMessages:
        self._fp = fp
        self._timestamp = timestamp
        soup = bs4.BeautifulSoup(html, "html.parser")
        print(soup)
        self._mark_html_elements_recursively(soup)
        self._apply_heading_verification()
        self._apply_atags_verification()
        # self._apply_assets_verification()
        self._apply_metadatatables_verification()
        self._apply_tables_verification()
        # self._apply_captions_verification()
        self._apply_hyperlinks_verification()
        return self._messages

    def _mark_html_elements_recursively(self, node, lvl=0):
        """
        Before applying the verification, this function traverses the tree and
        puts relevant bs4.Tag elements inside respective lists.
        Verification is then applied on the elements from the lists.
        """
        if not hasattr(node, "children"):
            return
        for child in node.children:
            if isinstance(child, bs4.element.Tag):
                if re.match(r"^h[0-9]*$", child.name):
                    self._headings.append(child)
                elif child.name == "a":
                    self._atags.append(child)
                elif child.name == "table":
                    self._tables.append(child)
                    # TODO: add caption verification
                    # elif beginning of the string matches "Figure <num>: text" or later maybe <caption>
                    #   captions.append(child)
            self._mark_html_elements_recursively(child, lvl + 1)

    # headings

    def _apply_heading_verification(self):
        self._unique_headings = []
        for tag in self._headings:
            if self._check_h_for_title_case(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_for_title_case"],
                    recommend=f"Consider changing the heading '{tag.text}' to '{tag.text.title()}'.",
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            if self._check_h_no_trailing_dot(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_no_trailing_dot"],
                    recommend=f"Consider removing the '.' character at the end of the heading.",
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            if self._check_h_no_footnotes(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_no_footnotes"],
                    recommend=f"Please remove the footnote from the heading '{tag.text}'.",
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS, FOOTNOTES],
                )
            if self._check_h_for_duplicates(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_for_duplicates"],
                    recommend=f"There should be no two headings with the same text. Please rephrase '{tag.text}'.",
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )

    def _check_h_for_title_case(self, tag: bs4.element.Tag):
        return tag.text != tag.text.title() and IS_HEADING_TITLE_CASED_REQUIRED

    def _check_h_no_trailing_dot(self, tag: bs4.element.Tag):
        return tag.text.strip().endswith(".")

    def _check_h_no_footnotes(self, tag: bs4.element.Tag):
        """
        Check for an anchor tag in a superscript tag. E.g.:
        <h1>No Footnotes In Headings<sup><a href="#footnote-1" id="footnote-ref-1">[1]</a></sup></h1>
        """
        for sup in tag.find_all("sup"):
            for a in sup.find_all("a"):
                if "footnote" in str(a):
                    return True
        return False

    def _check_h_for_duplicates(self, tag: bs4.element.Tag):
        if tag.text in self._unique_headings:
            return True
        self._unique_headings.append(tag.text)
        return False

    # anchor tags

    def _apply_atags_verification(self):
        pass

    # def _apply_assets_verification(self):
    #     pass

    def _apply_metadatatables_verification(self):
        pass

    def _apply_tables_verification(self):
        pass

    # def _apply_captions_verification(self):
    #     pass

    def _apply_hyperlinks_verification(self):
        pass
