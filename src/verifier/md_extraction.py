import dataclasses
import json
import pathlib
import typing as t
import uuid


try:
    from constants import (
        METADATA_FIELDS,
        FIELD_DIGITAL_SOURCE,
        FIELD_PAPER_SOURCE,
        FIELD_DELETE_PREVIOUS,
    )
except (ImportError, ModuleNotFoundError):
    from .constants import (
        METADATA_FIELDS,
        FIELD_DIGITAL_SOURCE,
        FIELD_PAPER_SOURCE,
        FIELD_DELETE_PREVIOUS,
    )


type AcceptedValues = t.Union[str, bool, pathlib.Path]


class FieldTypeRecord(t.TypedDict):
    key: str
    is_bool: bool
    is_required: bool
    aliases: list[str]
    desc: str


@dataclasses.dataclass
class AssetDatapoint:
    _key: str
    _val: str
    key: str = dataclasses.field(init=False)
    val: AcceptedValues = dataclasses.field(init=False)
    field: t.Optional[FieldTypeRecord] = dataclasses.field(init=False)

    def __post_init__(self):
        self.key = self._normalize_key(self._key)
        self.field = next((f for f in METADATA_FIELDS if f["key"] == self.key), None)
        if self.field is not None and self.field["is_bool"]:
            self.val = self._val_to_bool(self._val)
        elif self._looks_like_a_potential_filepath(self._val):
            fp = pathlib.Path(self._val)
            self.val = fp
        # TODO: consider adding an url handler
        else:
            self.val = self._val.strip()

    def _looks_like_a_potential_filepath(self, v: str) -> bool:
        # TODO: after clarity on the asset storage, change this naive
        # logic into `if fp.exists() and not fp.is_dir()` or similar
        if v.startswith("./"):
            return True
        return False

    def _normalize_key(self, s: str) -> str:
        while " " in s:
            s = s.replace(" ", "")
        s = s.lower().strip().replace("_", "").replace("-", "").replace("#", "")
        for field in METADATA_FIELDS:
            if s in field["aliases"]:
                return field["key"]
        return s

    def _val_to_bool(self, _v: str) -> bool:
        v = _v.strip().lower()
        if v in [
            "0",
            "no",
            "nee",
            "not",
            "non",
            "nul",
            "none",
            "nicht",
            "nein",
            "false",
            "kein",
        ]:
            return False
        return bool(v)

    def to_dict(self):
        return {self.key: self.val}

    def to_json(self):
        return {self.key: str(self.val)}


class AssetMetadata:
    """
    Container of key:val pairs describing a single asset
    (e.g. license and author data of a single image)
    """

    def __init__(self) -> None:
        self.uuid = str(uuid.uuid4())
        self._datapoints = []
        self.paper_fp = None
        self.digital_fp = None
        self.delete_prev = False

    def __getitem__(self, key: str) -> AcceptedValues:
        return self.__dict__[key]

    def __nonzero__(self):
        return bool(self._datapoints)

    def to_dict(self) -> dict[str, AcceptedValues]:
        res = {dp.key: dp.val for dp in self._datapoints}
        res["uuid"] = self.uuid
        return res

    def get(self, key: str, default: t.Any = None) -> t.Any:
        try:
            return self.__dict__[key]
        except KeyError:
            return default

    def add(self, key: str, val: str) -> None:
        datapoint = AssetDatapoint(_key=key, _val=val)
        if datapoint.key == FIELD_DELETE_PREVIOUS:
            self.delete_prev = datapoint.val
        elif isinstance(datapoint.val, pathlib.Path):
            if datapoint.key == FIELD_PAPER_SOURCE:
                self.paper_fp = datapoint.val
            elif datapoint.key == FIELD_DIGITAL_SOURCE:
                self.digital_fp = datapoint.val
        self._datapoints.append(datapoint)
        self.__dict__[datapoint.key] = datapoint.val

    def remove(self, key: str) -> None:
        for dp, i in enumerate(self._datapoints):
            if dp.key == key:
                del self._datapoints[i]

    def includes(self, key: str) -> bool:
        for dp in self._datapoints:
            if dp.key == key:
                return True
        return False

    def __str__(self):
        return json.dumps([dp.to_json() for dp in self._datapoints])

    def __len__(self):
        return len(self._datapoints)


class DocumentMetadata:
    def __init__(self) -> None:
        self.assets = []
        self._metadata = {}

    def __getitem__(self, key: str) -> AssetMetadata:
        return self._metadata[key]

    def add_asset_metadata(self, asset_meta: AssetMetadata) -> None:
        self._metadata[asset_meta.uuid] = asset_meta
        self.assets.append(asset_meta)

    def assets_as_dicts(self) -> list[dict[str, AcceptedValues]]:
        return [am.to_dict() for am in self.assets]

    def __str__(self) -> str:
        return "%s(assets=[%s])" % (
            self.__class__.__name__,
            ", ".join(str(am) for am in self.assets),
        )
