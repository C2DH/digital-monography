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

type AcceptedValues = t.Union[str, bool, pathlib.Path]
T = t.TypeVar("T")


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


class RefRecord(t.TypedDict):
    pk: int
    target_id: int
    target_full_id: str
    text: str
    href: str
    prev_string: str
    prev_href: str


class TargetRecord(t.TypedDict):
    pk: int
    full_id: str
    html: str
    text: str


@dataclasses.dataclass
class AssetDatapoint:
    pk: str
    kwargs: dict[str, AcceptedValues] = dataclasses.field(default_factory=dict)

    def to_json(self) -> dict[str, str]:
        res = {}
        for k, v in self.kwargs.items():
            if isinstance(v, pathlib.Path):
                v = str(v)
            res.update({k: v})
        res.update({"pk": self.pk})
        return res

    @staticmethod
    def from_json(jsml: dict[str, str]) -> "AssetDatapoint":
        pk = jsml["pk"]
        del jsml["pk"]
        return AssetDatapoint(pk=pk, kwargs=jsml)

    def __getitem__(self, name: str) -> t.Union[AcceptedValues]:
        return getattr(self, name)


@dataclasses.dataclass
class RefDatapoint:
    pk: int = dataclasses.field(default_factory=itertools.count().__next__, init=False)
    target_id: int
    target_full_id: str
    text: str
    href: str
    prev_string: str
    prev_href: str

    def to_json(self) -> dict[str, t.Union[str, int]]:
        return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}

    @staticmethod
    def from_json(jsml: dict[str, t.Union[str, int]]) -> "RefDatapoint":
        return RefDatapoint(**jsml)

    def __getitem__(self, name: str) -> t.Union[int, str]:
        return getattr(self, name)


@dataclasses.dataclass
class TargetDatapoint:
    pk: int = dataclasses.field(init=False)
    full_id: str
    html: str
    text: str

    def __post_init__(self):
        "Get 241403112 from _Unref241403112."
        self.pk = int("".join(ch for ch in self.full_id if ch.isdigit()))

    def to_json(self) -> dict[str, t.Union[str, int]]:
        return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}

    @staticmethod
    def from_json(jsml: dict[str, t.Union[str, int]]) -> "TargetDatapoint":
        return TargetDatapoint(**jsml)

    def __getitem__(self, name: str) -> t.Union[int, str]:
        return getattr(self, name)


class DocumentMetadata:
    """
    Collection of records (lists of dictionaries) about:
        assets: data from the Metadata tables describing assets
        refs: references (links and cross-references)
        targets: reference targets (e.g. headings, captions)
    """

    def __init__(self) -> None:
        self.assets: list[AssetDatapoint] = []
        self.refs: list[RefDatapoint] = []
        self.targets: list[TargetDatapoint] = []

    def add(
        self,
        records_name: str,
        record: t.Union[AssetDatapoint, RefDatapoint, TargetDatapoint],
    ) -> None:
        records = getattr(self, records_name)
        records.append(record)

    def get(
        self, records_name: str, val: str, attrib: str = "pk"
    ) -> t.Optional[t.Union[AssetDatapoint, RefDatapoint, TargetDatapoint]]:
        records = getattr(self, records_name)
        try:
            return next(rec for rec in records if rec[attrib] == val)
        except StopIteration:
            return None

    def filter(
        self, records_name: str, attrib: str, val: str
    ) -> list[t.Union[AssetDatapoint, RefDatapoint, TargetDatapoint]]:
        records = getattr(self, records_name)
        return [rec for rec in records if getattr(rec, attrib) == val]

    add_asset = functools.partialmethod(add, "assets")
    get_asset = functools.partialmethod(get, "assets")

    add_ref = functools.partialmethod(add, "refs")
    get_ref = functools.partialmethod(get, "refs")

    add_target = functools.partialmethod(add, "targets")
    get_target = functools.partialmethod(get, "targets")

    def to_dict(self) -> dict[str, list[dict[str, AcceptedValues]]]:
        return {
            "assets": self.assets,
            "refs": self.refs,
            "targets": self.targets,
        }

    def to_json(self) -> dict[str, list[dict[str, t.Union[str, t.Union[str, int]]]]]:
        return {
            "assets": [rec.to_json() for rec in self.assets],
            "refs": [rec.to_json() for rec in self.refs],
            "targets": [rec.to_json() for rec in self.targets],
        }

    def from_json(
        self, jsml: dict[str, t.Union[AssetRecord, RefRecord, TargetRecord]]
    ) -> None:
        self.assets = [AssetDatapoint.from_json(rec) for rec in jsml["assets"]]
        self.refs = [RefDatapoint.from_json(rec) for rec in jsml["refs"]]
        self.targets = [TargetDatapoint.from_json(rec) for rec in jsml["targets"]]

    def __str__(self) -> str:
        return "%s(assets=[%s], refs=[%s], targets=[%s])" % (
            self.__class__.__name__,
            ", ".join(str(rec) for rec in self.assets),
            ", ".join(str(rec) for rec in self.refs),
            ", ".join(str(rec) for rec in self.targets),
        )
