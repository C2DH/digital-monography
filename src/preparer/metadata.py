# ===== IMPORTANT =====
# Remember, the only source of truth for metadata.py is the one defined in
# `src/_common/metadata.py`. A file with the same name in the src/ folder will be
# replaced with `src/_common/metadata.py` before building the image.
# We advise that you always build the containers using Makefile commands,
# as the copy command is already included.
# ======================
import dataclasses
import functools
import itertools
import pathlib
import typing as t

# import bs4

try:
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .keys import KeyPath

T = t.TypeVar("T")
type AcceptedValues = t.Union[str, bool, pathlib.Path]
type DatapointUnion = t.Union[
    AssetDatapoint,
    HeadingDatapoint,
    RefDatapoint,
    TargetDatapoint,
    SubstitutionDatapoint,
    CitationGroupDatapoint,
    CitationItemDatapoint,
]
type RecordsUnion = t.Union[
    AssetRecord,
    HeadingRecord,
    RefRecord,
    TargetRecord,
    SubstitutionRecord,
    CitationGroupRecord,
    CitationItemRecord,
]


class FieldTypeRecord(t.TypedDict):
    """Structure of fields definition in METADATA_FIELDS."""

    key: str
    is_bool: bool
    is_required: bool
    aliases: list[str]
    desc: str


class AssetRecord(t.TypedDict):
    pk: str
    kwargs: dict[str, AcceptedValues]


class HeadingRecord(t.TypedDict):
    pk: int
    file: str
    # elem: str
    level: str
    text: str
    target: str


class RefRecord(t.TypedDict):
    pk: int
    target_id: int
    text: str
    href: str
    prev_string: str
    prev_href: str


class TargetRecord(t.TypedDict):
    pk: int
    html: str
    text: str


class SubstitutionRecord(t.TypedDict):
    pk: str
    src: str


class CitationGroupRecord(t.TypedDict):
    pk: str
    schema: str
    formattedCitation: str
    noteIndex: int
    plainCitation: str


class CitationItemRecord(t.TypedDict):
    pk: t.Union[int, str]
    citationId: str
    uris: list[str]
    itemData: dict[str, t.Any]


# TODO: elem attributes should be left as bs4.element.PageElement,
# not immediatly stringified.


@dataclasses.dataclass
class AssetDatapoint:
    pk: str
    kwargs: dict[str, AcceptedValues] = dataclasses.field(default_factory=dict)

    def to_json(self) -> dict[str, str]:
        res = {}
        for k, v in self.kwargs.items():
            if isinstance(v, pathlib.Path):
                v = str(v)
            if k != "elem":
                res.update({k: v})
        res.update({"pk": self.pk})
        return res

    @staticmethod
    def from_json(jsml: dict[str, str]) -> "AssetDatapoint":
        pk = jsml["pk"]
        del jsml["pk"]
        jsml["elem"] = ""
        return AssetDatapoint(pk=pk, kwargs=jsml)

    def __getitem__(self, name: str) -> t.Union[AcceptedValues]:
        return getattr(self, name)


@dataclasses.dataclass
class HeadingDatapoint:
    pk: int = dataclasses.field(default_factory=itertools.count().__next__, init=False)
    file_name: str
    elem: str
    level: str
    text: str
    word_count: int
    char_count: int
    target: str

    def to_json(self) -> dict[str, t.Union[str, int]]:
        omit = ("elem",)
        return {
            f.name: getattr(self, f.name)
            for f in dataclasses.fields(self)
            if f.name not in omit
        }

    @staticmethod
    def from_json(jsml: dict[str, t.Union[str, int]]) -> "HeadingDatapoint":
        del jsml["pk"]
        jsml["elem"] = ""
        return HeadingDatapoint(**jsml)

    def __getitem__(self, name: str) -> t.Union[int, str]:
        return getattr(self, name)


@dataclasses.dataclass
class RefDatapoint:
    pk: int = dataclasses.field(default_factory=itertools.count().__next__, init=False)
    fn: str
    target_id: str
    text: str
    href: str
    prev_string: str
    prev_href: str
    elem: str

    def to_json(self) -> dict[str, t.Union[str, int]]:
        omit = ("elem",)
        return {
            f.name: getattr(self, f.name)
            for f in dataclasses.fields(self)
            if f.name not in omit
        }

    @staticmethod
    def from_json(jsml: dict[str, t.Union[str, int]]) -> "RefDatapoint":
        del jsml["pk"]
        jsml["elem"] = ""
        return RefDatapoint(**jsml)

    def __getitem__(self, name: str) -> t.Union[int, str]:
        return getattr(self, name)


@dataclasses.dataclass
class TargetDatapoint:
    pk: str
    html: str
    text: str
    elem: str

    def to_json(self) -> dict[str, t.Union[str, int]]:
        omit = ("elem",)
        return {
            f.name: getattr(self, f.name)
            for f in dataclasses.fields(self)
            if f.name not in omit
        }

    @staticmethod
    def from_json(jsml: dict[str, t.Union[str, int]]) -> "TargetDatapoint":
        jsml["elem"] = ""
        return TargetDatapoint(**jsml)

    def __getitem__(self, name: str) -> t.Union[int, str]:
        return getattr(self, name)


@dataclasses.dataclass
class SubstitutionDatapoint:
    pk: str
    was: str
    placeholder: str
    # make sure that literal options are equal to constants.CAPTION_ITEM_TYPE_*
    item_type: t.Literal["fig", "tbl", "graph", "nul"]
    # TODO: for now item_type doesn't do anything, but it can be crucial e.g. for
    # adding counting numbers of figures and tables upon substitution

    def to_json(self) -> dict[str, t.Union[str, int]]:
        return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}

    @staticmethod
    def from_json(jsml: dict[str, t.Union[str, int]]) -> "SubstitutionDatapoint":
        return SubstitutionDatapoint(**jsml)

    def __getitem__(self, name: str) -> t.Union[int, str]:
        return getattr(self, name)


@dataclasses.dataclass
class CitationGroupDatapoint:
    pk: str
    file_name: str
    schema: str
    formattedCitation: str
    noteIndex: int
    plainCitation: str

    def to_json(self) -> dict[str, t.Union[str, int]]:
        return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}

    @staticmethod
    def from_json(jsml: dict[str, t.Union[str, int]]) -> "CitationGroupDatapoint":
        return CitationGroupDatapoint(**jsml)

    def __getitem__(self, name: str) -> t.Union[int, str]:
        return getattr(self, name)


@dataclasses.dataclass
class CitationItemDatapoint:
    pk: t.Union[int, str]
    file_name: str
    citationId: str
    uris: list[str]
    itemData: dict[str, t.Any]

    def to_json(self) -> dict[str, t.Union[str, int]]:
        return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}

    @staticmethod
    def from_json(jsml: dict[str, t.Union[str, int]]) -> "CitationItemDatapoint":
        return CitationItemDatapoint(**jsml)

    def __getitem__(self, name: str) -> t.Union[int, str]:
        return getattr(self, name)


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
        self.word_count = 0
        self.char_count = 0
        self.assets: list[AssetDatapoint] = []
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
        records = getattr(self, records_name)
        records.append(record)

    def get(
        self, records_name: str, val: str, attrib: str = "pk"
    ) -> t.Optional[DatapointUnion]:
        records = getattr(self, records_name)
        try:
            return next(rec for rec in records if rec[attrib] == val)
        except StopIteration:
            return None

    def filter(self, records_name: str, attrib: str, val: str) -> list[DatapointUnion]:
        records = getattr(self, records_name)
        return [rec for rec in records if getattr(rec, attrib) == val]

    add_asset = functools.partialmethod(add, "assets")
    get_asset = functools.partialmethod(get, "assets")

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

    def to_dict(self) -> dict[str, list[dict[str, AcceptedValues]]]:
        return {
            "assets": self.assets,
            "headings": self.headings,
            "refs": self.refs,
            "targets": self.targets,
            "substitutions": self.substitutions,
            "citation_groups": self.citation_groups,
            "citation_items": self.citation_items,
        }

    def to_json(self) -> dict[str, list[dict[str, t.Union[str, t.Union[str, int]]]]]:
        return {
            "assets": [rec.to_json() for rec in self.assets],
            "headings": [rec.to_json() for rec in self.headings],
            "refs": [rec.to_json() for rec in self.refs],
            "targets": [rec.to_json() for rec in self.targets],
            "substitutions": [rec.to_json() for rec in self.substitutions],
            "citation_groups": [rec.to_json() for rec in self.citation_groups],
            "citation_items": [rec.to_json() for rec in self.citation_items],
        }

    def from_json(self, jsml: dict[str, RecordsUnion]) -> None:
        self.assets = [AssetDatapoint.from_json(rec) for rec in jsml.get("assets", [])]
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
            "%s(assets=[%s], headings=[%s], refs=[%s], targets=[%s], substitutions=[%s], citation_groups=[%s], citation_items=[%s])"
            % (
                self.__class__.__name__,
                ", ".join(str(rec) for rec in self.assets),
                ", ".join(str(rec) for rec in self.headings),
                ", ".join(str(rec) for rec in self.refs),
                ", ".join(str(rec) for rec in self.targets),
                ", ".join(str(rec) for rec in self.substitutions),
                ", ".join(str(rec) for rec in self.citation_groups),
                ", ".join(str(rec) for rec in self.citation_items),
            )
        )
