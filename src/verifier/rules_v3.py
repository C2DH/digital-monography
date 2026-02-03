import collections
import bs4
import datetime
import enum
import logging
import json
import pathlib
import re
import typing as t


from src._common.constants import (
    IS_DEBUG,
    METADATA_FIELDS,
    METADATA_FIELDS_KEYS,
    CLS_METADATA_TABLE,
    CLS_METADATA_TABLE_JSONDATA,
    CLS_STATE_TABLE_JSONDATA,
    FIELD_LICENSE_NAME,
    FIELD_DIGITAL_SOURCE,
    FIELD_PAPER_SOURCE,
    CLS_CAPTION,
)
from src._common.metadata import DocumentMetadata, MetadataTableDatapoint
from src._common.state import DocumentState
from src._common.html2md import convert_to_md

# from local_constants import RECOGNIZED_LICENSE_NAMES
# from path_handler import PathHandler, SUPPORTED_SUFFIXES
from verif_warnings import VerifierMessages, VerifMessage


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
    CAPTIONS: {
        "check_cap_no_colon": "Captions must contain a colon.",
        "check_cap_no_number": "Second word in a caption must be a number.",
        "check_cap_no_bold": "Captions should start with bolded text.",
        "check_cap_invalid_type": "Invalid caption type.",
        "check_cap_no_end_dot": "Captions must end with a trailing dot.",
        "check_cap_dupl_num": "A caption with repeated numbering was found.",
        # "check_cap_nonsequantial_num": "Caption numbering is not sequential.",
        # "check_cap_no_copyright": "No valid license information found.",
        # "check_cap_many_bookmarks": "A caption includes duplicated bookmarks.",
    },
    HEADINGS: {
        # "check_h_no_h1_at_start": "Every file should start with Heading of level 1.",
        "check_h_first_h_not_h1": "First Heading should be of level 1.",
        # "check_h_h1_after_start": "You should place Headings of level 1 only at the beginning of the file.",
        "check_h_not_sequential": "Heading levels should only increment by one level at a time.",
        "check_h_no_title_case": "All headings should be title cased.",
        "check_h_with_trailing_dot": "Headings should not end with a trailing dot.",
        "check_h_with_footnotes": "Headings must not contain any footnotes.",
        "check_h_if_gte_6": "Heading of level 6 and above are not supported.",
        "check_h_for_duplicates": "Duplicate headings found.",
    },
    PARAGRAPHS: {
        "check_p_bold_instead_heading": "Found bold line. Did you meant to use a heading?",
    },
    LINKS: {
        "check_a_is_http": "Links should point to websites using secure https over http.",
        "check_a_not_archived": "Links should point to websites archived using the Internet Archive.",
    },
}


if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}_verifier.log")
    log_target.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_target,
        encoding="utf-8",
        level=logging.DEBUG,
        format="%(asctime)s::%(name)s::%(levelname)s::%(message)s",
    )
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MsgLevel(enum.Enum):
    INFO = 20  # Confirmation that things are working as expected.
    NOTICE = 25  # An indication that input data should be examined.
    WARNING = (
        30  # An indication that input data may lead to problems and MUST be examined.
    )
    ERROR = 40  # Due to a more serious error in input data, the software won't be able to perform some function.
    CRITICAL = 50  # Input data contains a serious error, indicating that the book might not be created/updated.


class HtmlVerifier:
    """
    Verify HTML documents (chapters).
    I don't like how it was written, but I was in a hurry :/
    """

    # TODO:
    # * add label for hyperlinks
    # *

    def __init__(self) -> None:
        self.soup = None
        self._messages = VerifierMessages()
        self._links: list[bs4.Tag] = []
        self._captions: list[bs4.Tag] = []
        self._headings: list[bs4.Tag] = []
        self._headings_lvls: list[int] = []
        self._paragraphs: list[bs4.Tag] = []
        self._tables = []
        self._metadata_tables = []
        self._comments = {}
        # self._messages = VerifierMessages()
        # self._metadata = DocumentMetadata()
        self._docstate = DocumentState()
        self._logs = []

    def to_json(self, md: bool = False):
        return self._messages.to_json(md)

    def sort(self) -> None:
        def msg_key(msg: VerifMessage) -> tuple[int, int]:
            return (msg.line, msg.pos)

        self._messages.sort(key=msg_key)

    def verify(
        self, html: str, fp: pathlib.Path, slug: str, timestamp: datetime.datetime
    ) -> VerifierMessages:
        self._first_tag = None
        self._fp = fp
        self._slug = slug
        self._timestamp = timestamp
        self.soup = bs4.BeautifulSoup(html, "html.parser")
        self._mark_html_elements_recursively(self.soup)
        self._apply_captions_verification()
        self._apply_heading_verification()
        self._apply_paragraphs_verification()
        self._apply_links_verification()

    def _mark_html_elements_recursively(self, node: bs4.PageElement, lvl=0) -> None:
        """
        Before applying the verification, this function traverses the tree and
        puts relevant bs4.Tag elements inside respective lists
        or marks those elements as first html elements in the file.
        Verification is then applied on the marked elements.
        """
        if not isinstance(node, bs4.Tag):
            return
        for child in node.children:
            if isinstance(child, bs4.Tag):
                if self._first_tag is None:
                    self._first_tag = child
                if re.match(r"^h[0-9]*$", child.name):
                    self._headings.append(child)
                    self._headings_lvls.append(int(re.findall(r"\d+", child.name)[0]))
                elif child.name == "a":
                    self._links.append(child)
                # elif "dgt-mon-caption" in child.attrs.get("class", []):
                elif CLS_CAPTION in child.attrs.get("class", []):
                    self._captions.append(child)
                elif child.name == "table" and CLS_METADATA_TABLE in child.attrs.get(
                    "class", []
                ):
                    self._metadata_tables.append(child)
                elif child.name == "table":
                    self._tables.append(child)
                # elif (
                #     child.name == "script"
                #     and CLS_METADATA_TABLE_JSONDATA in child.attrs.get("class", [])
                # ):
                #     self._metadata.from_json(json.loads(child.text))
                elif (
                    child.name == "script"
                    and CLS_STATE_TABLE_JSONDATA in child.attrs.get("class", [])
                ):
                    self._docstate.from_dict(json.loads(child.text))
                    # TODO: read document state form script tag
                if child.name == "p":
                    self._paragraphs.append(child)
            self._mark_html_elements_recursively(child, lvl + 1)

    # captions ##########################################################################

    def _apply_captions_verification(self) -> None:
        self._caption_numbers = collections.defaultdict(list)
        for caption in self._captions:
            item = number = None
            caption_match = re.match(r"(^\w+) (\d+):\s*", caption.text)
            if caption_match is not None:
                item = caption_match.group(1)
                number = (
                    int(caption_match.group(2))
                    if caption_match.group(2).isdigit()
                    else None
                )
            if self._check_cap_no_colon(caption):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[CAPTIONS]["check_cap_no_colon"],
                    recommend=f'Add ":" character, e.g. "**Figure 1:** Text.".',
                    elem=caption,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[CAPTIONS],
                )
            if self._check_cap_no_number(caption):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[CAPTIONS]["check_cap_no_number"],
                    recommend=f'Add a number, so that your caption has a structure similar to this example: "**Figure 1:** Text.".',
                    elem=caption,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[CAPTIONS],
                )
            if self._check_cap_no_bold(caption, item, number):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[CAPTIONS]["check_cap_no_bold"],
                    recommend=f'For example, if your caption is "Figure 1: Text." bold the "**Figure 1:**" (including a colon).',
                    elem=caption,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[CAPTIONS],
                )
            if self._check_cap_invalid_type(item, caption):
                recommend = f', not "{item}"' if item else ""
                valid_types = (
                    ", ".join(f'"{ct}"' for ct in CAPTION_TYPES[:-1])
                    + f' or "{CAPTION_TYPES[-1]}"'
                )
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[CAPTIONS]["check_cap_invalid_type"],
                    recommend=f"Captions must start with {valid_types}{recommend}.",
                    elem=caption,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[CAPTIONS],
                )
            if self._check_cap_no_end_dot(caption):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[CAPTIONS]["check_cap_no_end_dot"],
                    recommend=f'Add a dot after "{caption.text}".',
                    elem=caption,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[CAPTIONS],
                )
            if self._check_cap_dupl_num(item, number):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[CAPTIONS]["check_cap_dupl_num"],
                    recommend=f'Check your captions for duplicated numbers. If you are using MS Word "Insert Caption" option (as you should), you can update all dynamic fields in a document by pressing Ctrl+A and then F9.',
                    elem=caption,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[CAPTIONS],
                )
            # if self._check_cap_nonsequantial_num(item, number):
            #     self._messages.add_msg(
            #         problem=MSG_PROBLEMS[CAPTIONS]["check_cap_nonsequantial_num"],
            #         recommend=f'Check if your caption numbering is in order. If you are using MS Word "Insert Caption" option (as you should), you can update all dynamic fields in a document by pressing Ctrl+A and then F9.',
            #         elem=caption,
            #         fn=self._fp.name,
            #         timestamp=self._timestamp,
            #         tags=[CAPTIONS],
            #     )
            # if self._check_cap_no_copyright(item, caption):
            #     self._messages.add_msg(
            #         problem=MSG_PROBLEMS[CAPTIONS]["check_cap_no_copyright"],
            #         recommend=f"It is very important to include a [SPDX Identifier](https://spdx.org/licenses/) in every caption associated with a figure. The identifier must be phrased in exactly the same characters as were used originally on the spdx.org website (e.g. hyphens instead of spaces).",
            #         elem=caption,
            #         fn=self._fp.name,
            #         timestamp=self._timestamp,
            #         tags=[METADATA_TABLES, TABLES, CAPTIONS],
            #     )
            # ref_nums = self._check_cap_many_bookmarks(caption)
            # if len(ref_nums) > 1:
            #     refs_to_del = ", ".join(f'"{_ref}"' for _ref in ref_nums[1:])
            #     self._messages.add_msg(
            #         problem=MSG_PROBLEMS[CAPTIONS]["check_cap_many_bookmarks"],
            #         recommend=f'You have to remove the duplicates: {refs_to_del}. To do that, open "{self._fp.name}" in MS Word, select "Insert" button in the top pane, click on "Bookmark" button, turn on "Hidden bookmarks", locate the bookmarks to remove and hit "Delete".',
            #         elem=caption,
            #         fn=self._fp.name,
            #         timestamp=self._timestamp,
            #         tags=[CAPTIONS],
            #     )
            if item is not None and number is not None:
                self._caption_numbers[item].append(number)

    def _check_cap_no_colon(self, tag: bs4.Tag) -> bool:
        return ":" not in tag.text

    def _check_cap_no_number(self, tag: bs4.Tag) -> bool:
        return re.match(r"^\w+ \d+", tag.text) is None

    def _check_cap_no_bold(
        self, tag: bs4.Tag, item: str | None, number: int | None
    ) -> bool:
        bolded = tag.find_next("strong")
        if isinstance(bolded, bs4.Tag):
            bolded_md = convert_to_md(bolded)
            self._logs.append(
                {
                    "tag": tag,
                    "strong": bolded,
                    "bolded.text": bolded.text,
                    "bolded.string": bolded.string,
                    "caption_md": bolded_md,
                    r'bolded_md.startswith(f"{item} {number}:")': bolded_md.startswith(
                        f"{item} {number}:"
                    ),
                    "isinstance(bolded, bs4.Tag)": isinstance(bolded, bs4.Tag),
                    "match": re.match(
                        r"^\w+ {{ (_Unref|_Ref)[0-9]{9} }}:", bolded.text
                    ),
                }
            )
            # print(self._logs[-1])
            # print("-" * 25)
            return False if bolded_md.strip().startswith(f"{item} {number}") else True
        return True

    def _check_cap_invalid_type(self, item: t.Optional[str], tag: bs4.Tag) -> bool:
        if item in CAPTION_TYPES:
            return False
        match = re.match(r"^\w+", tag.text)
        if match and match.group(0) in CAPTION_TYPES:
            return False
        return True

    def _check_cap_no_end_dot(self, tag: bs4.Tag) -> bool:
        return not tag.text.strip().endswith(".")

    def _check_cap_dupl_num(
        self, item: t.Optional[str], number: t.Optional[int]
    ) -> bool:
        if item is None or number is None:
            return False
        return number in self._caption_numbers[item]

    # NOTE: 2024-10-11: replaced with dynamic numbering
    # def _check_cap_nonsequantial_num(
    #     self, item: t.Optional[str], number: t.Optional[int]
    # ) -> bool:
    #     if item is None or number is None:
    #         return False
    #     if len(self._caption_numbers[item]) >= 1:
    #         return self._caption_numbers[item][-1] - 1 != number
    #     return False

    # NOTE: 2026-01-29: copyright check should be smarter, license not applicable
    # def _check_cap_no_copyright(self, item: t.Optional[str], tag: bs4.Tag) -> bool:
    #     if item is None:
    #         match = re.match(r"^\w+", tag.text)
    #         item = match.group(0) if match is not None else ""
    #     if item == "Figure":
    #         uuid = tag.get("dgt-mon-metadata-uuid", "")
    #         if uuid:
    #             # asset = self._metadata.get_asset(uuid)
    #             metadata_tbl: MetadataTableDatapoint = (
    #                 self._metadata.get_metadata_table(uuid)
    #             )
    #             licensename = metadata_tbl.kwargs.get("licensename", "").lower()
    #             if licensename in tag.text.lower():
    #                 return False
    #         return True
    #     return False

    # NOTE: 2026-01-29: there shouldn't be any duplicated bookmarks
    # def _check_cap_many_bookmarks(self, tag: bs4.Tag) -> list[str]:
    #     ref_nums = []
    #     # if "dgt-mon-caption" in tag.get("class", []):
    #     if CLS_CAPTION in tag.get("class", []):
    #         for child in tag.children:
    #             if (
    #                 isinstance(child, bs4.Tag)
    #                 and child.name == "a"
    #                 and child.get("id", "").startswith("_Ref")
    #             ):
    #                 ref_nums.append(child.get("id", ""))
    #             if len(ref_nums) > 1:
    #                 return ref_nums
    #     return ref_nums

    # headings ##########################################################################

    def _apply_heading_verification(self) -> None:
        self._unique_headings = []
        self._h_stack = []
        # if self._check_h_no_h1_at_start(self._first_tag):
        #     shrt_txt = (
        #         self._first_tag.text[:25]
        #         if len(self._first_tag.text) > 25
        #         else self._first_tag.text
        #     )
        #     self._messages.add_msg(
        #         problem=MSG_PROBLEMS[HEADINGS]["check_h_no_h1_at_start"],
        #         recommend=f'Here, it begins with "{shrt_txt}..." which does not have a Heading 1 style.',
        #         elem=self._first_tag,
        #         fn=self._fp.name,
        #         timestamp=self._timestamp,
        #         tags=[HEADINGS],
        #     )
        for i in range(len(self._headings)):
            tag = self._headings[i]
            while self._h_stack and self._h_stack[-1] > self._headings_lvls[i]:
                self._h_stack.pop()
            if self._h_stack and self._headings_lvls[i] - self._h_stack[-1] > 1:
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_not_sequential"],
                    recommend=f'Heading {str(self._headings_lvls[i])} ("{tag.text}") is placed after heading level {str(self._h_stack[-1])}. Consider changing the former to style "Heading {str(self._h_stack[-1] + 1)}".',
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            if len(self._h_stack) == 0 and self._headings_lvls[i] != 1:
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_first_h_not_h1"],
                    recommend=f'Consider changing the style of "{tag.text}" or "{self._first_tag.text}" to "Heading 1".',
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            # # NOTE: 2026-02-02 this doesn't apply to single docx to split into multiple chapters
            # # check_h_h1_after_start
            # if i > 1 and self._headings_lvls[i] == 1:
            #     self._messages.add_msg(
            #         problem=MSG_PROBLEMS[HEADINGS]["check_h_h1_after_start"],
            #         recommend=f'Consider changing level of "{tag.text}" or splitting file into two as there should be only one top level heading per file.',
            #         elem=tag,
            #         fn=self._fp.name,
            #         timestamp=self._timestamp,
            #         tags=[HEADINGS],
            #     )
            self._h_stack.append(self._headings_lvls[i])

            if self._check_h_no_title_case(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_no_title_case"],
                    recommend=f'Consider changing the heading "{tag.text}" to "{tag.text.title()}".',
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            if self._check_h_with_trailing_dot(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_with_trailing_dot"],
                    recommend=f'Consider removing the "." character at the end of the heading.',
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            if self._check_h_with_footnotes(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_with_footnotes"],
                    recommend=f'Please remove the footnote from the heading "{tag.text}".',
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS, FOOTNOTES],
                )
            if self._check_h_if_gte_6(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_if_gte_6"],
                    recommend=f'Consider changing the style of "{tag.text}" to Heading 5 or lower.',
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )
            if self._check_h_for_duplicates(tag):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[HEADINGS]["check_h_for_duplicates"],
                    recommend=f'There should be no two headings with the same text. Please rephrase "{tag.text}".',
                    elem=tag,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS],
                )

    # TODO: this should cover cases when frontmatter is before h1
    # def _check_h_no_h1_at_start(self, tag: bs4.element.Tag) -> bool:
    #     try:
    #         is_heading = re.match(r"^h[0-9]*$", tag.name)
    #         tag_nums = re.findall(r"\d+", tag.name)
    #         if is_heading and tag_nums and int(tag_nums[0]) == 1:
    #             return False
    #     except ValueError as e:
    #         return False
    #     else:
    #         return True

    def _check_h_no_title_case(self, tag: bs4.Tag) -> bool:
        return tag.text != tag.text.title() and IS_HEADING_TITLE_CASED_REQUIRED

    def _check_h_with_trailing_dot(self, tag: bs4.Tag) -> bool:
        return tag.text.strip().endswith(".")

    def _check_h_with_footnotes(self, tag: bs4.Tag) -> bool:
        """
        Check for an anchor tag in a superscript tag. E.g.:
        <h1>No Footnotes In Headings<sup><a href="#footnote-1" id="footnote-ref-1">[1]</a></sup></h1>
        """
        for sup in tag.find_all("sup"):
            sup: bs4.Tag
            for a in sup.find_all("a"):
                if "footnote" in str(a):
                    return True
        return False

    def _check_h_if_gte_6(self, tag: bs4.Tag) -> bool:
        nums = re.findall(r"\d+", tag.name)
        if nums and int(nums[0]) >= 6:
            return True
        return False

    def _check_h_for_duplicates(self, tag: bs4.Tag) -> bool:
        if tag.text in self._unique_headings:
            return True
        self._unique_headings.append(tag.text)
        return False

    # paragraphs #######################################################################

    def _apply_paragraphs_verification(self) -> None:
        for p in self._paragraphs:
            if self._check_p_bold_instead_heading(p):
                bold = p.text[:20] + "..." if len(p.text) > 20 else p.text
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[PARAGRAPHS]["check_p_bold_instead_heading"],
                    recommend=f'If so, please change the MS Word style for "{bold}" to appropriate "Heading" level.',
                    elem=p,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[HEADINGS, PARAGRAPHS],
                )

    def _check_p_bold_instead_heading(self, tag: bs4.Tag) -> bool:
        """
        In case when a <strong> tag is only part of the <p> element,
        the children will include also bs4.element.NavigableString,
        which name attribute is None.
        """
        children_names = {
            getattr(ch, "name") for ch in tag.children if hasattr(ch, "name")
        }
        if len(children_names) == 1 and "strong" in children_names:
            return True
        return False

    # links #############################################################################

    def _apply_links_verification(self) -> None:
        for link in self._links:
            href = link.get("href", "")
            if self._check_a_is_http(href):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[LINKS]["check_a_is_http"],
                    recommend=f"Issue with the link `[{link.text}]({href})` was found. If possible, change \"`{href}`\" to \"{href.replace('http:', 'https:', 1)}\".",
                    elem=link.parent,
                    fn=self._fp.name,
                    timestamp=self._timestamp,
                    tags=[LINKS],
                )
            if self._check_a_not_archived(href):
                self._messages.add_msg(
                    problem=MSG_PROBLEMS[LINKS]["check_a_not_archived"],
                    recommend=f'Consider archiving the link [{link.text}]({href}) with "https://wayback-api.archive.org/" and replacing "`{href}`" in your manuscript with the archived link.',
                    elem=link.parent,
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
