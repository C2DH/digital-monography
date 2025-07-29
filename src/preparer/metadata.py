# ===== IMPORTANT =====
# Remember, the only source of truth for metadata.py is the one defined in
# `src/_common/metadata.py`. A file with the same name in the src/ folder will be
# replaced with `src/_common/metadata.py` before building the image.
# We advise that you always build the containers using Makefile commands,
# as the copy command is already included.
# ======================
import abc
import bs4
import json
import dataclasses
import datetime
import enum
import functools
import logging
import pathlib
import pydantic
import string
import typing as t
import uuid

if t.TYPE_CHECKING:
    from _typeshed import DataclassInstance
else:
    DataclassInstance = None

try:
    from constants import MediumEnum, AUTONUMBER_PLACEHOLDER
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .constants import MediumEnum, AUTONUMBER_PLACEHOLDER  # type: ignore
    from .keys import KeyPath  # type: ignore


logger = logging.getLogger()
logger.setLevel(logging.INFO)
DATAPOINTS: list[str] = [
    # "AssetDatapoint",
    "HeadingDatapoint",
    "RefDatapoint",
    "TargetDatapoint",
    "SubstitutionDatapoint",
    "CitationGroupDatapoint",
    "CitationItemDatapoint",
    "FileDatapoint",
    "MetadataTableDatapoint",
]

# TODO: elem attributes should be left as bs4.element.PageElement,
# not immediatly stringified.

T = t.TypeVar("T", bound=DataclassInstance)
type PrimitiveValues = str | int | bool | None


# @dataclasses.dataclass
class DatapointBase(pydantic.BaseModel, abc.ABC):
    # pk: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()), kw_only=True)
    pk: str

    def __init__(self, **data) -> None:
        pk = data.pop("pk", str(uuid.uuid4()))
        super().__init__(pk=pk, **data)

    @property
    def s3_key(self) -> str:
        raise NotImplementedError

    # # TODO: rename, because it's not really json...
    def to_json(self) -> dict[str, PrimitiveValues]:
        # to_json() should be `return self.model_dump_json()`
        return self.model_dump()

    # # TODO: rename, because it's not really json...
    # def to_json(self) -> dict[str, PrimitiveValues]:
    #     "Converts the dataclass obj to a dict with primitive values."

    #     def _primitive_dict(fields) -> dict[str, PrimitiveValues]:
    #         res = {}
    #         for key, val in fields:
    #             if isinstance(val, datetime.datetime):
    #                 val = val.isoformat()
    #             elif isinstance(val, enum.Enum):
    #                 val = val.value
    #             elif key == "elem":
    #                 val = ""  # NOTE: for now, html is not included in the JSON
    #             elif val not in [str, int, None] and not isinstance(val, bool):
    #                 val = str(val)
    #             res[key] = val
    #         return res

    #     return dataclasses.asdict(self, dict_factory=_primitive_dict)

    # # TODO: rename, because it's not really json...
    @classmethod
    def from_json(
        cls: t.Type[T],
        json_data: dict[str, PrimitiveValues],
    ) -> T:
        "Constructs a dataclass instance from a JSON-like dictionary."
        # from_json() should be `return cls(**json.loads(data))`
        return cls(**json_data)

    @classmethod
    def unpack_records(
        cls: t.Type[T],
        json_data: list[dict[str, PrimitiveValues]],
    ) -> list[T]:
        result = []
        for rec in json_data:
            cls: DatapointBase
            try:
                result.append(cls.from_json(rec))
            except pydantic.ValidationError as e:
                logger.error(
                    f"{cls.__name__} could not be created from {rec}. Error: {e}."
                )
        return result

    # # # TODO: rename, because it's not really json...
    # @classmethod
    # def from_json(
    #     cls: t.Type[T],
    #     json_data: dict[str, PrimitiveValues],
    # ) -> T:
    #     "Constructs a dataclass instance from a JSON-like dictionary."
    #     if not dataclasses.is_dataclass(cls):
    #         raise ValueError(f"{cls.__name__} must be a dataclass")
    #     res = {}

    #     def _get_field_type(field: dataclasses.Field) -> t.Type:
    #         "If type is Union, Optional, Literal, etc. return their argument type."
    #         if getattr(field.type, "__args__", None) is not None:
    #             args: tuple = getattr(field.type, "__args__", tuple())
    #             typ = next(type(arg) for arg in args if arg not in (None,))
    #             assert isinstance(typ, type)
    #             return typ
    #         else:
    #             assert isinstance(field.type, type)
    #             return field.type

    #     for field in dataclasses.fields(cls):
    #         val = json_data[field.name]
    #         assert field.type != datetime.datetime  # for now unsupported
    #         if val is None or val == "None":
    #             v = None
    #         elif field.name == "elem":
    #             v = ""  # NOTE: for now, html is not included in the JSON
    #         elif field.type == bs4.element.Tag and isinstance(val, str):
    #             soup = bs4.BeautifulSoup(val, "html.parser")
    #             v = next(soup.children)  # type: ignore
    #             # v is a b4 page element, whatever it may be
    #         # elif field.type == datetime.datetime:
    #         #     v = datetime.datetime.fromisoformat(str(val))
    #         elif field.type == t.Optional[KeyPath]:
    #             v = KeyPath(val)
    #         else:
    #             v = (_get_field_type(field))(val)
    #         res[field.name] = v
    #     return cls(**res)


class MetadataTableDatapoint(DatapointBase):
    """
    Unprocessed data from a Metadata table that describes an asset.
    """

    schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
    ###
    kwargs: dict[str, t.Any]

    def to_json(self) -> dict[str, PrimitiveValues]:
        "Converts the dataclass obj to a dict with str/int/bool as values."
        return {"pk": self.pk, "kwargs": json.dumps(self.kwargs, default=str)}

    @classmethod
    def from_json(cls: t.Type[T], json_data: dict[str, PrimitiveValues]) -> T:
        return cls(
            **{
                "pk": json_data["pk"],
                "kwargs": json.loads(json.dumps(json_data["kwargs"])),
            }
        )
        # return cls(
        #     **{"pk": json_data["pk"], "kwargs": json.loads(str(json_data["kwargs"]))}
        # )


class AssetDatapoint(DatapointBase):
    """
    Information about an asset extracted from a document, especially from
    * Metadata Tables
    * captions
    * target id above caption

    When analysing assets, this model should be joined with
    * upload level (s3) information
    * book level information
    """

    schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
    ###
    fp: pathlib.Path
    metadata_table: str
    medium: MediumEnum
    slug: str
    author: str
    source: str
    location: KeyPath | None
    alttext: str
    caption: str
    orig_caption: str
    comments: str
    target: str
    is_color: bool | None
    is_ready: bool
    is_on_paper: bool
    # is_on_paper: bool = dataclasses.field(default=False)

    model_config = pydantic.ConfigDict(
        arbitrary_types_allowed=True, json_encoders={KeyPath: lambda v: str(v)}
    )

    # class Config:
    #     arbitrary_types_allowed = True
    #     json_encoders = {KeyPath: lambda v: str(v)}

    # @pydantic.field_validator("location", mode="before")
    # def deserialize_location(cls, v):
    #     if isinstance(v, str):
    #         return KeyPath(v)
    #     return v

    def __init__(self, **data) -> None:
        # if data.get("medium") is not None:
        data["is_on_paper"] = data["medium"] in (
            MediumEnum.PAPER,
            MediumEnum.PAPER_AND_DIGITAL,
        )
        super().__init__(**data)

    # def __post_init__(self):
    #     if self.medium:
    #         self.is_on_paper = self.medium in (
    #             MediumEnum.PAPER,
    #             MediumEnum.PAPER_AND_DIGITAL,
    #         )

    @pydantic.field_validator("location", mode="before")
    def deserialize_location(cls, v):
        if isinstance(v, str):
            return KeyPath(v)
        return v

    @staticmethod
    def get_s3_key(key: KeyPath) -> str:
        # TODO: implement
        # # AssetInfoFromUpload
        # return f"{key.slug}/{key.stem}.json"
        # # AssetInfoFromBook
        # return f"{key.slug}/_data_from_book.json"
        return f"{key.slug}/{key.stem}.json"


class HeadingDatapoint(DatapointBase):
    schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
    ###
    file_name: str
    elem: str
    level: str
    text: str
    word_count: int
    char_count: int
    target: str


class RefDatapoint(DatapointBase):
    schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
    ###
    fn: str
    target_id: str
    text: str
    href: str
    prev_string: str
    prev_href: str
    elem: str
    asset_id: str | None = None

    @staticmethod
    def get_s3_key(slug: str, stem: str) -> str:
        return f"{slug}/{stem}.json"

    def is_external(self) -> bool:
        """Is it a link to an external target
        (currently only email and http protocol is recognized)."""
        if self.href.startswith("mailto:") and "@" in self.href:
            return True
        return self.href.startswith("http") and ".sharepoint.com/" not in self.href

    def is_internal_infile(self) -> bool:
        "Is it a link to a target in the same document (file)?"
        return self.href.startswith("#")

    def is_internal_f2f(self) -> bool:
        "Is it a link to another document (file)?"
        if self.is_internal_infile() or self.is_external():
            return False
        return "#" in self.href


class IRefStack(t.TypedDict):
    html: str
    plain_text_num: str
    prefix: str
    prev_item_num: int | None
    item_type: str


class TargetDatapoint(DatapointBase):
    schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
    ###
    html: str
    text: str
    elem: str
    is_paper: bool | None
    is_digital: bool | None
    # no "ref"
    filename: str | None
    fragment: str | None
    item_type: t.Literal["heading", "equation", "figure", "table", "graph", ""]
    file_count: int | None
    prefix: str
    prev_item_num: int | None
    new_item_num: int | None = None

    def new_value(self) -> str:
        """
        Returns the value that will replace placeholder.
        Used for substituting values in wordprocessor (for paper version).
        """
        if self.new_item_num is not None:
            file_count = self.file_count if self.file_count is not None else ""
            return f"{file_count}.{self.prefix}{self.new_item_num}"
        else:
            return ""

    @staticmethod
    def parse_ref_stack(
        ref_stack: list[bs4.PageElement],
    ) -> IRefStack:
        res = {
            "html": "",
            "plain_text_num": "",
            "item_type": "",
            "prefix": "",
            "prev_item_num": None,
        }
        for elem in ref_stack:
            res["html"] += str(elem)
            res["plain_text_num"] += (
                elem.string if hasattr(elem, "string") else str(elem)
            )
            if isinstance(elem, bs4.element.NavigableString) or isinstance(elem, str):
                res["prefix"] += elem.strip()
            elif not isinstance(elem, bs4.element.Tag):
                pass
            elif "SEQ " in elem.get("value", "").upper():
                """
                SEQ denotes describes sequential numbers of chapters, tables, figures,
                and other user-defined lists of items in a document.
                See ECMA-376 17.16.5.56 for more details.

                Alternatively, I could parse the value to get other useful information,
                like item type. However, parsing OOXML syntax seems full of unnecessary
                edge cases.
                """
                text = elem.text.strip().upper()
                if _is_roman_numeral(text):
                    res["prev_item_num"] = _roman_to_int(text)
                elif text.isdigit():
                    res["prev_item_num"] = int(text)
                elif text.isalpha() and len(text) == 1:
                    res["prev_item_num"] = string.ascii_uppercase.index(text) + 1
                else:
                    raise NotImplementedError(
                        f"Alphabet sequential numbering is not implemented for "
                        "numbers bigger than 26. Text: {text}"
                    )

                for w in elem.get("value", "").split():
                    word = w.lower()
                    if word in ["equation", "figure", "table"]:
                        res["item_type"] = word
            elif "STYLEREF " in elem.get("value", ""):
                r"""
                STYLEREF inserts the nearest text that is formatted by the style
                whose name is specified by the argument. In most cases, it the search goes
                backwards. Commonly used with "\s" field argument, which includes a case
                or section number. E.g. ` STYLEREF 1 \s ` inserts the number of the previous
                Heading1 styled text.
                See ECMA-376 17.16.5.59 for more details.
                """
                res["prefix"] += elem.text
            else:
                res["prev_item_num"] = None
        return res


def _is_roman_numeral(text: str) -> bool:
    roman_num_chars = ["I", "V", "X", "L", "C", "D", "M"]
    if not text:
        return False
    for ch in text:
        if ch not in roman_num_chars:
            return False
    return True


def _roman_to_int(text: str) -> int:
    nums = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    res = 0
    for i in range(len(text)):
        if text[i] in nums:
            if i + 1 < len(text) and nums[text[i]] < nums[text[i + 1]]:
                res -= nums[text[i]]
            else:
                res += nums[text[i]]
    return res


class SubstitutionDatapoint(DatapointBase):
    schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
    ###
    was: str
    placeholder: str
    is_digital: bool | None
    is_paper: bool | None
    item_type: t.Literal["heading", "equation", "figure", "table", "graph", "ref", ""]
    location: pathlib.Path | None
    target_fn: str | None
    file_count: int | None
    prefix: str
    prev_item_num: int | None
    new_item_num: int | None = None
    fprefix: str | None = None
    # make sure that literal options are equal to constants.CAPTION_ITEM_TYPE_*

    def new_value(self, file_prefix=None) -> str:
        """
        Returns the value that will replace placeholder.
        Used for substituting values in builder (for digital version).
        """
        if self.is_digital is False and self.is_paper is True:
            return ""
        elif self.new_item_num and file_prefix:
            return f"{file_prefix}.{self.prefix}{self.new_item_num}"
        elif self.new_item_num is not None:
            file_count = self.file_count if self.file_count is not None else ""
            return f"{file_count}.{self.prefix}{self.new_item_num}"
        elif self.was == AUTONUMBER_PLACEHOLDER:
            return ""
        else:
            return self.was


class CitationGroupDatapoint(DatapointBase):
    schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
    ###
    # id: int
    file_name: str
    citation_schema: str
    # schema: str
    formattedCitation: str
    noteIndex: int
    plainCitation: str


class CitationItemDatapoint(DatapointBase):
    schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
    ###
    id: int
    file_name: str
    citationId: str
    uris: list[str]
    itemData: dict[str, t.Any]


class FileDatapoint(DatapointBase):
    schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
    ###
    pk: str
    stem: str
    prefix: str

    def __init__(self, **data) -> None:
        data["pk"] = data["stem"]
        super().__init__(**data)


type DatapointUnion = t.Union[
    AssetDatapoint,
    HeadingDatapoint,
    RefDatapoint,
    TargetDatapoint,
    SubstitutionDatapoint,
    CitationGroupDatapoint,
    CitationItemDatapoint,
    FileDatapoint,
    MetadataTableDatapoint,
]


class DocumentMetadataAsDict(t.TypedDict):
    assets: list[AssetDatapoint]
    metadata_tables: list[MetadataTableDatapoint]
    headings: list[HeadingDatapoint]
    refs: list[RefDatapoint]
    targets: list[TargetDatapoint]
    substitutions: list[SubstitutionDatapoint]
    citation_groups: list[CitationGroupDatapoint]
    citation_items: list[CitationItemDatapoint]
    files: list[FileDatapoint]


type DocumentMetadataSerialized = dict[str, list[dict[str, PrimitiveValues]]]


class DocumentMetadata:
    """
    Collection of records (lists of dictionaries) about:
        assets: data from the Metadata tables describing assets
        refs: references (links and cross-references)
        targets: reference targets (e.g. headings, captions)
        substitutions: used to replace text with other text
        citation_groups: groupings of one or more citation
        citation_items: citations of a single source
        files: files (main parts of the book) in the book
    """

    def __init__(self, fp: t.Optional[KeyPath] = None) -> None:
        self.filepath = fp
        self.slug = fp.slug if fp else ""
        self.word_count = 0
        self.char_count = 0
        self.assets: list[AssetDatapoint] = []
        self.metadata_tables: list[MetadataTableDatapoint] = []
        self.headings: list[HeadingDatapoint] = []
        self.refs: list[RefDatapoint] = []
        self.targets: list[TargetDatapoint] = []
        self.substitutions: list[SubstitutionDatapoint] = []
        self.citation_groups: list[CitationGroupDatapoint] = []
        self.citation_items: list[CitationItemDatapoint] = []
        # maybe this should be at the book level?
        self.files: list[FileDatapoint] = []

    def get_chapter_number(self, s: str | None = None) -> int | None:
        """Extract `int(1)` from file name '01_book_chapter'."""
        if s is None:
            if self.filepath is None:
                return None
            s = self.filepath.stem
        number = ""
        for ch in s:
            if number and not ch.isdigit():
                return int(number)
            elif ch.isdigit():
                number += ch
        try:
            return int(number)
        except ValueError:
            return None

    def add(
        self,
        records_name: str,
        record: DatapointUnion,
    ) -> None:
        records: list[DatapointUnion] = getattr(self, records_name)
        records.append(record)

    def get(
        self, records_name: str, val: str, attrib: str = "pk"
    ) -> t.Optional[DatapointUnion]:
        records = getattr(self, records_name)
        try:
            return next(rec for rec in records if getattr(rec, attrib) == val)
        except StopIteration:
            return None

    def filter(self, records_name: str, attrib: str, val: str) -> list[DatapointUnion]:
        records = getattr(self, records_name)
        return [rec for rec in records if getattr(rec, attrib) == val]

    add_asset = functools.partialmethod(add, "assets")
    get_asset = functools.partialmethod(get, "assets")

    get_metadata_table = functools.partialmethod(get, "metadata_tables")

    add_ref = functools.partialmethod(add, "refs")
    get_ref = functools.partialmethod(get, "refs")

    add_heading = functools.partialmethod(add, "headings")
    get_heading = functools.partialmethod(get, "headings")

    add_target = functools.partialmethod(add, "targets")
    get_target = functools.partialmethod(get, "targets")

    add_substitution = functools.partialmethod(add, "substitutions")
    get_substitution = functools.partialmethod(get, "substitutions")

    add_citation_group = functools.partialmethod(add, "citation_groups")
    get_citation_group = functools.partialmethod(get, "citation_groups")

    add_citation_item = functools.partialmethod(add, "citation_items")
    get_citation_item = functools.partialmethod(get, "citation_items")

    add_file = functools.partialmethod(add, "files")
    get_file = functools.partialmethod(get, "files")

    def to_dict(self) -> DocumentMetadataAsDict:
        return {
            "assets": self.assets,
            "metadata_tables": self.metadata_tables,
            "headings": self.headings,
            "refs": self.refs,
            "targets": self.targets,
            "substitutions": self.substitutions,
            "citation_groups": self.citation_groups,
            "citation_items": self.citation_items,
            "files": self.files,
        }

    # def to_json(self) -> dict[str, list[dict[str, PrimitiveValues]]]:
    # TODO: rename
    def to_json(self) -> DocumentMetadataSerialized:
        return {
            "assets": [rec.model_dump(mode="json") for rec in self.assets],
            "metadata_tables": [
                rec.model_dump(mode="json") for rec in self.metadata_tables
            ],
            "headings": [rec.model_dump(mode="json") for rec in self.headings],
            "refs": [rec.model_dump(mode="json") for rec in self.refs],
            "targets": [rec.model_dump(mode="json") for rec in self.targets],
            "substitutions": [
                rec.model_dump(mode="json") for rec in self.substitutions
            ],
            "citation_groups": [
                rec.model_dump(mode="json") for rec in self.citation_groups
            ],
            "citation_items": [
                rec.model_dump(mode="json") for rec in self.citation_items
            ],
            "files": [rec.model_dump(mode="json") for rec in self.files],
        }

    # def to_json(self) -> DocumentMetadataSerialized:
    #     return {
    #         "assets": [rec.to_json() for rec in self.assets],
    #         "metadata_tables": [rec.to_json() for rec in self.metadata_tables],
    #         "headings": [rec.to_json() for rec in self.headings],
    #         "refs": [rec.to_json() for rec in self.refs],
    #         "targets": [rec.to_json() for rec in self.targets],
    #         "substitutions": [rec.to_json() for rec in self.substitutions],
    #         "citation_groups": [rec.to_json() for rec in self.citation_groups],
    #         "citation_items": [rec.to_json() for rec in self.citation_items],
    #     }

    # def from_json(self, jsml: dict[str, list[dict[str, PrimitiveValues]]]) -> None:
    def from_json(self, jsml: DocumentMetadataSerialized) -> None:
        self.assets = AssetDatapoint.unpack_records(jsml.get("assets", []))
        self.metadata_tables = MetadataTableDatapoint.unpack_records(
            jsml.get("metadata_tables", [])
        )
        self.headings = HeadingDatapoint.unpack_records(jsml.get("headings", []))
        self.refs = RefDatapoint.unpack_records(jsml.get("refs", []))
        self.targets = TargetDatapoint.unpack_records(jsml.get("targets", []))
        self.substitutions = SubstitutionDatapoint.unpack_records(
            jsml.get("substitutions", [])
        )
        self.citation_groups = CitationGroupDatapoint.unpack_records(
            jsml.get("citation_groups", [])
        )
        self.citation_items = CitationItemDatapoint.unpack_records(
            jsml.get("citation_items", [])
        )
        self.files = FileDatapoint.unpack_records(jsml.get("files", []))
        # self.assets = [AssetDatapoint.from_json(rec) for rec in jsml.get("assets", [])]
        # self.metadata_tables = [
        #     MetadataTableDatapoint.from_json(rec)
        #     for rec in jsml.get("metadata_tables", [])
        # ]
        # self.headings = [
        #     HeadingDatapoint.from_json(rec) for rec in jsml.get("headings", [])
        # ]
        # self.refs = [RefDatapoint.from_json(rec) for rec in jsml.get("refs", [])]
        # self.targets = [
        #     TargetDatapoint.from_json(rec) for rec in jsml.get("targets", [])
        # ]
        # self.substitutions = [
        #     SubstitutionDatapoint.from_json(rec)
        #     for rec in jsml.get("substitutions", [])
        # ]
        # self.citation_groups = [
        #     CitationGroupDatapoint.from_json(rec)
        #     for rec in jsml.get("citation_groups", [])
        # ]
        # self.citation_items = [
        #     CitationItemDatapoint.from_json(rec)
        #     for rec in jsml.get("citation_items", [])
        # ]
        # self.files = [FileDatapoint.from_json(rec) for rec in jsml.get("files", [])]

    def __str__(self) -> str:
        return (
            "%s(assets=[%s], metadata_tables=[%s], headings=[%s], refs=[%s], targets=[%s], substitutions=[%s], citation_groups=[%s], citation_items=[%s], files=[%s])"
            % (
                self.__class__.__name__,
                ", ".join(str(rec) for rec in self.assets),
                ", ".join(str(rec) for rec in self.metadata_tables),
                ", ".join(str(rec) for rec in self.headings),
                ", ".join(str(rec) for rec in self.refs),
                ", ".join(str(rec) for rec in self.targets),
                ", ".join(str(rec) for rec in self.substitutions),
                ", ".join(str(rec) for rec in self.citation_groups),
                ", ".join(str(rec) for rec in self.citation_items),
                ", ".join(str(rec) for rec in self.files),
            )
        )
