import bs4
import datetime
import json
import pathlib
import typing as t


from src._common.constants import CLS_METADATA_TABLE_JSONDATA
from src._common.metadata import DocumentMetadata
from verif_warnings import MessagesJson, VerifierMessages


CAPTION_TYPES = ["Figure", "Table", "Graph"]
IS_HEADING_TITLE_CASED_REQUIRED = True
ASSETS = "assets"
CAPTIONS = "captions"
FOOTNOTES = "footnotes"
HEADINGS = "headings"
PARAGRAPHS = "paragraphs"
LINKS = "links"
TABLES = "tables"
METADATA_TABLES = "metadata_tables"
MSG_PROBLEMS = {
    HEADINGS: {},
    PARAGRAPHS: {},
    CAPTIONS: {},
    LINKS: {
        "check_a_is_http": "Links should point to websites using secure https over http.",
        "check_a_not_archived": "Links should point to websites archived using the Internet Archive.",
    },
    TABLES: {},
}


class HtmlVerifier:
    def __init__(self) -> None:
        self.soup: t.Optional[bs4.BeautifulSoup] = None
        self._links: bs4.element.Tag = []
        self._messages: VerifierMessages = VerifierMessages()
        self._metadata: DocumentMetadata = DocumentMetadata()

    def to_json(self, md: bool = False) -> MessagesJson:
        return self._messages.to_json(md)

    def sort(self) -> None:
        self._messages.sort(key=lambda msg: (msg["line"], msg["pos"]))

    def verify(
        self, html: str, fp: pathlib.Path, slug: str, timestamp: datetime.datetime
    ) -> VerifierMessages:
        self._fp = fp
        self._slug = slug
        self._timestamp = timestamp
        self.soup = bs4.BeautifulSoup(html, "html.parser")
        self._mark_html_elements_recursively(self.soup)
        self._apply_links_verification()
        return self._messages

    def _mark_html_elements_recursively(
        self, node: bs4.element.PageElement, lvl=0
    ) -> None:
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
                if child.name == "a":
                    self._links.append(child)
                elif (
                    child.name == "script"
                    and CLS_METADATA_TABLE_JSONDATA in child.attrs.get("class", [])
                ):
                    # TODO: read document state form script tag
                    self._metadata.from_json(json.loads(child.text))
            self._mark_html_elements_recursively(child, lvl + 1)

    # links #############################################################################

    def _apply_links_verification(self) -> None:
        for link in self._links:
            link: bs4.element.Tag
            href = link.get("href", "")
            if self._check_a_is_http(href):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[LINKS]["check_a_is_http"],
                    recommend=f"If possible, change \"`{href}`\" to \"{href.replace('http:', 'https:', 1)}\".",
                    elem=link,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[LINKS],
                )
            if self._check_a_not_archived(href):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[LINKS]["check_a_not_archived"],
                    recommend=f'Go to "https://wayback-api.archive.org/" and replace "`{href}`" in your manuscript with the archived link.',
                    elem=link,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[LINKS],
                )

    def _check_a_is_http(self, href: str) -> bool:
        return href.startswith("http://")

    def _check_a_not_archived(self, href: str) -> bool:
        return href.startswith("http") and not href.startswith(
            "https://web.archive.org/"
        )
