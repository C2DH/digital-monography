import collections
import bs4
import datetime
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
        self._links = []
        self._captions: list[bs4.Tag] = []
        self._headings = []
        self._headings_lvls = []
        self._paragraphs = []
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
