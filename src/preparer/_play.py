import abc
import datetime
import enum
import json
import pathlib
import pydantic
import typing as t
import uuid
from sqlmodel.main import SQLModelMetaclass
from sqlmodel import SQLModel

from models._base import MySQLModel
from models import tables_to_models
from models.assets import Asset
from metadata import AssetDatapoint
from constants import MediumEnum
from keys import KeyPath

# from typing import Type


class SomeEnum(enum.StrEnum):
    PAPER = "P"
    DIGITAL = "D"
    PAPER_AND_DIGITAL = "P+D"


class Foo(type(pathlib.Path())):  # type: ignore
    def __new__(cls, *pathsegments):
        return super().__new__(cls, *pathsegments)

    def get_false(self) -> bool:
        return False


class BarBase(pydantic.BaseModel, abc.ABC):
    pk: str

    def __init__(cls, **data):
        pk = data.pop("pk", str(uuid.uuid4()))
        return super().__init__(pk=pk, **data)

    def to_json(self):
        # def to_json(self) -> str:
        # return self.model_dump_json()
        return self.model_dump()  # dump()

    @classmethod
    def from_json(cls, data):
        return cls(**data)

    # def from_json(cls, data: str):
    # return cls(**json.loads(data))


class Bar(BarBase):
    n: int | None
    s: str
    t: datetime.datetime
    p: Foo
    f: pathlib.PurePath
    e: SomeEnum
    is_e: bool
    # p: Type[KeyPath]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {Foo: lambda v: str(v)}

    @pydantic.field_validator("p", mode="before")
    def deserialize_foo(cls, v):
        if isinstance(v, str):
            return Foo(v)
        return v

    # def model_post_init(self, context) -> None:
    #     # if self.e:
    #     self._is_e = self.e in (
    #         SomeEnum.PAPER,
    #         SomeEnum.PAPER_AND_DIGITAL,
    #     )

    def __init__(self, **data) -> None:
        data["is_e"] = data["e"] in (
            SomeEnum.PAPER,
            SomeEnum.PAPER_AND_DIGITAL,
        )
        super().__init__(**data)


if __name__ == "__main__":
    dp1 = Bar(
        p=Foo("foo/bar/1.txt"),
        f=pathlib.PosixPath("foo/bar/1.txt"),
        n=1,
        s="1",
        t=datetime.datetime.now(),
        e=SomeEnum.PAPER,
    )
    dp2 = Bar(
        p=Foo("foo/bar/2.txt"),
        f=pathlib.PosixPath("foo/bar/2.txt"),
        n=2,
        s="2",
        t=datetime.datetime.now(),
        e=SomeEnum.DIGITAL,
    )
    # dp2 = Bar(
    #     **{
    #         "p": Foo("foo/bar/2.txt"),
    #         "n": None,
    #         "s": "2",
    #         "t": datetime.datetime.now(),
    #     }
    # )

    print(json.loads(dp1.model_dump_json()))
    dp3 = Bar(**json.loads(dp1.model_dump_json()))
    assert dp1.p == dp3.p

    ad1 = Asset(
        fp=pathlib.PosixPath("foo/bar/1.txt"),
        metadata_table="sdofiafjsoisdjfaosjfpafsodij",
        medium=MediumEnum.PAPER,
        slug="slug",
        author="author",
        source="source",
        location=KeyPath("foo/bar/config.yml"),
        alttext="alttext",
        caption="caption",
        comments="comments",
        target="target",
        is_color=True,
        is_ready=False,
        # is_on_paper=bool,
    )

    assert ad1.is_on_paper is True
    # print(ad1.to_json())

    # print(dp1.model)
