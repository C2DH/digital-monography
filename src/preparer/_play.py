import abc
import uuid
import bs4
import enum
import datetime
import dataclasses
import json
import pathlib
import typing as t

# from models.assets import (
#     AssetInfoFromBook,
#     AssetInfoFromUpload,
#     AssetInfoEncoder,
#     AssetsWriter,
# )


class MyEnum(enum.Enum):
    DIGITAL = 0
    PAPER = 1


T = t.TypeVar("T")


# bs = bs4.BeautifulSoup("", "html.parser")


@dataclasses.dataclass
class DatapointBase(abc.ABC):
    pk: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()), kw_only=True)

    # def __post_init__(self):
    #     self.pk = str(uuid.uuid4())

    @property
    def s3_key(self) -> str:
        raise NotImplementedError

    def to_json(self) -> dict[str, str | int | bool]:
        "Converts the dataclass obj to a dict with str/int/bool as values."

        def _primitive_dict(fields) -> dict[str, str | int | bool]:
            res = {}
            for key, val in fields:
                if isinstance(val, datetime.datetime):
                    val = val.isoformat()
                elif isinstance(val, enum.Enum):
                    val = val.value
                elif val not in [str, int, bool]:
                    # e.g. pathlib.PurePath, bs4.PageElement
                    val = str(val)
                res[key] = val
            return res

        return dataclasses.asdict(self, dict_factory=_primitive_dict)

    @classmethod
    def from_json(cls: t.Type[T], json_data: dict) -> T:
        "Constructs a dataclass instance from a JSON-like dictionary."
        if not dataclasses.is_dataclass(cls):
            raise ValueError(f"{cls.__name__} must be a dataclass")
        res = {}
        for field in dataclasses.fields(cls):
            val = json_data[field.name]
            if field.type == bs4.element.Tag:
                soup = bs4.BeautifulSoup(val, "html.parser")
                v = next(soup.children)
            elif field.type == datetime.datetime:
                v = datetime.datetime.fromisoformat(val)
            else:
                v = (field.type)(val)  # type casting
            res[field.name] = v
        return cls(**res)


@dataclasses.dataclass
class Test(DatapointBase):
    path: pathlib.PurePath
    enum: MyEnum
    tag: bs4.Tag
    time: datetime.datetime
    # pk: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))


@dataclasses.dataclass
class TestUnion(DatapointBase):
    unio: t.Union[str, int, bool]
    optio: t.Optional[str]
    dictio: dict[str, str]
    litero: t.Literal["hi", "bye"] = "hi"


tag = bs4.BeautifulSoup("<html><p>hi</p></html>", "html.parser").html.p


test = Test(
    path=pathlib.Path("/tmp/efs/README.md"),
    enum=MyEnum.PAPER,
    tag=tag,
    time=datetime.datetime.now(),
)

testu = TestUnion(unio="hi", optio="yey", dictio={"hi": "bye"})


# notation:
# j = test.to_json()
# Test.from_json(j)


# b1 = AssetInfoFromBook(slug="mybook")
# b2 = AssetInfoFromBook(slug="mybook")
# b3 = AssetInfoFromBook(slug="mybook")
# u1 = AssetInfoFromUpload(
#     **{
#         "key": "mybook/name.py",
#         "slug": "mybook",
#         "name": "name.png",
#         "exists": False,
#         "last_modified": datetime.datetime.now(),
#         "size": 0,
#     }
# )
# u2 = AssetInfoFromUpload(
#     **{
#         "key": "mybook/name2.py",
#         "slug": "mybook",
#         "name": "name2.png",
#         "exists": False,
#         "last_modified": datetime.datetime.now(),
#         "size": 0,
#     }
# )

# aw = AssetsWriter()
# aw.add(b1)
# aw.add(b2)
# aw.add(b3)

# aw2 = AssetsWriter()
# aw2.add(u1)
# aw2.add(u2)
