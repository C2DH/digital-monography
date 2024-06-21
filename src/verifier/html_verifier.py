import datetime
import pathlib
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
MSG_PROBLEMS = {
    HEADINGS: {
        "check_h_for_title_case": "All headings should be title cased.",
        "check_h_no_trailing_dot": "Headings should not end with a trailing dot.",
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
        self.problem = problem
        self.recommend = recommend
        self.elem = elem
        self.timestamp = timestamp
        self.fn = fn
        self.tags = tags
        self.line = elem.sourceline
        self.pos = elem.sourcepos

    def to_json(self) -> VerifierMessageJson:
        return {
            "problem": self.problem,
            "recommend": self.recommend,
            "fn": self.fn,
            "html": str(self.elem),
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

    def _check_h_for_title_case(self, tag: bs4.element.Tag):
        return tag.text != tag.text.title() and IS_HEADING_TITLE_CASED_REQUIRED

    def _check_h_no_trailing_dot(self, tag: bs4.element.Tag):
        return tag.text.strip().endswith(".")

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
