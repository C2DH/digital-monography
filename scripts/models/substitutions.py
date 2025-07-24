import pathlib
import sqlmodel
import typing as t
import uuid

try:
    from ._base import MySQLModel
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore
    from ..keys import KeyPath  # type: ignore


class Substitution(MySQLModel, table=True):
    __tablename__ = "substitutions"

    # pk: str = sqlmodel.Field(primary_key=True, default=str(uuid.uuid4()))
    was: str
    placeholder: str
    is_digital: bool | None
    is_paper: bool | None
    item_type: t.Literal[
        "heading", "equation", "figure", "table", "graph", "ref", ""
    ] = sqlmodel.Field(sa_type=sqlmodel.String)
    x_location: str = sqlmodel.Field(alias="location")
    target_fn: str | None
    file_count: int | None
    prefix: str
    prev_item_num: int | None
    new_item_num: int | None = sqlmodel.Field(default=None)
    fprefix: str | None = sqlmodel.Field(default=None)

    @property
    def location(self) -> pathlib.Path:
        return pathlib.Path(self.x_location)

    @location.setter
    def location(self, val: pathlib.Path) -> None:
        self.x_location = str(val)

    def __init__(self, **data: t.Dict[str, t.Any]) -> None:
        data["x_location"] = str(data.pop("location"))
        super().__init__(**data)


# class SubstitutionDatapoint(DatapointBase):
#     schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
#     ###
#     was: str
#     placeholder: str
#     is_digital: bool | None
#     is_paper: bool | None
#     item_type: t.Literal["heading", "equation", "figure", "table", "graph", "ref", ""]
#     target_fn: str | None
#     file_count: int | None
#     prefix: str
#     prev_item_num: int | None
#     new_item_num: int | None = None
#     fprefix: str | None = None
#     # make sure that literal options are equal to constants.CAPTION_ITEM_TYPE_*

#     def new_value(self, file_prefix=None) -> str:
#         """
#         Returns the value that will replace placeholder.
#         Used for substituting values in builder (for digital version).
#         """
#         if self.is_digital is False and self.is_paper is True:
#             return ""
#         elif self.new_item_num and file_prefix:
#             return f"{file_prefix}.{self.prefix}{self.new_item_num}"
#         elif self.new_item_num is not None:
#             file_count = self.file_count if self.file_count is not None else ""
#             return f"{file_count}.{self.prefix}{self.new_item_num}"
#         elif self.was == AUTONUMBER_PLACEHOLDER:
#             return ""
#         else:
#             return self.was
