import sqlmodel
import typing as t

try:
    from ._base import MySQLModel
    from services import get_number_from_filename
except (ImportError, ModuleNotFoundError):
    from ._base import MySQLModel  # type: ignore
    from ..services import get_number_from_filename  # type: ignore


class Heading(MySQLModel, table=True):
    __tablename__ = "headings"

    # id: int = sqlmodel.Field(primary_key=True)
    file_name: str
    file_num: int = sqlmodel.Field(default=-1)
    h_num: int
    elem: str
    level: str
    text: str
    word_count: int
    char_count: int
    target: str
    slug: str

    def __init__(self, **data: dict[str, t.Any]) -> None:
        data["file_num"] = get_number_from_filename(data["file_name"])
        super().__init__(**data)


# class HeadingDatapoint(DatapointBase):
#     schema_v: int = 1  # if multiple v in the db, the client might have to differentiate
#     ###
#     file_name: str
#     elem: str
#     level: str
#     text: str
#     word_count: int
#     char_count: int
#     target: str
