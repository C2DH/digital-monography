import pathlib
import sqlmodel
import typing as t

try:
    from ._base import ChapterSQLModel
    from keys import KeyPath
    from constants import MediumEnum
except (ImportError, ModuleNotFoundError):
    from ._base import ChapterSQLModel  # type: ignore
    from ..keys import KeyPath  # type: ignore
    from ..constants import MediumEnum  # type: ignore


class Asset(ChapterSQLModel, table=True):
    """
    Information about an asset extracted from a document, especially from
    * Metadata Tables
    * captions
    * target id above caption

    When analysing assets, this model should be joined with
    * upload level (s3) information
    * book level information
    """

    __tablename__ = "assets"

    x_fp: str = sqlmodel.Field(alias="fp")
    metadata_table: str
    x_medium: str = sqlmodel.Field(alias="medium")
    slug: str
    author: str
    source: str
    x_location: str | None = sqlmodel.Field(alias="location")
    alttext: str
    caption: str
    orig_caption: str
    comments: str
    target: str
    is_color: bool | None
    is_ready: bool
    is_on_paper: bool
    rest: str = sqlmodel.Field(default="")
    height: str = sqlmodel.Field(default="100%")

    @property
    def fp(self) -> pathlib.Path:
        return pathlib.Path(self.x_fp)

    @fp.setter
    def fp(self, val: pathlib.Path) -> None:
        self.x_fp = str(val)

    @property
    def medium(self) -> MediumEnum:
        return MediumEnum(self.x_medium)

    @medium.setter
    def medium(self, val: MediumEnum) -> None:
        self.x_medium = str(val)

    @property
    def location(self) -> KeyPath:
        return KeyPath(self.x_location)

    @location.setter
    def location(self, val: KeyPath) -> None:
        self.x_location = str(val)

    def __init__(self, **data: t.Dict[str, t.Any]) -> None:
        data["is_on_paper"] = data["medium"] in (
            MediumEnum.PAPER,
            MediumEnum.PAPER_AND_DIGITAL,
        )
        for k, v in data.items():
            if isinstance(v, pathlib.Path) or isinstance(v, KeyPath):
                data[k] = str(v)
        super().__init__(**data)


class AssetService:
    @staticmethod
    def is_digital(medium: MediumEnum) -> bool:
        """
        Check if the asset is digital based on its "medium" field.
        """
        return medium == MediumEnum.DIGITAL or medium == MediumEnum.PAPER_AND_DIGITAL

    @staticmethod
    def get_s3_key(key: KeyPath) -> str:
        return f"{key.slug}/{key.stem}.json"


#########################################################################################


# class AssetDatapoint(DatapointBase):
#     """
#     Information about an asset extracted from a document, especially from
#     * Metadata Tables
#     * captions
#     * target id above caption

#     When analysing assets, this model should be joined with
#     * upload level (s3) information
#     * book level information
#     """

#     schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
#     ###
#     fp: pathlib.Path
#     metadata_table: str
#     medium: MediumEnum
#     slug: str
#     author: str
#     source: str
#     location: KeyPath | None
#     alttext: str
#     caption: str
#     comments: str
#     target: str
#     is_color: bool | None
#     is_ready: bool
#     is_on_paper: bool

#     model_config = pydantic.ConfigDict(
#         arbitrary_types_allowed=True, json_encoders={KeyPath: lambda v: str(v)}
#     )

#     def __init__(self, **data) -> None:
#         # if data.get("medium") is not None:
#         data["is_on_paper"] = data["medium"] in (
#             MediumEnum.PAPER,
#             MediumEnum.PAPER_AND_DIGITAL,
#         )
#         super().__init__(**data)

#     @pydantic.field_validator("location", mode="before")
#     def deserialize_location(cls, v):
#         if isinstance(v, str):
#             return KeyPath(v)
#         return v

#     @staticmethod
#     def get_s3_key(key: KeyPath) -> str:
#         return f"{key.slug}/{key.stem}.json"
