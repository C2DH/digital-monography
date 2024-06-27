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
        "check_h_no_h1_at_start": "Every file should start with Heading of level 1.",
        "check_h_first_h_not_h1": "First Heading should be of level 1.",
        "check_h_h1_after_start": "You should place Headings of level 1 only at the beginning of the file.",
        "check_h_not_sequential": "Heading levels should only increment by one level at a time.",
        "check_h_no_title_case": "All headings should be title cased.",
        "check_h_with_trailing_dot": "Headings should not end with a trailing dot.",
        "check_h_with_footnotes": "Headings must not contain any footnotes.",
        "check_h_if_gte_6": "Heading of level 6 and above are not supported.",
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
        self._headings_lvls = []
        self._tables = []
        self._messages = VerifierMessages()

    def summary(self):
        pass

    def stats(self):
        pass

    def verify(
        self, html: str, fp: pathlib.Path, timestamp: datetime.datetime
    ) -> VerifierMessages:
        self._first_tag = None
        self._fp = fp
        self._timestamp = timestamp
        self.soup = bs4.BeautifulSoup(html, "html.parser")
        print(self.soup)
        self._mark_html_elements_recursively(self.soup)
        self._apply_heading_verification()
        self._apply_atags_verification()
        # self._apply_assets_verification()
        self._apply_metadatatables_verification()
        self._apply_tables_verification()
        # self._apply_captions_verification()
        self._apply_hyperlinks_verification()
        return self._messages

    def _mark_html_elements_recursively(self, node: bs4.element.PageElement, lvl=0):
        """
        Before applying the verification, this function traverses the tree and
        puts relevant bs4.Tag elements inside respective lists
        or marks those elements as first html elements in the file.
        Verification is then applied on the marked elements.
        """
        if not hasattr(node, "children"):
            return
        for child in node.children:
            if isinstance(child, bs4.element.Tag):
                if self._first_tag is None:
                    self._first_tag = child
                if re.match(r"^h[0-9]*$", child.name):
                    self._headings.append(child)
                    self._headings_lvls.append(int(re.findall(r"\d+", child.name)[0]))
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
        self._h_stack = []
        if self._check_h_no_h1_at_start(self._first_tag):
            shrt_txt = (
                self._first_tag.text[:25]
                if len(self._first_tag.text) > 25
                else self._first_tag.text
            )
            self._messages.add_msg(
                problem=MSG_PROBLEMS[HEADINGS]["check_h_no_h1_at_start"],
                recommend=f"Here, it begins with '{shrt_txt}...' which does not have a Heading 1 style.",
                elem=self._first_tag,
                fn=self._fp.name,
                timestamp=self._timestamp,
                tags=[HEADINGS],
            )
        for i in range(len(self._headings)):
            tag = self._headings[i]
            while self._h_stack and self._h_stack[-1] > self._headings_lvls[i]:
                self._h_stack.pop()
            if self._h_stack and self._headings_lvls[i] - self._h_stack[-1] > 1:
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_not_sequential"],
                    recommend=f"Heading {str(self._headings_lvls[i])} ('{tag.text}') is placed after heading level {str(self._h_stack[-1])}. Consider changing the former to style 'Heading {str(self._h_stack[-1] + 1)}'.",
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            if len(self._h_stack) == 0 and self._headings_lvls[i] != 1:
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_first_h_not_h1"],
                    recommend=f"Consider changing the style of '{tag.text}' or '{self._first_tag.text}' to 'Heading 1'.",
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            if i > 1 and self._headings_lvls[i] == 1:
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_h1_after_start"],
                    recommend=f"Consider changing level of '{tag.text}' or splitting file into two as there should be only one top level heading per file.",
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            self._h_stack.append(self._headings_lvls[i])

            if self._check_h_no_title_case(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_no_title_case"],
                    recommend=f"Consider changing the heading '{tag.text}' to '{tag.text.title()}'.",
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            if self._check_h_with_trailing_dot(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_with_trailing_dot"],
                    recommend=f"Consider removing the '.' character at the end of the heading.",
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            if self._check_h_with_footnotes(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_with_footnotes"],
                    recommend=f"Please remove the footnote from the heading '{tag.text}'.",
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS, FOOTNOTES],
                )
            if self._check_h_if_gte_6(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_if_gte_6"],
                    recommend=f"Consider changing the style of '{tag.text}' to Heading 5 or lower.",
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
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

    def _check_h_no_h1_at_start(self, tag: bs4.element.Tag):
        try:
            is_heading = re.match(r"^h[0-9]*$", tag.name)
            tag_nums = re.findall(r"\d+", tag.name)
            if is_heading and tag_nums and int(tag_nums[0]) == 1:
                return False
        except ValueError as e:
            return False
        else:
            return True

    def _check_h_no_title_case(self, tag: bs4.element.Tag):
        return tag.text != tag.text.title() and IS_HEADING_TITLE_CASED_REQUIRED

    def _check_h_with_trailing_dot(self, tag: bs4.element.Tag):
        return tag.text.strip().endswith(".")

    def _check_h_with_footnotes(self, tag: bs4.element.Tag):
        """
        Check for an anchor tag in a superscript tag. E.g.:
        <h1>No Footnotes In Headings<sup><a href="#footnote-1" id="footnote-ref-1">[1]</a></sup></h1>
        """
        for sup in tag.find_all("sup"):
            for a in sup.find_all("a"):
                if "footnote" in str(a):
                    return True
        return False

    def _check_h_if_gte_6(self, tag: bs4.element.Tag):
        nums = re.findall(r"\d+", tag.name)
        if nums and int(nums[0]) >= 6:
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
