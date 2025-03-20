# ===== IMPORTANT =====
# Remember, the only source of truth for metadata.py is the one defined in
# `src/_common/metadata.py`. A file with the same name in the src/ folder will be
# replaced with `src/_common/metadata.py` before building the image.
# We advise that you always build the containers using Makefile commands,
# as the copy command is already included.
# ======================
import abc
import json
import bs4
import dataclasses
import datetime
import enum
import functools
import pathlib
import typing as t
import uuid
from _typeshed import DataclassInstance


try:
    from keys import KeyPath
    from constants import MediumEnum
except (ImportError, ModuleNotFoundError):
    from .keys import KeyPath  # type: ignore
    from .constants import MediumEnum  # type: ignore


# class FieldTypeRecord(t.TypedDict):
#     """Structure of fields definition in METADATA_FIELDS."""

#     key: str
#     is_bool: bool
#     is_required: bool
#     aliases: list[str]
#     desc: str


# class AssetRecord(t.TypedDict):
#     pk: str
#     kwargs: dict[str, AcceptedValues]


# class HeadingRecord(t.TypedDict):
#     pk: str
#     file: str
#     # elem: str
#     level: str
#     text: str
#     target: str


# class RefRecord(t.TypedDict):
#     pk: str
#     target_id: int
#     text: str
#     href: str
#     prev_string: str
#     prev_href: str


# class TargetRecord(t.TypedDict):
#     pk: str
#     html: str
#     text: str


# class SubstitutionRecord(t.TypedDict):
#     pk: str
#     src: str


# class CitationGroupRecord(t.TypedDict):
#     pk: str
#     schema: str
#     formattedCitation: str
#     noteIndex: int
#     plainCitation: str


# class CitationItemRecord(t.TypedDict):
#     pk: str
#     citationId: str
#     uris: list[str]
#     itemData: dict[str, t.Any]


# TODO: elem attributes should be left as bs4.element.PageElement,
# not immediatly stringified.

T = t.TypeVar("T", bound=DataclassInstance)
type PrimitiveValues = str | int | bool | None


@dataclasses.dataclass
class DatapointBase(abc.ABC):
    pk: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()), kw_only=True)

    @property
    def s3_key(self) -> str:
        raise NotImplementedError

    # TODO: rename, because it's not really json...
    # def to_json(self) -> dict[str, str | int | bool | None]:
    def to_json(self) -> dict[str, PrimitiveValues]:
        "Converts the dataclass obj to a dict with primitive values."

        # def _primitive_dict(fields) -> dict[str, str | int | bool | None]:
        def _primitive_dict(fields) -> dict[str, PrimitiveValues]:
            res = {}
            for key, val in fields:
                if isinstance(val, datetime.datetime):
                    val = val.isoformat()
                elif isinstance(val, enum.Enum):
                    val = val.value
                elif key == "elem":
                    val = ""  # NOTE: for now, html is not included in the JSON
                elif val not in [str, int, None] and not isinstance(val, bool):
                    val = str(val)
                res[key] = val
            return res

        return dataclasses.asdict(self, dict_factory=_primitive_dict)

    @classmethod
    def from_json(
        cls: t.Type[T],
        json_data: dict[str, PrimitiveValues],
    ) -> T:
        "Constructs a dataclass instance from a JSON-like dictionary."
        if not dataclasses.is_dataclass(cls):
            raise ValueError(f"{cls.__name__} must be a dataclass")
        res = {}

        def _get_field_type(field: dataclasses.Field) -> t.Type:
            "If type is Union, Optional, Literal, etc. return their argument type."
            if getattr(field.type, "__args__", None) is not None:
                args: tuple = getattr(field.type, "__args__", tuple())
                typ = next(type(arg) for arg in args if arg not in (None,))
                assert isinstance(typ, type)
                return typ
            else:
                assert isinstance(field.type, type)
                return field.type

        for field in dataclasses.fields(cls):
            val = json_data[field.name]
            assert field.type != datetime.datetime  # for now unsupported
            if val is None or val == "None":
                v = None
            elif field.name == "elem":
                v = ""  # NOTE: for now, html is not included in the JSON
            elif field.type == bs4.element.Tag and isinstance(val, str):
                soup = bs4.BeautifulSoup(val, "html.parser")
                v = next(soup.children)  # type: ignore
                # v is a b4 page element, whatever it may be
            # elif field.type == datetime.datetime:
            #     v = datetime.datetime.fromisoformat(str(val))
            elif field.type == t.Optional[KeyPath]:
                v = KeyPath(val)
            else:
                v = (_get_field_type(field))(val)
            res[field.name] = v
        dataclass_instance = cls(**res)
        # assert isinstance(dataclass_instance, DataclassInstance)
        return dataclass_instance


@dataclasses.dataclass
class MetadataTableDatapoint(DatapointBase):
    """
    Unprocessed data from a Metadata table that describes an asset.
    """

    kwargs: dict[str, str]

    # def to_json(self) -> dict[str, str | int | bool | None]:
    def to_json(self) -> dict[str, PrimitiveValues]:
        "Converts the dataclass obj to a dict with str/int/bool as values."
        return {"pk": self.pk, "kwargs": json.dumps(self.kwargs, default=str)}

    # def from_json(cls: t.Type[T], json_data: dict[str, str | int | bool | None]) -> T:
    @classmethod
    def from_json(cls: t.Type[T], json_data: dict[str, PrimitiveValues]) -> T:
        return cls(
            **{"pk": json_data["pk"], "kwargs": json.loads(str(json_data["kwargs"]))}
        )


@dataclasses.dataclass
# class AssetInfoFromDoc(DatapointBase):
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

    # pk: str
    fp: pathlib.Path
    metadata_table: str
    medium: MediumEnum
    slug: str
    author: str
    source: str
    location: KeyPath | None
    alttext: str
    caption: str
    comments: str
    target: str
    is_color: bool | None
    is_ready: bool
    is_on_paper: bool = dataclasses.field(default=False)

    def __post_init__(self):
        if self.medium:
            self.is_on_paper = self.medium in (
                MediumEnum.PAPER,
                MediumEnum.PAPER_AND_DIGITAL,
            )

    @staticmethod
    def get_s3_key(key: KeyPath) -> str:
        # TODO: implement
        # # AssetInfoFromUpload
        # return f"{key.slug}/{key.stem}.json"
        # # AssetInfoFromBook
        # return f"{key.slug}/_data_from_book.json"
        return f"{key.slug}/{key.stem}.json"


@dataclasses.dataclass
class HeadingDatapoint(DatapointBase):
    # pk: int = dataclasses.field(default_factory=itertools.count().__next__, init=False)
    file_name: str
    elem: str
    level: str
    text: str
    word_count: int
    char_count: int
    target: str

    # def to_json(self) -> dict[str, t.Union[str, int]]:
    #     omit = ("elem",)
    #     return {
    #         f.name: getattr(self, f.name)
    #         for f in dataclasses.fields(self)
    #         if f.name not in omit
    #     }

    # @staticmethod
    # def from_json(jsml: dict[str, t.Union[str, int]]) -> "HeadingDatapoint":
    #     del jsml["pk"]
    #     jsml["elem"] = ""
    #     return HeadingDatapoint(**jsml)

    # def __getitem__(self, name: str) -> t.Union[int, str]:
    #     return getattr(self, name)


@dataclasses.dataclass
class RefDatapoint(DatapointBase):
    # pk: int = dataclasses.field(default_factory=itertools.count().__next__, init=False)
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

    # def to_json(self) -> dict[str, t.Union[str, int]]:
    #     omit = []  # ("elem",)
    #     return {
    #         f.name: getattr(self, f.name)
    #         for f in dataclasses.fields(self)
    #         if f.name not in omit
    #     }

    # @staticmethod
    # def from_json(jsml: dict[str, t.Union[str, int]]) -> "RefDatapoint":
    #     del jsml["pk"]
    #     # jsml["elem"] = ""
    #     return RefDatapoint(**jsml)

    # def __getitem__(self, name: str) -> t.Union[int, str]:
    #     return getattr(self, name)


@dataclasses.dataclass
class TargetDatapoint(DatapointBase):
    # pk: str
    html: str
    text: str
    elem: str

    # def to_json(self) -> dict[str, t.Union[str, int]]:
    #     omit = ("elem",)
    #     return {
    #         f.name: getattr(self, f.name)
    #         for f in dataclasses.fields(self)
    #         if f.name not in omit
    #     }

    # @staticmethod
    # def from_json(jsml: dict[str, t.Union[str, int]]) -> "TargetDatapoint":
    #     jsml["elem"] = ""
    #     return TargetDatapoint(**jsml)

    # def __getitem__(self, name: str) -> t.Union[int, str]:
    #     return getattr(self, name)


@dataclasses.dataclass
class SubstitutionDatapoint(DatapointBase):
    # pk: str
    was: str
    placeholder: str
    # make sure that literal options are equal to constants.CAPTION_ITEM_TYPE_*
    item_type: t.Literal["fig", "tbl", "graph", "nul"]
    # TODO: for now item_type doesn't do anything, but it can be crucial e.g. for
    # adding counting numbers of figures and tables upon substitution

    # def to_json(self) -> dict[str, t.Union[str, int]]:
    #     return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}

    # @staticmethod
    # def from_json(jsml: dict[str, t.Union[str, int]]) -> "SubstitutionDatapoint":
    #     return SubstitutionDatapoint(**jsml)

    # def __getitem__(self, name: str) -> t.Union[int, str]:
    #     return getattr(self, name)


@dataclasses.dataclass
class CitationGroupDatapoint(DatapointBase):
    # pk: str
    file_name: str
    schema: str
    formattedCitation: str
    noteIndex: int
    plainCitation: str

    # def to_json(self) -> dict[str, t.Union[str, int]]:
    #     return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}

    # @staticmethod
    # def from_json(jsml: dict[str, t.Union[str, int]]) -> "CitationGroupDatapoint":
    #     return CitationGroupDatapoint(**jsml)

    # def __getitem__(self, name: str) -> t.Union[int, str]:
    #     return getattr(self, name)


@dataclasses.dataclass
class CitationItemDatapoint(DatapointBase):
    # pk: t.Union[int, str]
    file_name: str
    citationId: str
    uris: list[str]
    itemData: dict[str, t.Any]

    # def to_json(self) -> dict[str, t.Union[str, int]]:
    #     return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}

    # @staticmethod
    # def from_json(jsml: dict[str, t.Union[str, int]]) -> "CitationItemDatapoint":
    #     return CitationItemDatapoint(**jsml)

    # def __getitem__(self, name: str) -> t.Union[int, str]:
    #     return getattr(self, name)


type DatapointUnion = t.Union[
    AssetDatapoint,
    HeadingDatapoint,
    RefDatapoint,
    TargetDatapoint,
    SubstitutionDatapoint,
    CitationGroupDatapoint,
    CitationItemDatapoint,
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
            # return next(rec for rec in records if rec[attrib] == val)
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
        }

    # def to_json(self) -> dict[str, list[dict[str, PrimitiveValues]]]:
    def to_json(self) -> DocumentMetadataSerialized:
        return {
            "assets": [rec.to_json() for rec in self.assets],
            "metadata_tables": [rec.to_json() for rec in self.metadata_tables],
            "headings": [rec.to_json() for rec in self.headings],
            "refs": [rec.to_json() for rec in self.refs],
            "targets": [rec.to_json() for rec in self.targets],
            "substitutions": [rec.to_json() for rec in self.substitutions],
            "citation_groups": [rec.to_json() for rec in self.citation_groups],
            "citation_items": [rec.to_json() for rec in self.citation_items],
        }

    # def from_json(self, jsml: dict[str, list[dict[str, PrimitiveValues]]]) -> None:
    def from_json(self, jsml: DocumentMetadataSerialized) -> None:
        self.assets = [AssetDatapoint.from_json(rec) for rec in jsml.get("assets", [])]
        self.metadata_tables = [
            MetadataTableDatapoint.from_json(rec)
            for rec in jsml.get("metadata_tables", [])
        ]
        self.headings = [
            HeadingDatapoint.from_json(rec) for rec in jsml.get("headings", [])
        ]
        self.refs = [RefDatapoint.from_json(rec) for rec in jsml.get("refs", [])]
        self.targets = [
            TargetDatapoint.from_json(rec) for rec in jsml.get("targets", [])
        ]
        self.substitutions = [
            SubstitutionDatapoint.from_json(rec)
            for rec in jsml.get("substitutions", [])
        ]
        self.citation_groups = [
            CitationGroupDatapoint.from_json(rec)
            for rec in jsml.get("citation_groups", [])
        ]
        self.citation_items = [
            CitationItemDatapoint.from_json(rec)
            for rec in jsml.get("citation_items", [])
        ]

    def __str__(self) -> str:
        return (
            "%s(assets=[%s], metadata_tables=[%s], headings=[%s], refs=[%s], targets=[%s], substitutions=[%s], citation_groups=[%s], citation_items=[%s])"
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
            )
        )
